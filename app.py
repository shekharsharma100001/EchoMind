import os
from flask import Flask
from flask_login import LoginManager
from database.db import init_db
from werkzeug.middleware.proxy_fix import ProxyFix
import json
from flask_mail import Mail

mail = Mail()

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    # App config
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key-change-in-prod')
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    
    # Upload folder config
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    
    # Profile Pictures folder config
    PROFILE_PICS_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'profile_pictures')
    os.makedirs(PROFILE_PICS_FOLDER, exist_ok=True)
    app.config['PROFILE_PICS_FOLDER'] = PROFILE_PICS_FOLDER
    
    # Mail config
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
    mail.init_app(app)
    
    # Initialize DB
    init_db(app)
    
    # Initialize OAuth
    from utils.oauth import init_oauth
    init_oauth(app)
    
    # Seed default admin user
    with app.app_context():
        from models.user import User
        admin = User.find_by_email('admin@echomind.cc')
        if not admin:
            User.create(username='admin', email='admin@echomind.cc', password='EchoMindLess', role='admin')

    # Flask-Login configuration
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return User.get(user_id)
    
    # Register blueprints (routes)
    from routes.pages import pages_bp
    from routes.auth import auth_bp
    from routes.api import api_bp
    from routes.profile import profile_bp
    from routes.admin import admin_bp
    
    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(profile_bp, url_prefix='/profile')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    @app.route('/test_auto_login')
    def test_auto_login():
        from models.user import User
        from flask_login import login_user
        from flask import redirect, url_for
        import database.db as db_module
        user_data = db_module.db.users.find_one({'email': 'shekharsharma100001@gmail.com'})
        if user_data:
            login_user(User(user_data))
            return redirect('/results/69fce9cd3287078f6a9f381d')
        return "User not found", 404
    
    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(debug=True, host='0.0.0.0', port=port)
