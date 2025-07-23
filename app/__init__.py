from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
csrf = CSRFProtect(app)
migrate = Migrate(app, db)

# >>> ADD THIS LINE <<<
from app import models # This imports your models file, making them known to SQLAlchemy/Migrate

login_manager.login_view = 'auth.login'

# >>> ADD THIS BLOCK (if you don't already have it, or modify if it's there but using app.models.User) <<<
@login_manager.user_loader
def load_user(user_id):
    # Make sure your User model is accessible here via `models.User`
    return models.User.query.get(int(user_id))


# 💡 Cache-control
@app.after_request
def add_header(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
    return response

# ✅ Blueprints import and register after app creation
from app.routes.auth import auth_bp
from app.routes.admin import admin_bp
from app.routes.supervisor import supervisor_bp

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(supervisor_bp, url_prefix='/supervisor')
