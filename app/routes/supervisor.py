from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.forms.employee_form import EmployeeForm
from app.forms.attendance_form import AttendanceForm
from app.models import User, Employee, Supervisor, Attendance, Location
from app.utils.excel_export import generate_attendance_excel
from app import db
from datetime import datetime, timedelta
import os
import json

supervisor_bp = Blueprint('supervisor', __name__)

@supervisor_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'supervisor':
        return redirect(url_for('auth.login'))
    
    # Get all employees under this supervisor
    employees = Employee.query.filter_by(supervisor_id=current_user.id).all()
    
    # Calculate statistics
    total_employees = len(employees)
    
    # Get present employees today
    today = datetime.now().date()
    present_employees = (
        db.session.query(Employee)
        .join(Attendance, Employee.id == Attendance.emp_id)
        .filter(
            Attendance.date == today,
            Attendance.status == 'P',
            Employee.supervisor_id == current_user.id
        )
        .count()
    )

    # Get attendance records for today
    attendance_records = (
        db.session.query(Employee, Attendance)
        .join(Attendance, Employee.id == Attendance.emp_id)
        .filter(
            Attendance.date == today,
            Employee.supervisor_id == current_user.id
        )
        .all()
    )

    return render_template('supervisor/dashboard.html',
                           employees=employees,
                           total_employees=total_employees,
                           present_employees=present_employees,
                           attendance_records=attendance_records)

@supervisor_bp.route('/employee_list')
@login_required
def employee_list():
    if current_user.role != 'supervisor':
        abort(403)

    supervisor = Supervisor.query.filter_by(user_id=current_user.id).first()
    if not supervisor:
        flash('Supervisor not found', 'danger')
        return redirect(url_for('supervisor.dashboard'))

    employees = Employee.query.filter_by(location_id=supervisor.location_id).all()
    return render_template('supervisor/employee_list.html', employees=employees)

@supervisor_bp.route('/my_employees')
@login_required
def my_employees():
    if current_user.role != 'supervisor':
        return redirect(url_for('auth.login'))
    
    supervisor = Supervisor.query.filter_by(user_id=current_user.id).first()
    if not supervisor:
        flash('Supervisor not found', 'danger')
        return redirect(url_for('supervisor.dashboard'))

    employees = Employee.query.filter_by(location_id=supervisor.location_id).all()
    return render_template('supervisor/my_employees.html', employees=employees)

@supervisor_bp.route('/mark_attendance', methods=['GET', 'POST'])
@login_required
def mark_attendance():
    form = AttendanceForm()
    
    if request.method == 'POST':
        data = request.form.get('attendanceData')
        if not data:
            flash("No attendance data received.", "danger")
            return redirect(url_for('supervisor.mark_attendance'))

        try:
            attendance_dict = json.loads(data)
        except json.JSONDecodeError:
            flash("Invalid attendance data format.", "danger")
            return redirect(url_for('supervisor.mark_attendance'))

        # Get the date from the first entry in attendance data
        if not attendance_dict:
            flash("No attendance entries found.", "danger")
            return redirect(url_for('supervisor.mark_attendance'))

        # Get the date from the first entry
        first_entry = next(iter(attendance_dict.values()))
        date_str = first_entry.get('date')
        
        if not date_str:
            flash("No date provided in attendance data.", "danger")
            return redirect(url_for('supervisor.mark_attendance'))

        try:
            attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            today = datetime.today().date()

            if (today - attendance_date).days > 7:
                flash("You can only mark or update attendance within 7 days.", "danger")
                return redirect(url_for('supervisor.mark_attendance'))

            # Process attendance records
            for key, details in attendance_dict.items():
                # Split the key to get emp_id and date
                emp_id, date_str = key.split('_')
                record = Attendance.query.filter_by(emp_id=int(emp_id), date=attendance_date).first()
                if not record:
                    record = Attendance(emp_id=int(emp_id), date=attendance_date)

                record.status = details.get('status', '')
                record.ot = details.get('ot', False)
                record.ot_hours = details.get('ot_hours', 0)
                db.session.add(record)

            db.session.commit()
            flash("Attendance submitted successfully!", "success")
            return redirect(url_for('supervisor.mark_attendance'))

        except ValueError:
            flash("Invalid date format.", "danger")
            return redirect(url_for('supervisor.mark_attendance'))

    # Handle GET request
    # Get current week dates
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    week_dates = [start_of_week + timedelta(days=i) for i in range(7)]
    
    # Get supervisor details
    supervisor = Supervisor.query.filter_by(user_id=current_user.id).first()
    location = Location.query.get(supervisor.location_id)
    
    # Get employees for this location
    employees = Employee.query.filter_by(location_id=supervisor.location_id).all()
    
    return render_template('supervisor/mark_attendance.html',
                         employees=employees,
                         form=form,
                         week_dates=week_dates,
                         location_name=location.name,
                         month_name=today.strftime('%B'),
                         week_no=(today.isocalendar()[1] - start_of_week.isocalendar()[1] + 1),
                         supervisor_name=f"{supervisor.first_name} {supervisor.last_name}")

