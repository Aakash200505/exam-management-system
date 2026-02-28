from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='student')  # admin, teacher, student
    bio = db.Column(db.String(256))
    avatar_url = db.Column(db.String(256))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    teacher = db.relationship('User', backref='courses_taught')
    exams = db.relationship('Exam', backref='course', cascade='all, delete-orphan', lazy='dynamic')
    students = db.relationship('User', secondary='enrollment', back_populates='enrolled_courses')

enrollment = db.Table('enrollment',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('course.id'), primary_key=True),
    db.Column('date_enrolled', db.DateTime, default=datetime.utcnow)
)

# Update User model to include enrolled_courses
User.enrolled_courses = db.relationship('Course', secondary=enrollment, back_populates='students')

class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    duration_minutes = db.Column(db.Integer, default=60)
    
    questions = db.relationship('Question', backref='exam', cascade='all, delete-orphan', lazy='dynamic')

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'))
    text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(200))
    option_b = db.Column(db.String(200))
    option_c = db.Column(db.String(200))
    option_d = db.Column(db.String(200))
    correct_option = db.Column(db.String(1))  # 'A', 'B', 'C', or 'D'
    marks = db.Column(db.Integer, default=1)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'))
    score = db.Column(db.Float)
    total_marks = db.Column(db.Integer)
    date_taken = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('User', backref='results')
    exam = db.relationship('Exam', backref='results')
