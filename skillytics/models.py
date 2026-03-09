from datetime import datetime
from skillytics import db, login_manager, bcrypt
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    # First, try to find the user in the Student table
    user = Student.query.get(int(user_id))
    if user:
        return user

    # If not found, try to find the user in the Staff table
    return Staff.query.get(int(user_id))

class Staff(db.Model, UserMixin):
    __tablename__ = 'staff'
    staff_id = db.Column(db.Integer, primary_key=True)
    picture = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(100))
    address = db.Column(db.String(200))
    institution_name = db.Column(db.String(100))
    faculty_name = db.Column(db.String(100))
    last_online = db.Column(db.DateTime)

    feedbacks = db.relationship('Feedback', backref='staff', lazy=True)
    notifications = db.relationship('Notification', backref='staff', lazy=True)

    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.password, attempted_password)

    def get_id(self):
        return str(self.staff_id)

    def get_role(self):
        return 'Staff'
    
    def get_position(self):
        return str(self.position)

class Student(db.Model, UserMixin):
    __tablename__ = 'student'
    student_id = db.Column(db.Integer, primary_key=True)
    picture = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    phone_number = db.Column(db.String(100))
    address = db.Column(db.String(200))
    part_id = db.Column(db.Integer, db.ForeignKey('part.part_id'))
    institution_name = db.Column(db.String(100))
    faculty_name = db.Column(db.String(100))
    program_code = db.Column(db.String(100))
    last_online = db.Column(db.DateTime)
    status = db.Column(db.String(20), nullable=False)

    enrollments = db.relationship('Enrollment', backref='student', lazy=True, cascade="all, delete-orphan")
    technical_skill_scores = db.relationship('TechnicalSkillScore', backref='student', lazy=True, cascade="all, delete-orphan")
    student_part_gpas = db.relationship('StudentPartGPA', backref='student', lazy=True, cascade="all, delete-orphan")
    student_semester_clusters = db.relationship('StudentSemesterCluster', backref='student', lazy=True, cascade="all, delete-orphan")
    feedbacks = db.relationship('Feedback', backref='student', lazy=True, cascade="all, delete-orphan")

    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.password, attempted_password)

    def get_id(self):
        return str(self.student_id)

    def get_role(self):
        return 'Student'


class Part(db.Model):
    __tablename__ = 'part'
    part_id = db.Column(db.Integer, primary_key=True)
    part_no = db.Column(db.Integer, nullable=False)

    students = db.relationship('Student', backref='part', lazy=True)
    courses = db.relationship('Course', backref='part', lazy=True)
    student_part_gpas = db.relationship('StudentPartGPA', backref='part', lazy=True)
    student_semester_clusters = db.relationship('StudentSemesterCluster', backref='part', lazy=True)
    notifications = db.relationship('Notification', backref='part', lazy=True)
    technical_skill_scores = db.relationship('TechnicalSkillScore', backref='part', lazy=True)
    enrollments = db.relationship('Enrollment', backref='part', lazy=True)

class Course(db.Model):
    __tablename__ = 'course'
    course_code = db.Column(db.String(20), unique=True, primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey('part.part_id'))
    course_name = db.Column(db.String(100))
    credit_hour = db.Column(db.Float)

    enrollments = db.relationship('Enrollment', backref='course', lazy=True)

class Enrollment(db.Model):
    __tablename__ = 'enrollment'
    enrollment_id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey('part.part_id'))
    student_id = db.Column(db.Integer, db.ForeignKey('student.student_id', ondelete='CASCADE'))
    course_code = db.Column(db.String(20), db.ForeignKey('course.course_code'))
    course_grade = db.Column(db.String(5))

class TechnicalSkillCategory(db.Model):
    __tablename__ = 'technical_skill_category'
    technical_skill_category_id = db.Column(db.Integer, primary_key=True)
    ts_type = db.Column(db.String(50), unique=True)

    technical_skill_scores = db.relationship('TechnicalSkillScore', backref='technical_skill_category', lazy=True)

class TechnicalSkillScore(db.Model):
    __tablename__ = 'technical_skill_score'
    technical_skill_score_id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey('part.part_id'))
    technical_skill_category_id = db.Column(db.Integer, db.ForeignKey('technical_skill_category.technical_skill_category_id'))
    student_id = db.Column(db.Integer, db.ForeignKey('student.student_id', ondelete='CASCADE'))
    q1_score = db.Column(db.Integer)
    q2_score = db.Column(db.Integer)
    q3_score = db.Column(db.Integer)
    q4_score = db.Column(db.Integer)
    q5_score = db.Column(db.Integer)

    def get_q1_score(self):
        return (self.q1_score)

class StudentPartGPA(db.Model):
    __tablename__ = 'student_part_gpa'
    gpa_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.student_id', ondelete='CASCADE'))
    part_id = db.Column(db.Integer, db.ForeignKey('part.part_id'))
    gpa = db.Column(db.Float)

class StudentSemesterCluster(db.Model):
    __tablename__ = 'student_semester_cluster'
    cluster_id = db.Column(db.Integer, primary_key=True)
    cluster_both = db.Column(db.Integer)
    cluster_academic = db.Column(db.Integer)
    cluster_technical_skills = db.Column(db.Integer)
    student_id = db.Column(db.Integer, db.ForeignKey('student.student_id', ondelete='CASCADE'))
    part_id = db.Column(db.Integer, db.ForeignKey('part.part_id'))

class Feedback(db.Model):
    __tablename__ = 'feedback'
    feedback_id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    time_sent = db.Column(db.DateTime, default=datetime.utcnow)
    student_id = db.Column(db.Integer, db.ForeignKey('student.student_id', ondelete='CASCADE'))
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id'))

class Notification(db.Model):
    __tablename__ = 'notification'
    notification_id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.staff_id'))
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    time_sent = db.Column(db.DateTime, default=datetime.utcnow)
    part_id = db.Column(db.Integer, db.ForeignKey('part.part_id'))
    cluster_type = db.Column(db.String(255))
    cluster_no = db.Column(db.Integer)
