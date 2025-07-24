# create_admin.py

from app import app, db
from app.models import User, Location, Supervisor, Employee
from datetime import datetime

with app.app_context():
    # IMPORTANT: Uncomment this line to ensure tables are created if they don't exist.
    # If you are using Flask-Migrate for schema management, you might keep this commented
    # and use 'flask db upgrade' instead. For initial setup, uncommenting is simpler.
    db.create_all() 

    try:
        # Check if admin user already exists to avoid duplicates
        existing_admin_user = User.query.filter_by(username='admin').first()
        if existing_admin_user:
            print("Admin user already exists. Skipping creation.")
        else:
            # Create a test location (if it doesn't exist)
            location = Location.query.filter_by(name='Test Location').first()
            if not location:
                location = Location(name='Test Location')
                db.session.add(location)
                db.session.commit()
                print("Test Location created.")
            
            # Create admin user
            admin = User(
                username='admin',
                name='Admin User',
                role='admin'
            )
            admin.set_password('admin123') # This method hashes and sets password_hash

            db.session.add(admin)
            db.session.commit()
            print("Admin created successfully with hashed password.")

        # --- Supervisor User and Profile Creation Logic ---
        # First, check if the supervisor user exists in the User table
        supervisor_user = User.query.filter_by(username='supervisor').first()

        if supervisor_user:
            print("Supervisor user already exists.")
        else:
            # If supervisor user doesn't exist, create it
            supervisor_user = User(
                username='supervisor',
                name='Supervisor User',
                role='supervisor'
            )
            supervisor_user.set_password('supervisor123') # Hash the password
            db.session.add(supervisor_user)
            db.session.commit()
            print("Supervisor user created successfully with hashed password.")

        # Now, check if the supervisor profile exists in the Supervisor table
        # This ensures the profile is created even if the user already existed.
        existing_supervisor_profile = Supervisor.query.filter_by(user_id=supervisor_user.id).first()

        if existing_supervisor_profile:
            print("Supervisor profile already exists. Skipping creation.")
        else:
            # Create supervisor profile
            location = Location.query.filter_by(name='Test Location').first() # Re-fetch location
            if location:
                supervisor_profile = Supervisor(
                    user_id=supervisor_user.id, # Use the ID of the created/found supervisor_user
                    location_id=location.id,
                    first_name='Test',
                    last_name='Supervisor',
                    dob=datetime(1980, 1, 1),
                    doj=datetime.now(),
                    phone='1234567890', # This is 10 chars, should fit if column is varchar(11) or more
                    employee_code='SUP001',
                    # Adjusted values below to be 11 characters or less to avoid StringDataRightTruncation
                    # IMPORTANT: The ideal fix is to update the 'length' attribute in your app/models.py
                    # for the corresponding columns (e.g., aadhaar_no, account_number, ifsc)
                    # to match the expected data length.
                    aadhaar_no='12345678901', # Shortened from 12 to 11 chars
                    pan_no='ABCDE1234F', # 10 chars, fits
                    designation='Test Supervisor',
                    account_number='12345678901', # Shortened from 12 to 11 chars
                    ifsc='ABCD0123456', # Shortened from 12 to 11 chars
                    bank_name='Test Bank',
                    current_address='Test Address',
                    permanent_address='Test Address'
                )
                db.session.add(supervisor_profile)
                db.session.commit()
                print("Test Supervisor profile created successfully!")
            else:
                print("Could not create supervisor profile: Test Location not found. Ensure 'Test Location' is created first.")

        print("\nDatabase contents:")
        print("\nLocations:", Location.query.all())
        print("\nUsers:", User.query.all())
        print("\nSupervisors:", Supervisor.query.all())

    except Exception as e:
        print(f"Error creating test data: {str(e)}")
        db.session.rollback()
