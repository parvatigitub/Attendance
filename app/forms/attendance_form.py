from flask_wtf import FlaskForm
from wtforms import HiddenField
from wtforms import BooleanField, IntegerField
from wtforms.validators import NumberRange

class AttendanceForm(FlaskForm):
    emp_id = HiddenField()  # Employee ID (hidden input in form)
    present = BooleanField("Present")  # Checkbox for Present/Absent
    ot = IntegerField("OT (hrs)", default=0, validators=[NumberRange(min=0)])  # Overtime field
