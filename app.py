from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from datetime import datetime

# Data models
class Course:
    def __init__(self, course_id, name, instructor, schedule, capacity):
        self.course_id = course_id
        self.name = name
        self.instructor = instructor
        self.schedule = schedule
        self.capacity = capacity
        self.enrolled_students = []
        
    def is_full(self):
        return len(self.enrolled_students) >= self.capacity
    
    def enroll_student(self, student):
        if not self.is_full() and student not in self.enrolled_students:
            self.enrolled_students.append(student)
            return True
        return False
    
    def drop_student(self, student):
        if student in self.enrolled_students:
            self.enrolled_students.remove(student)
            return True
        return False
    
    def get_available_seats(self):
        return self.capacity - len(self.enrolled_students)


class Student:
    def __init__(self, student_id, name, grade_level, password):
        self.student_id = student_id
        self.name = name
        self.grade_level = grade_level
        self.password = password  # In production, this should be hashed
        self.enrolled_courses = []
    
    def enroll(self, course):
        if course not in self.enrolled_courses and course.enroll_student(self):
            self.enrolled_courses.append(course)
            return True
        return False
    
    def drop(self, course):
        if course in self.enrolled_courses and course.drop_student(self):
            self.enrolled_courses.remove(course)
            return True
        return False


class EnrollmentSystem:
    def __init__(self):
        self.courses = {}
        self.students = {}
        self.admins = {}  # Basic admin accounts
    
    def add_course(self, course):
        self.courses[course.course_id] = course
    
    def remove_course(self, course_id):
        if course_id in self.courses:
            course = self.courses[course_id]
            # Automatically drop all students from this course
            for student in course.enrolled_students[:]:
                student.drop(course)
            del self.courses[course_id]
            return True
        return False
    
    def add_student(self, student):
        self.students[student.student_id] = student
    
    def add_admin(self, admin_id, name, password):
        self.admins[admin_id] = {"name": name, "password": password}
    
    def get_course(self, course_id):
        return self.courses.get(course_id)
    
    def get_student(self, student_id):
        return self.students.get(student_id)
    
    def verify_admin(self, admin_id, password):
        admin = self.admins.get(admin_id)
        if admin and admin["password"] == password:
            return True
        return False
    
    def list_all_courses(self):
        return list(self.courses.values())
    
    def list_all_students(self):
        return list(self.students.values())


from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from datetime import datetime
from models import Course, Student, EnrollmentSystem
from data_persistence import save_data, load_data

# Initialize the system
enrollment_system = EnrollmentSystem()

# Try to load data, if it fails, initialize with default data
if not load_data(enrollment_system):
    print("No existing data found or error loading data. Initializing with default data.")
    
    # Add some courses
    enrollment_system.add_course(Course("CS101", "Introduction to Programming", "Jomar Leano", "MWF 9:00-10:30", 30))
    enrollment_system.add_course(Course("BIO201", "Biology I", "Stephanie Mores", "TTh 10:30-12:00", 25))
    enrollment_system.add_course(Course("ENG101", "English Composition", "Vince Fernandez", "MWF 13:00-14:30", 35))
    enrollment_system.add_course(Course("PHYS101", "Physics I", "Marylou Bacordio", "TTh 14:00-15:30", 20))
    enrollment_system.add_course(Course("CHEM101", "Chemistry I", "Remar Bacula", "MWF 15:00-16:30", 40))

    # Add some students
    enrollment_system.add_student(Student("S1001", "Marlon Pabroa", 12, "pass123"))
    enrollment_system.add_student(Student("S1002", "Jackine Geoca", 12, "pass123"))
    enrollment_system.add_student(Student("S1003", "Ryle Cabanilla", 12, "pass123"))
    enrollment_system.add_student(Student("S1004", "Xyrill Mensoro", 12, "pass123"))
    enrollment_system.add_student(Student("S1005", "Norvy Daclan", 12, "pass123"))
    
    # Add an admin
    enrollment_system.add_admin("admin", "Administrator", "admin123")
    
    # Save the initial data
    save_data(enrollment_system)
else:
    print("Data loaded successfully.")