@supervisor_bp.route('/download_attendance')
@login_required
def download_attendance():
    supervisor = Supervisor.query.filter_by(user_id=current_user.id).first()
    if not supervisor:
        flash("Supervisor not found", "danger")
        return redirect(url_for('supervisor.dashboard'))

    location_id = supervisor.location_id
    week_start = datetime.today().date() - timedelta(days=datetime.today().weekday() + 1)
    week_dates = [week_start + timedelta(days=i) for i in range(7)]

    employees = Employee.query.filter_by(location_id=location_id).all()
    data = []

    for emp in employees:
        row = {
            'Name': f"{emp.first_name} {emp.last_name}",
            'Location': emp.location.name
        }
        for day in week_dates:
            att = Attendance.query.filter_by(employee_id=emp.id, date=day).first()
            row[day.strftime("%A (%d-%b)")] = att.status if att else ''
        data.append(row)

    file_path = generate_attendance_excel(data)
    return send_file(file_path, as_attachment=True, download_name="attendance.xlsx")

@supervisor_bp.route('/edit_employee/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def edit_employee(employee_id):
    if current_user.role != 'supervisor':
        abort(403)

    employee = Employee.query.get_or_404(employee_id)
    supervisor = Supervisor.query.filter_by(user_id=current_user.id).first()

    # Verify employee belongs to this supervisor's location
    if employee.location_id != supervisor.location_id:
        flash('You cannot edit this employee.', 'danger')
        return redirect(url_for('supervisor.employee_list'))

    form = EmployeeForm(obj=employee)

    if form.validate_on_submit():
        # Update employee fields
        employee.first_name = form.first_name.data
        employee.middle_name = form.middle_name.data
        employee.last_name = form.last_name.data
        employee.dob = form.dob.data
        employee.doj = form.doj.data
        employee.phone = form.phone.data
        employee.employee_code = form.employee_code.data
        employee.designation = form.designation.data
        employee.aadhaar_no = form.aadhaar_no.data
        employee.pan_no = form.pan_no.data
        employee.account_number = form.account_number.data
        employee.ifsc = form.ifsc.data
        employee.bank_name = form.bank_name.data
        employee.current_address = form.current_address.data
        employee.permanent_address = form.permanent_address.data

        # Handle image uploads
        def save_image(image_field):
            if image_field.data:
                filename = secure_filename(image_field.data.filename)
                path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                image_field.data.save(path)
                return f'uploads/{filename}'
            return None

        if form.aadhaar_image.data:
            employee.aadhaar_image = save_image(form.aadhaar_image)
        if form.pan_image.data:
            employee.pan_image = save_image(form.pan_image)
        if form.passbook_image.data:
            employee.passbook_image = save_image(form.passbook_image)
        if form.profile_image.data:
            employee.profile_image = save_image(form.profile_image)

        db.session.commit()
        flash('Employee updated successfully.', 'success')
        return redirect(url_for('supervisor.employee_list'))

    return render_template('supervisor/edit_employee.html', form=form, employee=employee)

@supervisor_bp.route('/add_employee', methods=['GET', 'POST'])
@login_required
def add_employee():
    if current_user.role != 'supervisor':
        return redirect(url_for('auth.login'))
    
    form = EmployeeForm()
    
    # Get supervisor details for the current user
    supervisor = current_user.supervisor
    if not supervisor:
        flash('No supervisor found for your account.', 'error')
        return redirect(url_for('supervisor.dashboard'))
    
    # Set form choices
    form.supervisor_id.choices = [(supervisor.id, f"{supervisor.first_name} {supervisor.last_name}")]  # Only current supervisor
    form.location_id.choices = [(loc.id, loc.name) for loc in Location.query.all()]
    
    # Check CSRF token before processing the form
    if request.method == 'POST':
        try:
            # Flask-WTF handles CSRF validation automatically
            if form.validate_on_submit():
                try:
                    # Create employee object
                    employee = Employee(
                        supervisor_id=supervisor.id,
                        location_id=form.location_id.data,
                        status='pending',
                        first_name=form.first_name.data,
                        middle_name=form.middle_name.data,
                        last_name=form.last_name.data,
                        employee_code=form.employee_code.data,
                        designation=form.designation.data,
                        dob=form.dob.data,
                        doj=form.doj.data,
                        phone=form.phone.data,
                        aadhaar_no=form.aadhaar_no.data,
                        pan_no=form.pan_no.data,
                        account_number=form.account_number.data,
                        ifsc=form.ifsc.data,
                        bank_name=form.bank_name.data,
                        current_address=form.current_address.data,
                        permanent_address=form.permanent_address.data
                    )
                    
                    # Save uploaded files
                    if form.aadhaar_image.data:
                        filename = secure_filename(form.aadhaar_image.data.filename)
                        form.aadhaar_image.data.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                        employee.aadhaar_image = filename
                    
                    if form.pan_image.data:
                        filename = secure_filename(form.pan_image.data.filename)
                        form.pan_image.data.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                        employee.pan_image = filename
                    
                    if form.passbook_image.data:
                        filename = secure_filename(form.passbook_image.data.filename)
                        form.passbook_image.data.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                        employee.passbook_image = filename
                    
                    if form.profile_image.data:
                        filename = secure_filename(form.profile_image.data.filename)
                        form.profile_image.data.save(os.path.join(current_app.config['PROFILE_FOLDER'], filename))
                        employee.profile_image = filename
                    
                    # Add to database
                    db.session.add(employee)
                    db.session.commit()
                    
                    flash('Employee added successfully!', 'success')
                    return redirect(url_for('supervisor.employee_list'))
                    
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error adding employee: {str(e)}', 'danger')
                    return redirect(url_for('supervisor.add_employee'))
            else:
                # Show form errors
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f'{field}: {error}', 'danger')
                        
        except Exception as e:
            flash('Invalid form submission. Please try again.', 'danger')
            return redirect(url_for('supervisor.add_employee'))
    
    return render_template('supervisor/add_employee.html', form=form)
