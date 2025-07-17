from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField, FileField, SelectField
from wtforms.validators import DataRequired, Regexp
from flask_wtf.file import FileRequired, FileAllowed

class EmployeeForm(FlaskForm):
    status = SelectField('Status', choices=[('active', 'Active'), ('inactive', 'Inactive')], validators=[DataRequired()])
    role = SelectField('Role', choices=[('employee', 'Employee'), ('supervisor', 'Supervisor'), ('admin', 'Admin')], validators=[DataRequired()])
    supervisor_id = SelectField('Supervisor', coerce=int, validators=[DataRequired()])
    location_id = SelectField('Location', coerce=int, validators=[DataRequired()])
    first_name = StringField('First Name', validators=[DataRequired()])
    middle_name = StringField('Middle Name')
    last_name = StringField('Last Name', validators=[DataRequired()])
    dob = DateField('Date of Birth', validators=[DataRequired()])
    doj = DateField('Date of Joining', validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired(), Regexp(r'^\d{10}$')])
    employee_code = StringField('Employee Code', validators=[DataRequired()])
    designation = StringField('Designation', validators=[DataRequired()])

    aadhaar_no = StringField('Aadhaar No', validators=[DataRequired(), Regexp(r'^\d{12}$')])
    pan_no = StringField('PAN No', validators=[DataRequired(), Regexp(r'^[A-Z]{5}[0-9]{4}[A-Z]$')])

    account_number = StringField('Account Number', validators=[DataRequired()])
    ifsc = StringField('IFSC Code', validators=[DataRequired(), Regexp(r'^[A-Z]{4}0[A-Z0-9]{6}$')])
    bank_name = StringField('Bank Name', validators=[DataRequired()])

    current_address = StringField('Current Address', validators=[DataRequired()])
    permanent_address = StringField('Permanent Address', validators=[DataRequired()])

    aadhaar_image = FileField('Aadhaar Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    pan_image = FileField('PAN Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    passbook_image = FileField('Passbook Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    profile_image = FileField('Profile Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])

    submit = SubmitField('Add Employee')
