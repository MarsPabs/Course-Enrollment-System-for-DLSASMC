# models.py
import datetime


class Course:
    def __init__(self, course_id, name, instructor, schedule, capacity, fee=1000):
        self.course_id = course_id
        self.name = name
        self.instructor = instructor
        self.schedule = schedule
        self.capacity = capacity
        self.fee = fee  # Course fee in pesos
        self.enrolled_students = []
        
    # Rest of the class remains the same
        
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
        self.balance = 0  # Initialize balance to 0
        self.transactions = []  # Initialize empty transactions list
    
    def enroll(self, course):
        if course not in self.enrolled_courses and course.enroll_student(self):
            self.enrolled_courses.append(course)
            # Add a charge for enrollment
            self.add_transaction(500, f"Enrollment fee for {course.name}", "charge")
            return True
        return False
    
    def drop(self, course):
        if course in self.enrolled_courses and course.drop_student(self):
            self.enrolled_courses.remove(course)
            return True
        return False
    
    def add_transaction(self, amount, description, type):
        """Add a transaction to the student's account
        
        Args:
            amount (float): Transaction amount
            description (str): Description of the transaction
            type (str): Either 'charge' or 'payment'
        """
        from datetime import datetime
        
        # Create transaction record
        transaction = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "description": description,
            "amount": amount,
            "type": type
        }
        
        # Add to transactions history
        self.transactions.append(transaction)
        
        # Update balance
        if type == "charge":
            self.balance += amount
        elif type == "payment":
            self.balance -= amount
    
    def make_payment(self, amount, payment_method):
        """Make a payment toward the student's balance
        
        Args:
            amount (float): Amount to pay
            payment_method (str): Method of payment
            
        Returns:
            bool: True if payment was successful, False otherwise
        """
        if amount <= 0 or amount > self.balance:
            return False
        
        self.add_transaction(amount, f"Payment via {payment_method}", "payment")
        return True

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