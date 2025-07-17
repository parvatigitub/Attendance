import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file
from flask_login import login_required, current_user
from app.forms.location_form import LocationForm
from app.forms.employee_form import EmployeeForm
from app.forms.supervisor_form import SupervisorForm
from app.forms.csrf_form import CSRFOnlyForm
from app.models import User, Supervisor, Location, Employee, Attendance
from app import db
from sqlalchemy import or_
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
import os

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))
    
    form = EmployeeForm()
    form.supervisor_id.choices = [(sup.id, f"{sup.first_name} {sup.last_name}") for sup in Supervisor.query.all()]
    form.location_id.choices = [(loc.id, loc.name) for loc in Location.query.all()]
    
    # Get all employees
    employees = Employee.query.all()
    
    # Calculate statistics
    total_employees = len(employees)
    
    # Get present employees today
    today = datetime.now().date()
    present_employees = (
        db.session.query(Employee)
        .join(Attendance, Employee.id == Attendance.emp_id)
        .filter(Attendance.date == today, Attendance.status == 'P')
        .count()
    )

    return render_template('admin/dashboard.html',
                           form=form,
                           employees=employees,
                           total_employees=total_employees,
                           present_employees=present_employees)

@admin_bp.route('/mark_attendance/<int:emp_id>/<string:status>')
@login_required
def admin_mark_attendance(emp_id, status):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    # Get or create today's attendance record
    today = datetime.now().date()
    attendance = Attendance.query.filter_by(emp_id=emp_id, date=today).first()
    
    if not attendance:
        attendance = Attendance(
            emp_id=emp_id,
            date=today,
            status=status
        )
        db.session.add(attendance)
    else:
        attendance.status = status
    
    db.session.commit()
    
    return jsonify({'success': True})

@admin_bp.route('/employees', methods=['GET'])
@login_required
def employee_list():
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))
    
    supervisor_id = request.args.get('supervisor_id')
    location_id = request.args.get('location_id')
    search = request.args.get('search')

    # Get all employees for statistics
    all_employees = Employee.query.all()
    
    # Calculate statistics
    total_employees = len(all_employees)
    
    # Get present employees today
    today = datetime.now().date()
    present_employees = (
        db.session.query(Employee)
        .join(Attendance, Employee.id == Attendance.emp_id)
        .filter(Attendance.date == today, Attendance.status == 'P')
        .count()
    )

    # Apply filters to main query
    query = Employee.query

    if supervisor_id:
        query = query.filter(Employee.supervisor_id == supervisor_id)
    if location_id:
        query = query.filter(Employee.location_id == location_id)
    if search:
        query = query.filter(
            or_(
                Employee.first_name.ilike(f"%{search}%"),
                Employee.phone.ilike(f"%{search}%"),
                Employee.aadhaar_no.ilike(f"%{search}%")
            )
        )

    employees = query.all()
    supervisors = Supervisor.query.all()
    locations = Location.query.all()

    csrf_form = CSRFOnlyForm()
    return render_template('admin/employee_list.html', employees=employees,
                           supervisors=supervisors, locations=locations,
                           form=csrf_form,
                           total_employees=total_employees,
                           present_employees=present_employees)



@admin_bp.route('/locations', methods=['GET', 'POST'])
def locations():
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))

    form = LocationForm()
    locations = Location.query.all()
    today = datetime.now().date()

    # Get count of present employees per location
    present_data = (
        db.session.query(Location.id, db.func.count(Attendance.emp_id))
        .join(Employee, Employee.location_id == Location.id)
        .join(Attendance, Attendance.emp_id == Employee.id)
        .filter(Attendance.date == today, Attendance.status == 'P')
        .group_by(Location.id)
        .all()
    )
    present_counts = {loc_id: count for loc_id, count in present_data}

    if form.validate_on_submit():
        existing = Location.query.filter_by(name=form.name.data.strip()).first()
        if existing:
            flash('Location already exists.', 'warning')
        else:
            new_location = Location(name=form.name.data.strip())
            db.session.add(new_location)
            db.session.commit()
            flash('Location added successfully.', 'success')
            return redirect(url_for('admin.locations'))

    return render_template('admin/locations.html', form=form, locations=locations, present_counts=present_counts)

