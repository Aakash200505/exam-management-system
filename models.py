from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, index=True)
    teacher_id = db.Column(db.String(20), unique=True, index=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    avatar = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    courses = db.relationship("Course", back_populates="teacher", cascade="all, delete-orphan", foreign_keys="Course.teacher_id")
    enrollments = db.relationship("Enrollment", back_populates="student", cascade="all, delete-orphan", foreign_keys="Enrollment.student_id")
    results = db.relationship("Result", back_populates="student", cascade="all, delete-orphan", foreign_keys="Result.student_id")
    questions_created = db.relationship("Question", back_populates="creator", foreign_keys="Question.created_by")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    teacher = db.relationship("User", back_populates="courses", foreign_keys=[teacher_id])
    exams = db.relationship("Exam", back_populates="course", cascade="all, delete-orphan")
    enrollments = db.relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")


class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    student = db.relationship("User", back_populates="enrollments", foreign_keys=[student_id])
    course = db.relationship("Course", back_populates="enrollments")
    __table_args__ = (db.UniqueConstraint("student_id", "course_id", name="unique_enrollment"),)


class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    duration = db.Column(db.Integer, nullable=False, default=30)
    total_marks = db.Column(db.Integer, nullable=False, default=0)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    course = db.relationship("Course", back_populates="exams")
    teacher = db.relationship("User", foreign_keys=[teacher_id])
    questions = db.relationship("Question", back_populates="exam", cascade="all, delete-orphan", order_by="Question.id")
    results = db.relationship("Result", back_populates="exam", cascade="all, delete-orphan")

    def refresh_total_marks(self):
        self.total_marks = sum(question.marks for question in self.questions)


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exam.id"), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255), nullable=False)
    option_b = db.Column(db.String(255), nullable=False)
    option_c = db.Column(db.String(255), nullable=False)
    option_d = db.Column(db.String(255), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)
    marks = db.Column(db.Integer, nullable=False, default=1)
    time_limit = db.Column(db.Integer, nullable=False, default=60)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    exam = db.relationship("Exam", back_populates="questions")
    creator = db.relationship("User", back_populates="questions_created", foreign_keys=[created_by])


class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey("exam.id"), nullable=False)
    score = db.Column(db.Integer, nullable=False, default=0)
    total_marks = db.Column(db.Integer, nullable=False, default=0)
    percentage = db.Column(db.Float, nullable=False, default=0)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    student = db.relationship("User", back_populates="results", foreign_keys=[student_id])
    exam = db.relationship("Exam", back_populates="results")
    __table_args__ = (db.UniqueConstraint("student_id", "exam_id", name="unique_result"),)
