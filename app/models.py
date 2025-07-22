from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from . import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    role = db.Column(db.String(20), nullable=False)  # 'admin' or 'supervisor'

    supervisor = db.relationship('Supervisor', backref='user', uselist=False)


class Location(db.Model):
    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    supervisors = db.relationship('Supervisor', backref='location', lazy=True)
    employees = db.relationship('Employee', backref='location', lazy=True)

class Supervisor(db.Model):
    __tablename__ = 'supervisors'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)

    first_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    doj = db.Column(db.Date, nullable=False)
    phone = db.Column(db.String(10), nullable=False)
    employee_code = db.Column(db.String(50), nullable=False)
    esic_no = db.Column(db.String(50))
    uan_no = db.Column(db.String(50))
    aadhaar_no = db.Column(db.String(12), nullable=False)
    pan_no = db.Column(db.String(10), nullable=False)
    designation = db.Column(db.String(100), nullable=False)
    account_number = db.Column(db.String(50), nullable=False)
    ifsc = db.Column(db.String(11), nullable=False)
    bank_name = db.Column(db.String(100), nullable=False)
    
    profile_image = db.Column(db.String(200))
    aadhaar_image = db.Column(db.String(200))
    pan_image = db.Column(db.String(200))
    passbook_image = db.Column(db.String(200))
    
    current_address = db.Column(db.Text, nullable=False)
    permanent_address = db.Column(db.Text, nullable=False)

    employees = db.relationship('Employee', backref='supervisor', lazy=True)

class Employee(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisors.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)

    status = db.Column(db.String(20), default='pending')  # 'pending' or 'approved'

    first_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50), nullable=False)
    employee_code = db.Column(db.String(50), nullable=False)
    designation = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    doj = db.Column(db.Date, nullable=False)
    phone = db.Column(db.String(10), nullable=False)
    aadhaar_no = db.Column(db.String(12), nullable=False)
    pan_no = db.Column(db.String(10), nullable=False)

    account_number = db.Column(db.String(50), nullable=False)
    ifsc = db.Column(db.String(11), nullable=False)
    bank_name = db.Column(db.String(100), nullable=False)

    profile_image = db.Column(db.String(200))
    aadhaar_image = db.Column(db.String(200))
    pan_image = db.Column(db.String(200))
    passbook_image = db.Column(db.String(200))

    current_address = db.Column(db.Text, nullable=False)
    permanent_address = db.Column(db.Text, nullable=False)

    attendance_records = db.relationship('Attendance', back_populates='employee', lazy=True)

class Attendance(db.Model):
    __tablename__ = 'attendances'
    __table_args__ = (
        db.PrimaryKeyConstraint('emp_id', 'date'),
    )

    emp_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(10))  # 'P'
    ot = db.Column(db.Boolean, default=False)
    ot_hours = db.Column(db.Float, default=0.0)

    employee = db.relationship('Employee', back_populates='attendance_records')

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50))  # 'employee_pending', etc.
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    status = db.Column(db.String(20), default='unread')  # unread / read
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