@admin_bp.route('/admin/location/edit/<int:id>', methods=['GET', 'POST'])
def edit_location(id):
    location = Location.query.get_or_404(id)
    form = LocationForm(obj=location)
    if form.validate_on_submit():
        location.name = form.name.data
        db.session.commit()
        flash("Location updated!", "success")
        return redirect(url_for('admin.locations'))
    return render_template('admin/edit_location.html', form=form)

@admin_bp.route('/admin/location/delete/<int:id>', methods=['POST'])
def delete_location(id):
    loc = Location.query.get_or_404(id)
    
    # Check if any supervisors are using this location
    supervisors = Supervisor.query.filter_by(location_id=id).all()
    if supervisors:
        flash("Cannot delete location because it's being used by supervisors. Please reassign supervisors first.", "danger")
        return redirect(url_for('admin.locations'))
    
    # Check if any employees are using this location
    employees = Employee.query.filter_by(location_id=id).all()
    if employees:
        flash("Cannot delete location because it's being used by employees. Please reassign employees first.", "danger")
        return redirect(url_for('admin.locations'))
    
    db.session.delete(loc)
    db.session.commit()
    flash("Location deleted!", "success")
    return redirect(url_for('admin.locations'))


@admin_bp.route('/add_supervisor', methods=['GET', 'POST'])
@login_required
def add_supervisor():
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))

    form = SupervisorForm()
    form.location_id.choices = [(loc.id, loc.name) for loc in Location.query.all()]

    if form.validate_on_submit():
        # Create user
        user = User(
            username=form.username.data,
            name=f"{form.first_name.data} {form.last_name.data}",
            role='supervisor'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        def save_image(image_field):
            filename = secure_filename(image_field.data.filename)
            path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            image_field.data.save(path)
            return f'uploads/{filename}'

        supervisor = Supervisor(
            user_id=user.id,
            location_id=form.location_id.data,
            first_name=form.first_name.data,
            middle_name=form.middle_name.data,
            last_name=form.last_name.data,
            dob=form.dob.data,
            doj=form.doj.data,
            phone=form.phone.data,
            employee_code=form.employee_code.data,
            esic_no=form.esic_no.data,
            uan_no=form.uan_no.data,
            aadhaar_no=form.aadhaar_no.data,
            pan_no=form.pan_no.data,
            designation=form.designation.data,
            account_number=form.account_number.data,
            ifsc=form.ifsc.data,
            bank_name=form.bank_name.data,
            aadhaar_image=save_image(form.aadhaar_image),
            pan_image=save_image(form.pan_image),
            passbook_image=save_image(form.passbook_image),
            profile_image=save_image(form.profile_image),
            current_address=form.current_address.data,
            permanent_address=form.permanent_address.data
        )

        db.session.add(supervisor)
        db.session.commit()

        flash('Supervisor registered successfully!', 'success')
        return redirect(url_for('admin.add_supervisor'))

    return render_template('admin/add_supervisor.html', form=form)

@admin_bp.route('/supervisors')
@login_required
def view_supervisors():
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))

    supervisors = Supervisor.query.all()
    return render_template('admin/view_supervisors.html', supervisors=supervisors)

@admin_bp.route('/approve-employees')
@login_required
def approve_employees():
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))
    pending_employees = Employee.query.filter_by(status='pending').all()
    return render_template('admin/approve_employees.html', employees=pending_employees)

