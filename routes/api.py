import os
import uuid
import mimetypes
from io import BytesIO
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, session, send_file
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from flask_login import login_required, current_user
from models.document import DocumentRecord
from models.conversation import Conversation
from supabase import create_client, Client
import json
from utils.gemini_helper import upload_to_gemini, transcribe_file, diarize_file, summarize_content
from utils.rag_helper import create_embeddings, query_rag
from flask_mail import Message
import database.db as db_module

api_bp = Blueprint('api', __name__)
global_cache = {}

@api_bp.route('/contact', methods=['POST'])
def api_contact():
    from app import mail
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        message = data.get('message')
        
        if not all([first_name, email, message]):
            return jsonify({"error": "Please fill in all required fields"}), 400

        # Save to MongoDB
        contact_doc = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "message": message,
            "submitted_at": datetime.utcnow()
        }
        db_module.db.contact_messages.insert_one(contact_doc)

        # Send Email
        try:
            msg = Message(
                subject=f"New Contact Form Submission: {first_name} {last_name}",
                recipients=[current_app.config.get('MAIL_USERNAME')],
                body=f"Name: {first_name} {last_name}\nEmail: {email}\n\nMessage:\n{message}"
            )
            mail.send(msg)
        except Exception as mail_err:
            print(f"Mail sending failed: {mail_err}")
            # We still return success because it's saved in DB
            
        return jsonify({"message": "Message received successfully"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'flac', 'aac', 'mp4', 'mov', 'mkv', 'avi', 'txt', 'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_supabase():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise Exception("Supabase credentials not found.")
    return create_client(url, key)

@api_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if file and allowed_file(file.filename):
        # Generate a unique filename and save locally temporarily
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Upload to Supabase Storage
        try:
            supabase = get_supabase()
            content_type, _ = mimetypes.guess_type(filepath)
            with open(filepath, 'rb') as f:
                supabase.storage.from_("echomind-uploads").upload(
                    path=filename, 
                    file=f, 
                    file_options={"content-type": content_type or "application/octet-stream"}
                )
            file_url = supabase.storage.from_("echomind-uploads").get_public_url(filename)
        except Exception as e:
            return jsonify({"error": f"Supabase upload failed: {str(e)}"}), 500
        
        # Upload to Gemini immediately so it processes while user navigates to results
        try:
            mime_type = content_type
            gemini_filepath = filepath
            
            if ext == 'docx':
                import docx
                doc = docx.Document(filepath)
                text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                
                gemini_filepath = filepath + ".txt"
                with open(gemini_filepath, "w", encoding="utf-8") as txt_file:
                    txt_file.write(text)
                mime_type = "text/plain"
                
            # Send file to Gemini API (wait for processing)
            gemini_file = upload_to_gemini(gemini_filepath, mime_type=mime_type)
            # Store the gemini URI or name in session
            session['gemini_file_name'] = gemini_file.name
            session['upload_context'] = request.form.get('context', '')
            
            # Record an activity log in MongoDB
            new_doc = DocumentRecord.create(filename=file.filename, user_id=current_user.id)
            
            # Record conversation in MongoDB
            new_conv = Conversation.create(
                user_id=current_user.id,
                file_name=file.filename,
                file_url=file_url
            )
            
            session['conversation_id'] = new_conv['id']
            
            return jsonify({
                "message": "Upload successful", 
                "gemini_file_name": gemini_file.name
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
            
    return jsonify({"error": "File type not allowed"}), 400

@api_bp.route('/transcribe', methods=['POST'])
@login_required
def api_transcribe():
    gemini_file_name = session.get('gemini_file_name')
    if not gemini_file_name:
        return jsonify({"error": "No file context in session"}), 400
        
    try:
        data = request.get_json(silent=True) or {}
        language = data.get('language', 'Default')
        context = session.get('upload_context', '')
        transcript = transcribe_file(gemini_file_name, context=context, language=language)
        global_cache[gemini_file_name] = transcript
        
        # Save to DB
        conv_id = session.get('conversation_id')
        if conv_id:
            Conversation.update(conv_id, {'transcription': transcript, 'transcript': transcript})
                
        return jsonify({"transcript": transcript}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/diarize', methods=['POST'])
@login_required
def api_diarize():
    gemini_file_name = session.get('gemini_file_name')
    if not gemini_file_name:
        return jsonify({"error": "No file context in session"}), 400
        
    try:
        data = request.get_json(silent=True) or {}
        language = data.get('language', 'Default')
        context = session.get('upload_context', '')
        diarized = diarize_file(gemini_file_name, context=context, language=language)
        
        # Save to DB
        conv_id = session.get('conversation_id')
        if conv_id:
            Conversation.update(conv_id, {'diarization': diarized})
                
        return jsonify({"diarized": diarized}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/summarize', methods=['POST'])
@login_required
def api_summarize():
    gemini_file_name = session.get('gemini_file_name')
    if not gemini_file_name:
        return jsonify({"error": "No file context in session"}), 400
        
    try:
        data = request.get_json(silent=True) or {}
        language = data.get('language', 'Default')
        summary_length = data.get('summary_length', 'Detailed')
        summary_type = data.get('summary_type', 'Paragraph')
        summary_prompt = data.get('summary_prompt', '')
        context = session.get('upload_context', '')
        summary_data = summarize_content(gemini_file_name, context=context, language=language, summary_length=summary_length, summary_type=summary_type, summary_prompt=summary_prompt)
        
        # Save to DB
        conv_id = session.get('conversation_id')
        if conv_id:
            Conversation.update(conv_id, {
                'summary': summary_data.get('summary', ''),
                'insights': json.dumps(summary_data.get('key_insights', [])),
                'sentiment': json.dumps(summary_data.get('emotion_keywords', {})),
                'metrics': json.dumps(summary_data.get('metrics', {})),
                'speaker_analysis': json.dumps(summary_data.get('speaker_analysis', [])),
                'analysis_result': json.dumps(summary_data)
            })
        
        # Now populate RAG embeddings
        file_key = f"conv_{conv_id}" if conv_id else gemini_file_name
        transcript = global_cache.get(gemini_file_name, "")
        knowledge_base = transcript + "\n\nSUMMARY:\n" + str(summary_data)
        create_embeddings(file_key, knowledge_base)
        
        return jsonify(summary_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/ask', methods=['POST'])
@login_required
def api_ask():
    data = request.json or {}
    question = data.get('question')
    conv_id = data.get('conversation_id') or session.get('conversation_id')
    language = data.get('language', 'Default')
    
    if not question:
        return jsonify({"error": "Question is required"}), 400
        
    if not conv_id:
        # Fallback to gemini_file_name if conv_id is completely missing
        gemini_file_name = session.get('gemini_file_name')
        if not gemini_file_name:
            return jsonify({"error": "No file context in session"}), 400
        file_key = gemini_file_name
    else:
        # Validate conversation ownership
        from models.conversation import Conversation
        conv = Conversation.get(conv_id)
        if not conv or conv.get('user_id') != current_user.id:
            return jsonify({"error": "Invalid conversation"}), 403
            
        file_key = f"conv_{conv['id']}"
        
        # Build embeddings on the fly if missing from in-memory vector store
        from utils.rag_helper import vector_store, create_embeddings
        if file_key not in vector_store:
            knowledge_base = (conv.get('transcription') or "") + "\n\nSUMMARY:\n" + (conv.get('summary') or "")
            if knowledge_base.strip():
                create_embeddings(file_key, knowledge_base)
            else:
                return jsonify({"error": "Conversation context is empty"}), 400

    try:
        from utils.rag_helper import query_rag
        answer = query_rag(file_key, question, language=language)
        if conv_id:
            Conversation.add_qa(conv_id, {'question': question, 'answer': answer})
        return jsonify({"answer": answer}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500




