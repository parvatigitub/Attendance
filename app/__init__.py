from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config

# ✅ Flask App and Config Setup
app = Flask(__name__)
app.config.from_object(Config)

# ✅ Extensions Initialization
db = SQLAlchemy(app)
login_manager = LoginManager(app)
csrf = CSRFProtect(app)
migrate = Migrate(app, db)

login_manager.login_view = 'auth.login'

# ✅ Create tables during deployment
with app.app_context():
    db.create_all()

# ✅ Cache-control to prevent back-button login issues
@app.after_request
def add_header(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
    return response

# ✅ Blueprints register
from app.routes.auth import auth_bp
from app.routes.admin import admin_bp
from app.routes.supervisor import supervisor_bp

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(supervisor_bp, url_prefix='/supervisor')
