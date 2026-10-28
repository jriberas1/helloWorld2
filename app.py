import os
import re
from datetime import datetime as dt

from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Student, Major


# --------------------------------------------------
# Initialize the Flask application
# --------------------------------------------------
app = Flask(__name__)

# Use the existing database in the instance directory.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'sqlite:///' + os.path.join(app.instance_path, 'university.db')
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'beyond_course_scope'

db.init_app(app)


# --------------------------------------------------
# Validate the student's email address
# --------------------------------------------------
def valid_email(email):
    """Check that the email is present, valid, and at most 100 characters."""
    if not email or len(email) > 100:
        return False

    return bool(re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email))


# --------------------------------------------------
# View all students
# --------------------------------------------------
@app.route('/student/view')
def student_view_all():
    students = (
        Student.query
        .outerjoin(Major, Student.major_id == Major.major_id)
        .add_entity(Major)
        .order_by(Student.last_name, Student.first_name)
        .all()
    )

    return render_template(
        'student_view_all.html',
        students=students
    )


# --------------------------------------------------
# View an individual student
# --------------------------------------------------
@app.route('/student/view/<int:student_id>')
def student_view(student_id):
    student = Student.query.filter_by(student_id=student_id).first()
    majors = Major.query.order_by(Major.major).all()

    if student:
        return render_template(
            'student_entry.html',
            student=student,
            majors=majors,
            action='read'
        )

    flash('Student attempting to be viewed could not be found!', 'error')
    return redirect(url_for('student_view_all'))


# --------------------------------------------------
# Add a new student
# --------------------------------------------------
@app.route('/student/create', methods=['GET', 'POST'])
def student_create():
    if request.method == 'GET':
        majors = Major.query.order_by(Major.major).all()

        return render_template(
            'student_entry.html',
            majors=majors,
            action='create'
        )

    # Collect the submitted form values.
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip()
    major_id = request.form.get('major_id', '')
    birth_date = request.form.get('birth_date', '')
    is_honors = 'is_honors' in request.form

    # Validate the required name fields.
    if not first_name or len(first_name) > 30:
        flash('Enter a first name of 1 to 30 characters.', 'error')
        return redirect(url_for('student_create'))

    if not last_name or len(last_name) > 50:
        flash('Enter a last name of 1 to 50 characters.', 'error')
        return redirect(url_for('student_create'))

    # Email is required and cannot exceed 100 characters.
    if not valid_email(email):
        flash(
            'Enter a valid email address of no more than 100 characters.',
            'error'
        )
        return redirect(url_for('student_create'))

    # Make sure the selected major exists.
    major = (
        db.session.get(Major, int(major_id))
        if major_id.isdigit() else None
    )

    if not major:
        flash('Please select a valid major.', 'error')
        return redirect(url_for('student_create'))

    # Validate the birth date.
    try:
        parsed_birth_date = dt.strptime(birth_date, '%Y-%m-%d')
    except ValueError:
        flash('Please enter a valid birth date.', 'error')
        return redirect(url_for('student_create'))

    # Create the student record.
    student = Student(
        first_name=first_name,
        last_name=last_name,
        email=email,
        major_id=major.major_id,
        birth_date=parsed_birth_date,
        is_honors=is_honors
    )

    db.session.add(student)
    db.session.commit()

    flash(
        f'{first_name} {last_name} was successfully added!',
        'success'
    )
    return redirect(url_for('student_view_all'))


# --------------------------------------------------
# Update an existing student
# --------------------------------------------------
@app.route('/student/update/<int:student_id>', methods=['GET', 'POST'])
def student_edit(student_id):
    student = Student.query.filter_by(student_id=student_id).first()

    if not student:
        flash('Student attempting to be edited could not be found!', 'error')
        return redirect(url_for('student_view_all'))

    if request.method == 'GET':
        majors = Major.query.order_by(Major.major).all()

        return render_template(
            'student_entry.html',
            student=student,
            majors=majors,
            action='update'
        )

    # Collect the submitted form values.
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip()
    major_id = request.form.get('major_id', '')
    birth_date = request.form.get('birth_date', '')
    credits = request.form.get('num_credits_completed', '')
    gpa = request.form.get('gpa', '')
    is_honors = 'is_honors' in request.form

    # Validate the required name fields.
    if not first_name or len(first_name) > 30:
        flash('Enter a first name of 1 to 30 characters.', 'error')
        return redirect(url_for('student_edit', student_id=student_id))

    if not last_name or len(last_name) > 50:
        flash('Enter a last name of 1 to 50 characters.', 'error')
        return redirect(url_for('student_edit', student_id=student_id))

    # Validate the required email address.
    if not valid_email(email):
        flash(
            'Enter a valid email address of no more than 100 characters.',
            'error'
        )
        return redirect(url_for('student_edit', student_id=student_id))

    # Validate the selected major.
    major = (
        db.session.get(Major, int(major_id))
        if major_id.isdigit() else None
    )

    if not major:
        flash('Please select a valid major.', 'error')
        return redirect(url_for('student_edit', student_id=student_id))

    # Validate the birth date.
    try:
        parsed_birth_date = dt.strptime(birth_date, '%Y-%m-%d')
    except ValueError:
        flash('Please enter a valid birth date.', 'error')
        return redirect(url_for('student_edit', student_id=student_id))

    # Validate credits and GPA.
    try:
        parsed_credits = int(credits)
        parsed_gpa = float(gpa)

        if not 0 <= parsed_credits <= 200:
            raise ValueError

        if not 0.0 <= parsed_gpa <= 4.0:
            raise ValueError

    except (ValueError, TypeError):
        flash(
            'Credits must be between 0 and 200, and GPA between 0.00 and 4.00.',
            'error'
        )
        return redirect(url_for('student_edit', student_id=student_id))

    # Save the updated student information.
    student.first_name = first_name
    student.last_name = last_name
    student.email = email
    student.major_id = major.major_id
    student.birth_date = parsed_birth_date
    student.num_credits_completed = parsed_credits
    student.gpa = parsed_gpa
    student.is_honors = is_honors

    db.session.commit()

    flash(
        f'{student.first_name} {student.last_name} was successfully updated!',
        'success'
    )
    return redirect(url_for('student_view_all'))


# --------------------------------------------------
# Delete a student
# --------------------------------------------------
@app.route('/student/delete/<int:student_id>')
def student_delete(student_id):
    student = Student.query.filter_by(student_id=student_id).first()

    if student:
        student_name = str(student)
        db.session.delete(student)
        db.session.commit()
        flash(f'{student_name} was successfully deleted!', 'success')
    else:
        flash('Delete failed! Student could not be found.', 'error')

    return redirect(url_for('student_view_all'))


# --------------------------------------------------
# Redirect the home page to the student list
# --------------------------------------------------
@app.route('/')
def home():
    return redirect(url_for('student_view_all'))


# --------------------------------------------------
# Run the application
# --------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)