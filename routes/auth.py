from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from utils.oauth import oauth
import secrets
from datetime import datetime, timedelta
import database.db as db_module

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('pages.upload'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.find_by_email(email)
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            return redirect(next_page) if next_page else redirect(url_for('pages.upload'))
        else:
            flash('Invalid email or password', 'error')
            
    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('pages.upload'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.find_by_email(email):
            flash('Email already exists', 'error')
        else:
            user = User.create(username=username, email=email, password=password)
            login_user(user)
            flash('Account created successfully!', 'success')
            return redirect(url_for('pages.upload'))
            
    return render_template('signup.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('pages.index'))

@auth_bp.route('/login/google')
def login_google():
    redirect_uri = url_for('auth.auth_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route('/callback')
def auth_callback():
    token = oauth.google.authorize_access_token()
    user_info = token.get('userinfo')
    if user_info:
        email = user_info.get('email')
        google_id = user_info.get('sub')
        name = user_info.get('name')
        picture = user_info.get('picture')
        
        user = User.find_by_email(email)
        if not user:
            # Create a new user if one doesn't exist
            user = User.create(username=name, email=email, google_id=google_id, profile_picture=picture)
        
        login_user(user)
        if user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('pages.upload'))
    flash('Failed to authenticate with Google.', 'error')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = User.find_by_email(email)
        if user:
            token = secrets.token_urlsafe(32)
            expires = datetime.utcnow() + timedelta(hours=1)
            from bson.objectid import ObjectId
            db_module.db.users.update_one(
                {'_id': ObjectId(user.id)},
                {'$set': {'reset_token': token, 'reset_expires': expires}}
            )
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            flash(f'RESET_LINK:{reset_url}', 'reset_link')
        else:
            # Don't reveal whether email exists
            flash('If that email is registered, a reset link has been generated.', 'info')
        return redirect(url_for('auth.forgot_password'))
    return render_template('forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user_data = db_module.db.users.find_one({'reset_token': token})
    if not user_data or user_data.get('reset_expires', datetime.utcnow()) < datetime.utcnow():
        flash('This reset link is invalid or has expired.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        if len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'error')
        elif new_password != confirm_password:
            flash('Passwords do not match.', 'error')
        else:
            import bcrypt
            from bson.objectid import ObjectId
            salt = bcrypt.gensalt()
            new_hash = bcrypt.hashpw(new_password.encode('utf-8'), salt).decode('utf-8')
            db_module.db.users.update_one(
                {'_id': user_data['_id']},
                {'$set': {'password_hash': new_hash}, '$unset': {'reset_token': '', 'reset_expires': ''}}
            )
            flash('Password reset successfully! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
    return render_template('reset_password.html', token=token)
