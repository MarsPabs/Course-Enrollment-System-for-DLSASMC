import json
import os
from datetime import datetime
from models import Course, Student

class DataEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle objects"""
    def default(self, obj):
        if hasattr(obj, '__dict__'):
            # Convert object to dictionary
            obj_dict = obj.__dict__.copy()
            
            # Handle circular references
            if 'enrolled_students' in obj_dict:
                obj_dict['enrolled_students'] = [student.student_id for student in obj_dict['enrolled_students']]
            
            if 'enrolled_courses' in obj_dict:
                obj_dict['enrolled_courses'] = [course.course_id for course in obj_dict['enrolled_courses']]
            
            return obj_dict
        return super().default(obj)

def save_data(enrollment_system, data_dir='data'):
    """Save enrollment system data to JSON files"""
    # Create data directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    
    # Save courses
    with open(os.path.join(data_dir, 'courses.json'), 'w') as f:
        json.dump(list(enrollment_system.courses.values()), f, cls=DataEncoder, indent=2)
    
    # Save students
    with open(os.path.join(data_dir, 'students.json'), 'w') as f:
        json.dump(list(enrollment_system.students.values()), f, cls=DataEncoder, indent=2)
    
    # Save admins
    with open(os.path.join(data_dir, 'admins.json'), 'w') as f:
        json.dump(enrollment_system.admins, f, indent=2)
    
    # Save timestamp
    with open(os.path.join(data_dir, 'last_save.txt'), 'w') as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def load_data(enrollment_system, data_dir='data'):
    """Load enrollment system data from JSON files"""
    # Check if data directory exists
    if not os.path.exists(data_dir):
        return False
    
    try:
        # Load courses
        if os.path.exists(os.path.join(data_dir, 'courses.json')):
            with open(os.path.join(data_dir, 'courses.json'), 'r') as f:
                courses_data = json.load(f)
                
                # Clear existing courses
                enrollment_system.courses = {}
                
                # Create course objects
                for course_data in courses_data:
                    course = Course(
                        course_data['course_id'],
                        course_data['name'],
                        course_data['instructor'],
                        course_data['schedule'],
                        course_data['capacity']
                    )
                    enrollment_system.courses[course.course_id] = course
        
        # Load students
        if os.path.exists(os.path.join(data_dir, 'students.json')):
            with open(os.path.join(data_dir, 'students.json'), 'r') as f:
                students_data = json.load(f)
                
                # Clear existing students
                enrollment_system.students = {}
                
                # Create student objects
                for student_data in students_data:
                    student = Student(
                        student_data['student_id'],
                        student_data['name'],
                        student_data['grade_level'],
                        student_data['password']
                    )
                    
                    # Set financial attributes if they exist in the loaded data
                    if 'balance' in student_data:
                        student.balance = student_data['balance']
                    if 'transactions' in student_data:
                        student.transactions = student_data['transactions']
                        
                    enrollment_system.students[student.student_id] = student
        
        # Load admins
        if os.path.exists(os.path.join(data_dir, 'admins.json')):
            with open(os.path.join(data_dir, 'admins.json'), 'r') as f:
                enrollment_system.admins = json.load(f)
        
        # Restore relationships
        if os.path.exists(os.path.join(data_dir, 'courses.json')) and os.path.exists(os.path.join(data_dir, 'students.json')):
            with open(os.path.join(data_dir, 'courses.json'), 'r') as f:
                courses_data = json.load(f)
                
                # Restore enrolled_students in courses
                for course_data in courses_data:
                    course = enrollment_system.courses.get(course_data['course_id'])
                    if course:
                        for student_id in course_data['enrolled_students']:
                            student = enrollment_system.students.get(student_id)
                            if student:
                                course.enrolled_students.append(student)
            
            with open(os.path.join(data_dir, 'students.json'), 'r') as f:
                students_data = json.load(f)
                
                # Restore enrolled_courses in students
                for student_data in students_data:
                    student = enrollment_system.students.get(student_data['student_id'])
                    if student:
                        for course_id in student_data['enrolled_courses']:
                            course = enrollment_system.courses.get(course_id)
                            if course:
                                student.enrolled_courses.append(course)
        
        return True
    
    except Exception as e:
        print(f"Error loading data: {e}")
        return False