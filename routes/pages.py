from flask import Blueprint, render_template
from flask_login import login_required
import json

pages_bp = Blueprint('pages', __name__)

@pages_bp.route('/')
def index():
    return render_template('index.html')

@pages_bp.route('/upload')
@login_required
def upload():
    return render_template('upload.html')

@pages_bp.route('/results')
@pages_bp.route('/results/<string:conversation_id>')
@login_required
def results(conversation_id=None):
    from models.conversation import Conversation
    from flask_login import current_user
    from flask import session
    
    conv_data = None
    cid = conversation_id or session.get('conversation_id')
    print(f"DEBUG /results: cid={cid}")
    if cid:
        conv = Conversation.get(cid)
        print(f"DEBUG /results: conv found={conv is not None}")
        if conv:
            print(f"DEBUG /results: conv.user_id={conv.get('user_id')}, current_user.id={current_user.id}, match={conv.get('user_id') == current_user.id}")
        if conv and conv.get('user_id') == current_user.id:
            # Safely parse JSON properties
            def safe_json_load(val, default):
                if not val: return default
                if isinstance(val, str):
                    try: return json.loads(val)
                    except: return default
                return val

            insights = safe_json_load(conv.get('insights'), [])
            sentiment = safe_json_load(conv.get('sentiment'), {})
            metrics = safe_json_load(conv.get('metrics'), {})
            speaker_analysis = safe_json_load(conv.get('speaker_analysis'), [])
            analysis_result = safe_json_load(conv.get('analysis_result'), None)

            # Prepare dictionary to pass to template
            conv_data = {
                "id": str(conv['_id']),
                "file_name": conv.get('file_name'),
                "file_url": conv.get('file_url'),
                "transcription": conv.get('transcription') or conv.get('transcript'),
                "diarization": conv.get('diarization'),
                "summary": conv.get('summary'),
                "insights": insights,
                "sentiment": sentiment,
                "metrics": metrics,
                "speaker_analysis": speaker_analysis,
                "analysis_result": analysis_result
            }
            
    return render_template('results.html', past_conversation=conv_data)

@pages_bp.route('/about')
def about():
    return render_template('about.html')

@pages_bp.route('/contact')
def contact():
    return render_template('contact.html')

@pages_bp.route('/team')
def team():
    return render_template('team.html')

@pages_bp.route('/membership')
def membership():
    return render_template('membership.html')
