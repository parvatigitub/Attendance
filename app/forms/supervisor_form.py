from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField, SelectField, FileField
from wtforms.validators import DataRequired, Length, Regexp
from flask_wtf.file import FileAllowed, FileRequired

class SupervisorForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])
    location_id = SelectField('Location', coerce=int, validators=[DataRequired()])

    first_name = StringField('First Name', validators=[DataRequired()])
    middle_name = StringField('Middle Name')
    last_name = StringField('Last Name', validators=[DataRequired()])
    dob = DateField('Date of Birth', validators=[DataRequired()])
    doj = DateField('Date of Joining', validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired(), Regexp(r'^\d{10}$', message="Enter 10 digit phone number")])
    employee_code = StringField('Employee Code', validators=[DataRequired()])
    esic_no = StringField('ESIC No')
    uan_no = StringField('UAN No')
    aadhaar_no = StringField('Aadhaar No', validators=[DataRequired(), Regexp(r'^\d{12}$', message="Enter 12 digit Aadhaar number")])
    pan_no = StringField('PAN No', validators=[DataRequired(), Regexp(r'^[A-Z]{5}[0-9]{4}[A-Z]$', message="Enter valid PAN number")])
    designation = StringField('Designation', validators=[DataRequired()])
    account_number = StringField('Account Number', validators=[DataRequired()])
    ifsc = StringField('IFSC Code', validators=[DataRequired(), Regexp(r'^[A-Z]{4}0[A-Z0-9]{6}$', message="Enter valid IFSC code")])
    bank_name = StringField('Bank Name', validators=[DataRequired()])
    
    aadhaar_image = FileField('Aadhaar Image', validators=[FileRequired(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    pan_image = FileField('PAN Image', validators=[FileRequired(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    passbook_image = FileField('Passbook Image', validators=[FileRequired(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    profile_image = FileField('Profile Image', validators=[FileRequired(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])

    current_address = StringField('Current Address', validators=[DataRequired()])
    permanent_address = StringField('Permanent Address', validators=[DataRequired()])

    submit = SubmitField('Register Supervisor')
