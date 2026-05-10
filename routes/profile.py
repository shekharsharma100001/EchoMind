from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
import database.db as db_module
from models.user import User
import os, uuid
from routes.api import get_supabase
import mimetypes

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/', methods=['GET'])
@login_required
def profile_page():
    # Get recent activity
    conversations = list(db_module.db.conversations.find({'user_id': current_user.id}).sort('upload_date', -1))
    for c in conversations:
        c['id'] = str(c['_id'])
        if isinstance(c.get('summary'), list):
            c['summary'] = ' '.join([str(item) for item in c['summary']])
    total_docs = len(conversations)
    return render_template('profile.html', conversations=conversations, total_docs=total_docs)

@profile_bp.route('/api/update', methods=['POST'])
@login_required
def update_profile():
    data = request.json
    updates = {}
    try:
        if 'name' in data and data['name']:
            updates['username'] = data['name']
        if 'email' in data and data['email']:
            updates['email'] = data['email']
        if 'password' in data and data['password']:
            import bcrypt
            salt = bcrypt.gensalt()
            updates['password_hash'] = bcrypt.hashpw(data['password'].encode('utf-8'), salt).decode('utf-8')
            
        if updates:
            from bson.objectid import ObjectId
            db_module.db.users.update_one({'_id': ObjectId(current_user.id)}, {'$set': updates})
        return jsonify({"message": "Profile updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@profile_bp.route('/api/delete_conversation/<conv_id>', methods=['DELETE'])
@login_required
def delete_conversation(conv_id):
    from models.conversation import Conversation
    conv = Conversation.get(conv_id)
    
    if not conv:
        return jsonify({"error": "Conversation not found"}), 404
        
    if conv.get('user_id') != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
        
    # Delete from Supabase
    file_url = conv.get('file_url')
    if file_url:
        try:
            supabase = get_supabase()
            filename = file_url.split('/')[-1]
            supabase.storage.from_("echomind-uploads").remove([filename])
        except Exception as e:
            print(f"Error deleting from supabase: {e}")
            
    # Delete from DB
    if Conversation.delete(conv_id):
        return jsonify({"message": "Deleted successfully"}), 200
    else:
        return jsonify({"error": "Failed to delete from database"}), 500

@profile_bp.route('/api/upload_picture', methods=['POST'])
@login_required
def upload_profile_picture():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if file:
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            return jsonify({"error": "Invalid file type"}), 400
            
        filename = f"user_{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"
        
        try:
            supabase = get_supabase()
            content_type, _ = mimetypes.guess_type(filename)
            supabase.storage.from_("echomind-uploads").upload(
                path=f"profiles/{filename}", 
                file=file.read(), 
                file_options={"content-type": content_type or "image/jpeg"}
            )
            file_url = supabase.storage.from_("echomind-uploads").get_public_url(f"profiles/{filename}")
            
            from bson.objectid import ObjectId
            db_module.db.users.update_one({'_id': ObjectId(current_user.id)}, {'$set': {'profile_picture': file_url}})
            
            return jsonify({"message": "Profile picture updated", "filename": file_url})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Unknown error"}), 500