@admin_bp.route('/download-attendance', methods=['GET'])
@login_required
def download_attendance():
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))

    # Get filter parameters
    supervisor_id = request.args.get('supervisor_id')
    location_id = request.args.get('location_id')
    search = request.args.get('search', '').strip()
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')

    # Build the base query
    query = db.session.query(
        Employee, Attendance
    ).join(
        Attendance, Employee.id == Attendance.emp_id, isouter=True
    )

    # Apply filters
    if supervisor_id:
        query = query.filter(Employee.supervisor_id == supervisor_id)
    if location_id:
        query = query.filter(Employee.location_id == location_id)
    if search:
        query = query.filter(
            or_(
                Employee.first_name.ilike(f'%{search}%'),
                Employee.last_name.ilike(f'%{search}%'),
                Employee.phone.ilike(f'%{search}%'),
                Employee.aadhaar_no.ilike(f'%{search}%')
            )
        )
    if from_date:
        try:
            from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
            query = query.filter(Attendance.date >= from_date)
        except ValueError:
            pass
    if to_date:
        try:
            to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
            query = query.filter(Attendance.date <= to_date)
        except ValueError:
            pass

    # Get all supervisors and locations for the filter form
    supervisors = Supervisor.query.all()
    locations = Location.query.all()

    # If it's a form submission (has any filter), generate Excel
    if any([supervisor_id, location_id, search, from_date, to_date]):
        records = query.all()
        
        # Prepare data for Excel
        data = []
        for emp, att in records:
            if att:  # Only include records with attendance
                data.append({
                    'Date': att.date.strftime('%Y-%m-%d'),
                    'Employee Name': f"{emp.first_name} {emp.last_name}",
                    'Employee Code': emp.employee_code,
                    'Phone': emp.phone,
                    'Aadhaar No': emp.aadhaar_no,
                    'Location': emp.location.name if emp.location else '',
                    'Supervisor': f"{emp.supervisor.first_name} {emp.supervisor.last_name}" if emp.supervisor else '',
                    'Status': att.status,'OT (hrs)': att.ot if att.ot is not None else 0 
                })
        
        # Create DataFrame and Excel file in memory
        if data:
            df = pd.DataFrame(data)
            output = BytesIO()
            df.to_excel(output, index=False, sheet_name='Attendance')
            output.seek(0)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"attendance_report_{timestamp}.xlsx"
            
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )
        else:
            flash('No attendance records found matching the criteria.', 'info')
    
    # If it's just a page load or no records found, render the template
    return render_template(
        'admin/download_attendance.html',
        supervisors=supervisors,
        locations=locations,
        current_supervisor=supervisor_id,
        current_location=location_id,
        current_search=search,
        current_from_date=from_date,
        current_to_date=to_date
    )

@admin_bp.route('/employee_action/<int:emp_id>/<string:action>')
@login_required
def employee_action(emp_id, action):
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))

    employee = Employee.query.get_or_404(emp_id)

    if action == 'accept':
        employee.status = 'approved'
        db.session.commit()
        flash('Employee approved successfully!', 'success')
    elif action == 'reject':
        employee.status = 'rejected'
        db.session.commit()
        flash('Employee rejected successfully!', 'success')

    return redirect(url_for('admin.employee_list'))

@admin_bp.route('/mark_attendance/<int:emp_id>/<string:status>')
@login_required
def mark_attendance(emp_id, status):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})

    employee = Employee.query.get_or_404(emp_id)
    
    # Get or create today's attendance record
    today = datetime.now().date()
    attendance = Attendance.query.filter_by(emp_id=emp_id, date=today).first()
    
    if not attendance:
        attendance = Attendance(
            emp_id=emp_id,
            date=today,
            status=status
        )
        db.session.add(attendance)
    else:
        attendance.status = status
    
    db.session.commit()
    
    return jsonify({'success': True})

@admin_bp.route('/employees/add', methods=['GET', 'POST'])
def add_employee():
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))

    form = EmployeeForm()
    form.supervisor_id.choices = [(sup.id, f"{sup.first_name} {sup.last_name}") for sup in Supervisor.query.all()]
    form.location_id.choices = [(loc.id, loc.name) for loc in Location.query.all()]

    if form.validate_on_submit():
        employee = Employee(
            supervisor_id=form.supervisor_id.data,
            location_id=form.location_id.data,
            first_name=form.first_name.data,
            middle_name=form.middle_name.data,
            last_name=form.last_name.data,
            dob=form.dob.data,
            doj=form.doj.data,
            phone=form.phone.data,
            employee_code=form.employee_code.data,
            esic_no=form.esic_no.data,
            uan_no=form.uan_no.data,
            aadhaar_no=form.aadhaar_no.data,
            pan_no=form.pan_no.data,
            designation=form.designation.data,
            account_number=form.account_number.data,
            ifsc=form.ifsc.data,
            bank_name=form.bank_name.data,
            current_address=form.current_address.data,
            permanent_address=form.permanent_address.data,
            status='pending'
        )
        db.session.add(employee)
        db.session.commit()
        flash('Employee added successfully!', 'success')
        return redirect(url_for('admin.employee_list'))

    return render_template('admin/add_employee.html', form=form)


