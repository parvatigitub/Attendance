from app import app, db
from app.models import User

with app.app_context():
    existing_admin = User.query.filter_by(username='admin').first()

    if not existing_admin:
        admin = User(username='admin', name='Admin User')
        admin.set_password('admin123')  # assumes you have set_password method
        admin.role = 'admin'
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin created successfully.")
    else:
        print("ℹ️ Admin user already exists.")
