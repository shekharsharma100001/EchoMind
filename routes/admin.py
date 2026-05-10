from flask import Blueprint, render_template, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
import database.db as db_module
from models.user import User
from bson.objectid import ObjectId

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
@login_required
def check_admin():
    if not current_user.is_admin:
        flash("You do not have permission to access the admin panel.", "error")
        return redirect(url_for('pages.index'))

@admin_bp.route('/dashboard')
def dashboard():
    users_data = list(db_module.db.users.find())
    users = [User(u) for u in users_data]
    active_users_count = len(users)
    
    user_stats = []
    total_docs = 0
    for user in users:
        docs = db_module.db.documents.count_documents({'user_id': user.id})
        total_docs += docs
        user_stats.append({
            'user': user,
            'doc_count': docs
        })
        
    return render_template('admin.html', 
                           user_stats=user_stats, 
                           active_users_count=active_users_count, 
                           total_docs=total_docs)

@admin_bp.route('/delete_user/<string:user_id>', methods=['POST'])
def delete_user(user_id):
    if user_id == current_user.id:
        return jsonify({"error": "Cannot delete your own admin account."}), 400
        
    try:
        user_data = db_module.db.users.find_one({'_id': ObjectId(user_id)})
        if not user_data:
            return jsonify({"error": "User not found."}), 404
            
        # Delete related documents and conversations
        db_module.db.documents.delete_many({'user_id': user_id})
        db_module.db.conversations.delete_many({'user_id': user_id})
        db_module.db.users.delete_one({'_id': ObjectId(user_id)})
        return jsonify({"message": "User deleted successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
