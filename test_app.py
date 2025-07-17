from app import create_app, db
from app.models import User, Location, Supervisor, Employee
from datetime import datetime

app = create_app()

with app.app_context():
    # Create tables
    db.create_all()

    # Test data creation
    try:
        # Create a test location
        location = Location(name='Test Location')
        db.session.add(location)
        db.session.commit()

        # Create admin user
        admin = User(
            username='admin',
            password='admin123',  # Insecure - this should be hashed in production
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()

        # Create supervisor user
        supervisor = User(
            username='supervisor',
            password='supervisor123',  # Insecure - this should be hashed in production
            role='supervisor'
        )
        db.session.add(supervisor)
        db.session.commit()

        # Create supervisor profile
        supervisor_profile = Supervisor(
            user_id=supervisor.id,
            location_id=location.id,
            first_name='Test',
            last_name='Supervisor',
            dob=datetime(1980, 1, 1),
            doj=datetime.now(),
            phone='1234567890',
            employee_code='SUP001',
            aadhaar_no='123456789012',
            pan_no='ABCDE1234F',
            designation='Test Supervisor',
            account_number='123456789012',
            ifsc='ABCD01234567',
            bank_name='Test Bank',
            current_address='Test Address',
            permanent_address='Test Address'
        )
        db.session.add(supervisor_profile)
        db.session.commit()

        print("Test data created successfully!")
        print("\nDatabase contents:")
        print("\nLocations:", Location.query.all())
        print("\nUsers:", User.query.all())
        print("\nSupervisors:", Supervisor.query.all())

    except Exception as e:
        print(f"Error creating test data: {str(e)}")
        db.session.rollback()

    # Test routes
    print("\nTesting routes:")
    with app.test_client() as client:
        # Test login
        response = client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        })
        print(f"\nLogin response status: {response.status_code}")

        # Test admin dashboard access
        response = client.get('/admin/dashboard')
        print(f"Admin dashboard status: {response.status_code}")

        # Test supervisor dashboard access
        response = client.get('/supervisor/dashboard')
        print(f"Supervisor dashboard status: {response.status_code}")