# Flask application
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']
        user_type = request.form['user_type']
        
        if user_type == 'student':
            student = enrollment_system.get_student(user_id)
            if student and student.password == password:
                session['user_id'] = user_id
                session['user_type'] = 'student'
                session['name'] = student.name
                flash('Login successful!', 'success')
                return redirect(url_for('student_dashboard'))
        
        elif user_type == 'admin':
            if enrollment_system.verify_admin(user_id, password):
                session['user_id'] = user_id
                session['user_type'] = 'admin'
                session['name'] = enrollment_system.admins[user_id]['name']
                flash('Admin login successful!', 'success')
                return redirect(url_for('admin_dashboard'))
        
        flash('Invalid credentials!', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/student/dashboard')
def student_dashboard():
    if 'user_id' not in session or session['user_type'] != 'student':
        flash('Please login first!', 'warning')
        return redirect(url_for('login'))
    
    student = enrollment_system.get_student(session['user_id'])
    all_courses = enrollment_system.list_all_courses()
    return render_template('student_dashboard.html', student=student, all_courses=all_courses)

@app.route('/student/enroll/<course_id>')
def enroll_course(course_id):
    if 'user_id' not in session or session['user_type'] != 'student':
        flash('Please login first!', 'warning')
        return redirect(url_for('login'))
    
    student = enrollment_system.get_student(session['user_id'])
    course = enrollment_system.get_course(course_id)
    
    if course and student.enroll(course):
        flash(f'Successfully enrolled in {course.name}!', 'success')
        save_data(enrollment_system)  # Save data after enrollment
    else:
        flash('Enrollment failed. Course might be full or you are already enrolled.', 'danger')
    
    return redirect(url_for('student_dashboard'))

@app.route('/student/drop/<course_id>')
def drop_course(course_id):
    if 'user_id' not in session or session['user_type'] != 'student':
        flash('Please login first!', 'warning')
        return redirect(url_for('login'))
    
    student = enrollment_system.get_student(session['user_id'])
    course = enrollment_system.get_course(course_id)
    
    if course and student.drop(course):
        flash(f'Successfully dropped {course.name}.', 'success')
        save_data(enrollment_system)  # Save data after dropping
    else:
        flash('Drop failed. You might not be enrolled in this course.', 'danger')
    
    return redirect(url_for('student_dashboard'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['user_type'] != 'admin':
        flash('Admin access required!', 'warning')
        return redirect(url_for('login'))
    
    return render_template('admin_dashboard.html', 
                          courses=enrollment_system.list_all_courses(),
                          students=enrollment_system.list_all_students())

@app.route('/admin/course/add', methods=['GET', 'POST'])
def add_course():
    if 'user_id' not in session or session['user_type'] != 'admin':
        flash('Admin access required!', 'warning')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        course_id = request.form['course_id']
        name = request.form['name']
        instructor = request.form['instructor']
        schedule = request.form['schedule']
        capacity = int(request.form['capacity'])
        
        # Check if course ID already exists
        if enrollment_system.get_course(course_id):
            flash('Course ID already exists!', 'danger')
        else:
            new_course = Course(course_id, name, instructor, schedule, capacity)
            enrollment_system.add_course(new_course)
            flash('Course added successfully!', 'success')
            save_data(enrollment_system)  # Save data after adding course
            return redirect(url_for('admin_dashboard'))
    
    return render_template('add_course.html')

@app.route('/admin/course/remove/<course_id>')
def remove_course(course_id):
    if 'user_id' not in session or session['user_type'] != 'admin':
        flash('Admin access required!', 'warning')
        return redirect(url_for('login'))
    
    if enrollment_system.remove_course(course_id):
        flash('Course removed successfully!', 'success')
        save_data(enrollment_system)  # Save data after removing course
    else:
        flash('Failed to remove course.', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/student/add', methods=['GET', 'POST'])
def add_student():
    if 'user_id' not in session or session['user_type'] != 'admin':
        flash('Admin access required!', 'warning')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        grade_level = int(request.form['grade_level'])
        password = request.form['password']
        
        # Check if student ID already exists
        if enrollment_system.get_student(student_id):
            flash('Student ID already exists!', 'danger')
        else:
            new_student = Student(student_id, name, grade_level, password)
            enrollment_system.add_student(new_student)
            flash('Student added successfully!', 'success')
            save_data(enrollment_system)  # Save data after adding student
            return redirect(url_for('admin_dashboard'))
    
    return render_template('add_student.html')

@app.route('/admin/course/<course_id>/roster')
def view_course_roster(course_id):
    if 'user_id' not in session or session['user_type'] != 'admin':
        flash('Admin access required!', 'warning')
        return redirect(url_for('login'))
    
    course = enrollment_system.get_course(course_id)
    if course:
        return render_template('course_roster.html', course=course)
    else:
        flash('Course not found!', 'danger')
        return redirect(url_for('admin_dashboard'))
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        grade_level = int(request.form['grade_level'])
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validate input
        errors = []
        
        # Check if ID already exists
        if enrollment_system.get_student(student_id):
            errors.append('Student ID already exists!')
        
        # Check if passwords match
        if password != confirm_password:
            errors.append('Passwords do not match!')
        
        # If there are no errors, create the new student
        if not errors:
            new_student = Student(student_id, name, grade_level, password)
            enrollment_system.add_student(new_student)
            flash('Registration successful! Please login.', 'success')
            save_data(enrollment_system)  # Save data after registration
            return redirect(url_for('login'))
        
        # If there are errors, show them
        for error in errors:
            flash(error, 'danger')
    
    return render_template('register.html')

@app.route('/student/finances')
def student_finances():
    if 'user_id' not in session or session['user_type'] != 'student':
        flash('Please login first!', 'warning')
        return redirect(url_for('login'))
    
    student = enrollment_system.get_student(session['user_id'])
    return render_template('student_finances.html', student=student)

@app.route('/student/make_payment', methods=['POST'])
def make_payment():
    if 'user_id' not in session or session['user_type'] != 'student':
        flash('Please login first!', 'warning')
        return redirect(url_for('login'))
    
    amount = float(request.form['amount'])
    payment_method = request.form['payment_method']
    
    student = enrollment_system.get_student(session['user_id'])
    if student.make_payment(amount, payment_method):
        flash(f'Payment of {amount} pesos successful!', 'success')
        save_data(enrollment_system)  # Save data after payment
    else:
        flash('Payment failed. Please check the amount.', 'danger')
    
    return redirect(url_for('student_finances'))


if __name__ == '__main__':
    app.run(debug=True)