@admin_bp.route('/edit_employee/<int:id>', methods=['GET', 'POST'])
def edit_employee(id):
    emp = Employee.query.get_or_404(id)
    form = EmployeeForm()
    
    # Populate form with employee data
    form.first_name.data = emp.first_name
    form.middle_name.data = emp.middle_name
    form.last_name.data = emp.last_name
    form.dob.data = emp.dob
    form.doj.data = emp.doj
    form.phone.data = emp.phone
    form.employee_code.data = emp.employee_code
    form.designation.data = emp.designation
    form.aadhaar_no.data = emp.aadhaar_no
    form.pan_no.data = emp.pan_no
    form.account_number.data = emp.account_number
    form.ifsc.data = emp.ifsc
    form.bank_name.data = emp.bank_name
    form.current_address.data = emp.current_address
    form.permanent_address.data = emp.permanent_address
    form.status.data = emp.status
    form.role.data = emp.role
    form.supervisor_id.data = emp.supervisor_id
    form.location_id.data = emp.location_id

    if form.validate_on_submit():
        form.populate_obj(emp)

        # Handle all file uploads
        upload_folder = os.path.join(current_app.root_path, 'static', 'profile_images')
        os.makedirs(upload_folder, exist_ok=True)

        # Handle profile image
        if form.profile_image.data:
            filename = secure_filename(form.profile_image.data.filename)
            file_path = os.path.join(upload_folder, filename)
            form.profile_image.data.save(file_path)
            emp.profile_image = f"profile_images/{filename}"

        # Handle aadhaar image
        if form.aadhaar_image.data:
            filename = secure_filename(form.aadhaar_image.data.filename)
            file_path = os.path.join(upload_folder, filename)
            form.aadhaar_image.data.save(file_path)
            emp.aadhaar_image = f"profile_images/{filename}"

        # Handle pan image
        if form.pan_image.data:
            filename = secure_filename(form.pan_image.data.filename)
            file_path = os.path.join(upload_folder, filename)
            form.pan_image.data.save(file_path)
            emp.pan_image = f"profile_images/{filename}"

        # Handle passbook image
        if form.passbook_image.data:
            filename = secure_filename(form.passbook_image.data.filename)
            file_path = os.path.join(upload_folder, filename)
            form.passbook_image.data.save(file_path)
            emp.passbook_image = f"profile_images/{filename}"

        db.session.commit()
        flash("Employee updated successfully", "success")
        return redirect(url_for('admin.employee_list'))

    return render_template('admin/edit_employee.html', form=form, employee=emp)

@admin_bp.route('/delete_employee/<int:id>', methods=['POST'])
@login_required
def delete_employee(id):
    if current_user.role != 'admin':
        flash("Access denied. Only admins can delete employees.", "danger")
        return redirect(url_for('admin.employee_list'))
    
    emp = Employee.query.get_or_404(id)
    try:
        # Delete associated files first
        upload_folder = os.path.join(current_app.root_path, 'static', 'profile_images')
        if emp.profile_image:
            profile_path = os.path.join(upload_folder, emp.profile_image.split('/')[-1])
            if os.path.exists(profile_path):
                os.remove(profile_path)
        
        if emp.aadhaar_image:
            aadhaar_path = os.path.join(upload_folder, emp.aadhaar_image.split('/')[-1])
            if os.path.exists(aadhaar_path):
                os.remove(aadhaar_path)
        
        if emp.pan_image:
            pan_path = os.path.join(upload_folder, emp.pan_image.split('/')[-1])
            if os.path.exists(pan_path):
                os.remove(pan_path)
        
        if emp.passbook_image:
            passbook_path = os.path.join(upload_folder, emp.passbook_image.split('/')[-1])
            if os.path.exists(passbook_path):
                os.remove(passbook_path)
        
        # Delete the employee record
        db.session.delete(emp)
        db.session.commit()
        flash("Employee deleted successfully", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting employee: {str(e)}", "danger")
    
    return redirect(url_for('admin.employee_list'))
