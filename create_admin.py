from app import create_app, db
from app.models import User

app = create_app()
app.app_context().push()

# Create admin user with hashed password
admin = User(username='admin', name='Admin User')
admin.set_password('admin123')
admin.role = 'admin'
db.session.add(admin)
db.session.commit()
print("Admin created successfully with hashed password")
