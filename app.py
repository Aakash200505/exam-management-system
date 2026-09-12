import os
import re
import secrets
import smtplib
from datetime import datetime
from email.message import EmailMessage
from functools import wraps
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func
from werkzeug.utils import secure_filename

from config import Config, INSTANCE_DIR
from extensions import db, login_manager, migrate
from models import Course, Enrollment, Exam, Question, Result, User

PASSWORD_RULE = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{10,}$")
EMAIL_RULE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _next_identity_id(model, field, prefix):
    values = db.session.query(field).filter(field.isnot(None)).all()
    numbers = []
    for (value,) in values:
        if value and value.startswith(prefix) and value[len(prefix):].isdigit():
            numbers.append(int(value[len(prefix):]))
    candidate = max(numbers, default=0) + 1
    identity = f"{prefix}{candidate:04d}"
    while db.session.query(model).filter(field == identity).first():
        candidate += 1
        identity = f"{prefix}{candidate:04d}"
    return identity


def generate_student_id():
    return _next_identity_id(User, User.student_id, "STU")


def generate_teacher_id():
    return _next_identity_id(User, User.teacher_id, "TCH")


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "login"

    with app.app_context():
        _prepare_database()
        db.create_all()

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    def role_required(role):
        def decorator(view):
            @wraps(view)
            @login_required
            def wrapped(*args, **kwargs):
                if current_user.role != role:
                    abort(403)
                return view(*args, **kwargs)
            return wrapped
        return decorator

    def password_error(password):
        if not PASSWORD_RULE.fullmatch(password or ""):
            return "Password must be at least 10 characters and include uppercase, lowercase, a number, and a special character."
        return None

    def positive(value, default=1):
        try:
            return max(1, int(value))
        except (TypeError, ValueError):
            return default

    def nonnegative(value, default=0):
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return default

    def owns_course(course):
        return current_user.role == "teacher" and course.teacher_id == current_user.id

    def owns_exam(exam):
        return current_user.role == "teacher" and exam.teacher_id == current_user.id

    def send_enrollment_email(student, course, address, enrolled_at):
        if not app.config.get("MAIL_SERVER") or not app.config.get("MAIL_DEFAULT_SENDER"):
            return False
        message = EmailMessage()
        message["Subject"] = "Course Enrollment Confirmation"
        message["From"] = app.config["MAIL_DEFAULT_SENDER"]
        message["To"] = address
        message.set_content(f"Hello {student.full_name},\n\nYou have successfully enrolled in {course.name}.\n\nEnrollment Date: {enrolled_at:%Y-%m-%d}\n\nThank you.")
        with smtplib.SMTP(app.config["MAIL_SERVER"], app.config["MAIL_PORT"]) as server:
            if app.config["MAIL_USE_TLS"]:
                server.starttls()
            if app.config.get("MAIL_USERNAME"):
                server.login(app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
            server.send_message(message)
        return True

    @app.context_processor
    def inject_helpers():
        def avatar_url(user):
            return url_for("uploaded_avatar", filename=user.avatar) if user and user.avatar else url_for("static", filename="images/default-avatar.svg")
        return {"avatar_url": avatar_url, "now": datetime.utcnow}

    @app.route("/uploads/avatars/<path:filename>")
    def uploaded_avatar(filename):
        from flask import send_from_directory
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.route("/")
    def index():
        return redirect(url_for("dashboard")) if current_user.is_authenticated else render_template("index.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            first_name = request.form.get("first_name", "").strip()
            last_name = request.form.get("last_name", "").strip()
            username = request.form.get("username", "").strip().lower()
            password = request.form.get("password", "")
            role = request.form.get("role", "")
            error = password_error(password)
            if not first_name or not last_name or not username or role not in {"teacher", "student"}:
                flash("Complete all registration fields.", "danger")
            elif error:
                flash(error, "danger")
            elif password != request.form.get("confirmation", ""):
                flash("Passwords do not match.", "danger")
            else:
                user = User(
                    first_name=first_name,
                    last_name=last_name,
                    username=username,
                    role=role,
                    student_id=generate_student_id() if role == "student" else None,
                    teacher_id=generate_teacher_id() if role == "teacher" else None,
                )
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                flash("Account created. You can now log in.", "success")
                return redirect(url_for("login"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            candidates = User.query.filter_by(
                username=request.form.get("username", "").strip().lower(),
                role=request.form.get("role", ""),
            ).order_by(User.id).all()
            role = request.form.get("role", "")
            for user in candidates:
                if user.check_password(request.form.get("password", "")):
                    login_user(user)
                    return redirect(request.args.get("next") or url_for("dashboard"))
            flash("Invalid username, password, or role.", "danger")
        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("index"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        return redirect(url_for("teacher_dashboard" if current_user.role == "teacher" else "student_dashboard"))

    @app.route("/teacher")
    @role_required("teacher")
    def teacher_dashboard():
        courses = Course.query.filter_by(teacher_id=current_user.id).all()
        exams = Exam.query.filter_by(teacher_id=current_user.id).order_by(Exam.created_at.desc()).limit(5).all()
        questions = Question.query.filter_by(created_by=current_user.id).count()
        student_count = db.session.query(func.count(func.distinct(Enrollment.student_id))).join(Course).filter(Course.teacher_id == current_user.id).scalar() or 0
        results = Result.query.join(Exam).filter(Exam.teacher_id == current_user.id).order_by(Result.submitted_at.desc()).limit(6).all()
        return render_template("teacher_dashboard.html", courses=courses, exams=exams, question_count=questions, student_count=student_count, results=results)

    @app.route("/student")
    @role_required("student")
    def student_dashboard():
        enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
        course_ids = [item.course_id for item in enrollments]
        exams = Exam.query.filter(Exam.course_id.in_(course_ids), Exam.is_active.is_(True)).all() if course_ids else []
        results = Result.query.filter_by(student_id=current_user.id).order_by(Result.submitted_at.desc()).limit(5).all()
        return render_template("student_dashboard.html", enrollments=enrollments, exams=exams, results=results)

    @app.route("/profile")
    @login_required
    def profile():
        return render_template("profile.html")

    @app.route("/profile/edit", methods=["GET", "POST"])
    @login_required
    def edit_profile():
        if request.method == "POST":
            first_name = request.form.get("first_name", "").strip()
            last_name = request.form.get("last_name", "").strip()
            username = request.form.get("username", "").strip().lower()
            if not first_name or not last_name or not username:
                flash("First name, last name, and username are required.", "danger")
            else:
                current_user.first_name = first_name
                current_user.last_name = last_name
                current_user.username = username
                new_password = request.form.get("new_password", "")
                if new_password:
                    error = password_error(new_password)
                    if error:
                        flash(error, "danger")
                        return render_template("edit_profile.html")
                    if new_password != request.form.get("confirmation", ""):
                        flash("Passwords do not match.", "danger")
                        return render_template("edit_profile.html")
                    current_user.set_password(new_password)
                avatar = request.files.get("avatar")
                if avatar and avatar.filename:
                    extension = Path(avatar.filename).suffix.lower().lstrip(".")
                    if extension not in app.config["ALLOWED_AVATAR_EXTENSIONS"]:
                        flash("Avatar must be PNG, JPG, JPEG, or WEBP.", "danger")
                        return render_template("edit_profile.html")
                    header = avatar.stream.read(12)
                    avatar.stream.seek(0)
                    valid_signature = (
                        (extension == "png" and header.startswith(b"\x89PNG\r\n\x1a\n"))
                        or (extension in {"jpg", "jpeg"} and header.startswith(b"\xff\xd8\xff"))
                        or (extension == "webp" and header[:4] == b"RIFF" and header[8:12] == b"WEBP")
                    )
                    if not valid_signature:
                        flash("The avatar file is not a valid image.", "danger")
                        return render_template("edit_profile.html")
                    filename = f"{current_user.id}-{secrets.token_hex(8)}.{extension}"
                    avatar.save(os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(filename)))
                    current_user.avatar = filename
                db.session.commit()
                flash("Profile updated.", "success")
                return redirect(url_for("profile"))
        return render_template("edit_profile.html")

    @app.route("/courses")
    @login_required
    def courses():
        search = request.args.get("q", "").strip()
        query = Course.query.order_by(Course.name)
        if search:
            query = query.filter(Course.name.ilike(f"%{search}%"))
        return render_template("courses.html", courses=query.all())

    @app.route("/courses/create", methods=["GET", "POST"])
    @role_required("teacher")
    def create_course():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            if not name:
                flash("Course name is required.", "danger")
            else:
                db.session.add(Course(name=name, description=request.form.get("description", "").strip(), teacher_id=current_user.id))
                db.session.commit()
                flash("Course created.", "success")
                return redirect(url_for("courses"))
        return render_template("create_course.html", course=None)

    @app.route("/courses/<int:course_id>")
    @login_required
    def course_detail(course_id):
        course = db.get_or_404(Course, course_id)
        enrolled = Enrollment.query.filter_by(student_id=current_user.id, course_id=course.id).first() if current_user.role == "student" else None
        return render_template("course_detail.html", course=course, enrolled=enrolled)

    @app.route("/courses/<int:course_id>/edit", methods=["GET", "POST"])
    @role_required("teacher")
    def edit_course(course_id):
        course = db.get_or_404(Course, course_id)
        if not owns_course(course): abort(403)
        if request.method == "POST":
            course.name = request.form.get("name", "").strip()
            course.description = request.form.get("description", "").strip()
            db.session.commit()
            flash("Course updated.", "success")
            return redirect(url_for("course_detail", course_id=course.id))
        return render_template("edit_course.html", course=course)

    @app.post("/courses/<int:course_id>/delete")
    @role_required("teacher")
    def delete_course(course_id):
        course = db.get_or_404(Course, course_id)
        if not owns_course(course): abort(403)
        db.session.delete(course)
        db.session.commit()
        return redirect(url_for("courses"))

    @app.route("/courses/<int:course_id>/enroll", methods=["GET", "POST"])
    @role_required("student")
    def enroll(course_id):
        course = db.get_or_404(Course, course_id)
        if Enrollment.query.filter_by(student_id=current_user.id, course_id=course.id).first():
            flash("You are already enrolled in this course.", "info")
            return redirect(url_for("course_detail", course_id=course.id))
        if request.method == "POST":
            address = request.form.get("email", "").strip()
            if not EMAIL_RULE.fullmatch(address):
                flash("Enter a valid email address.", "danger")
            else:
                enrollment = Enrollment(student_id=current_user.id, course_id=course.id, email=address)
                db.session.add(enrollment)
                db.session.commit()
                try:
                    sent = send_enrollment_email(current_user, course, address, enrollment.enrolled_at)
                except (OSError, smtplib.SMTPException):
                    sent = False
                flash("You have successfully enrolled in this course." + (" Confirmation email sent." if sent else " Email delivery is not configured locally."), "success")
                return redirect(url_for("course_detail", course_id=course.id))
        return render_template("enroll.html", course=course)

    @app.route("/exams")
    @login_required
    def exams():
        query = Exam.query.order_by(Exam.created_at.desc())
        if current_user.role == "teacher": query = query.filter_by(teacher_id=current_user.id)
        return render_template("exam_detail.html", exams=query.all(), exam=None)

    @app.route("/exams/create", methods=["GET", "POST"])
    @role_required("teacher")
    def create_exam():
        courses_list = Course.query.filter_by(teacher_id=current_user.id).all()
        if request.method == "POST":
            course = db.session.get(Course, request.form.get("course_id", type=int))
            if not course or not owns_course(course): abort(403)
            exam = Exam(title=request.form.get("title", "").strip(), description=request.form.get("description", "").strip(), duration=positive(request.form.get("duration"), 30), total_marks=nonnegative(request.form.get("total_marks")), course_id=course.id, teacher_id=current_user.id, is_active=bool(request.form.get("is_active")))
            db.session.add(exam); db.session.commit()
            return redirect(url_for("question_list", exam_id=exam.id))
        return render_template("create_exam.html", exam=None, courses=courses_list)

    @app.route("/exams/<int:exam_id>")
    @login_required
    def exam_detail(exam_id):
        exam = db.get_or_404(Exam, exam_id)
        return render_template("exam_detail.html", exam=exam, exams=None)

    @app.route("/exams/<int:exam_id>/edit", methods=["GET", "POST"])
    @role_required("teacher")
    def edit_exam(exam_id):
        exam = db.get_or_404(Exam, exam_id)
        if not owns_exam(exam): abort(403)
        if request.method == "POST":
            course = db.session.get(Course, request.form.get("course_id", type=int))
            if not course or not owns_course(course): abort(403)
            exam.title = request.form.get("title", "").strip(); exam.description = request.form.get("description", "").strip(); exam.duration = positive(request.form.get("duration"), 30); exam.total_marks = nonnegative(request.form.get("total_marks"), exam.total_marks); exam.course_id = course.id; exam.is_active = bool(request.form.get("is_active")); db.session.commit()
            flash("Exam updated.", "success")
            return redirect(url_for("exam_detail", exam_id=exam.id))
        return render_template("edit_exam.html", exam=exam, courses=Course.query.filter_by(teacher_id=current_user.id).all())

    @app.post("/exams/<int:exam_id>/delete")
    @role_required("teacher")
    def delete_exam(exam_id):
        exam = db.get_or_404(Exam, exam_id)
        if not owns_exam(exam): abort(403)
        db.session.delete(exam); db.session.commit(); return redirect(url_for("exams"))

    @app.route("/exams/<int:exam_id>/questions")
    @role_required("teacher")
    def question_list(exam_id):
        exam = db.get_or_404(Exam, exam_id)
        if not owns_exam(exam): abort(403)
        return render_template("question_list.html", exam=exam)

    def question_data():
        unit = request.form.get("time_unit", "seconds")
        amount = positive(request.form.get("time_amount"), 60)
        return {"question_text": request.form.get("question_text", "").strip(), "option_a": request.form.get("option_a", "").strip(), "option_b": request.form.get("option_b", "").strip(), "option_c": request.form.get("option_c", "").strip(), "option_d": request.form.get("option_d", "").strip(), "correct_answer": request.form.get("correct_answer", "").lower(), "marks": positive(request.form.get("marks"), 1), "time_limit": amount * 60 if unit == "minutes" else amount}

    def valid_question(data):
        return all(data.get(key) for key in ("question_text", "option_a", "option_b", "option_c", "option_d")) and data["correct_answer"] in "abcd"

    @app.route("/exams/<int:exam_id>/questions/add", methods=["GET", "POST"])
    @role_required("teacher")
    def add_question(exam_id):
        exam = db.get_or_404(Exam, exam_id)
        if not owns_exam(exam): abort(403)
        if request.method == "POST":
            data = question_data()
            if valid_question(data):
                db.session.add(Question(exam_id=exam.id, created_by=current_user.id, **data)); db.session.flush(); exam.refresh_total_marks(); db.session.commit(); return redirect(url_for("question_list", exam_id=exam.id))
            flash("Complete every question field.", "danger")
        return render_template("add_question.html", exam=exam, question=None)

    @app.route("/questions/<int:question_id>/edit", methods=["GET", "POST"])
    @role_required("teacher")
    def edit_question(question_id):
        question = db.get_or_404(Question, question_id)
        if question.created_by != current_user.id: abort(403)
        if request.method == "POST":
            data = question_data()
            if valid_question(data):
                for key, value in data.items(): setattr(question, key, value)
                question.exam.refresh_total_marks(); db.session.commit(); return redirect(url_for("question_list", exam_id=question.exam_id))
            flash("Complete every question field.", "danger")
        return render_template("edit_question.html", exam=question.exam, question=question)

    @app.post("/questions/<int:question_id>/delete")
    @role_required("teacher")
    def delete_question(question_id):
        question = db.get_or_404(Question, question_id)
        if question.created_by != current_user.id: abort(403)
        exam = question.exam; db.session.delete(question); db.session.flush(); exam.refresh_total_marks(); db.session.commit(); return redirect(url_for("question_list", exam_id=exam.id))

    @app.route("/question-bank")
    @role_required("teacher")
    def question_bank():
        query = Question.query.join(Exam).join(Course)
        search = request.args.get("q", "").strip()
        if search: query = query.filter(Question.question_text.ilike(f"%{search}%"))
        if request.args.get("teacher_id", type=int): query = query.filter(Question.created_by == request.args["teacher_id"])
        return render_template("question_bank.html", questions=query.order_by(Question.created_at.desc()).all(), teachers=User.query.filter_by(role="teacher").all())

    @app.route("/exams/<int:exam_id>/take", methods=["GET", "POST"])
    @role_required("student")
    def take_exam(exam_id):
        exam = db.get_or_404(Exam, exam_id)
        if not Enrollment.query.filter_by(student_id=current_user.id, course_id=exam.course_id).first(): abort(403)
        if Result.query.filter_by(student_id=current_user.id, exam_id=exam.id).first(): return redirect(url_for("my_results"))
        if not exam.is_active or not exam.questions: flash("This exam is not available.", "warning"); return redirect(url_for("student_dashboard"))
        if request.method == "GET": session[f"exam_started_{exam.id}"] = datetime.utcnow().timestamp()
        started = session.get(f"exam_started_{exam.id}", datetime.utcnow().timestamp())
        if request.method == "POST":
            if datetime.utcnow().timestamp() - started > exam.duration * 60 + 10: flash("The exam time expired.", "warning")
            score = sum(q.marks for q in exam.questions if request.form.get(f"question_{q.id}") == q.correct_answer)
            result = Result(student_id=current_user.id, exam_id=exam.id, score=score, total_marks=exam.total_marks, percentage=(score / exam.total_marks * 100) if exam.total_marks else 0)
            db.session.add(result); db.session.commit(); session.pop(f"exam_started_{exam.id}", None); return redirect(url_for("exam_result", result_id=result.id))
        return render_template("take_exam.html", exam=exam, started=started)

    @app.route("/results")
    @role_required("student")
    def my_results(): return render_template("my_results.html", results=Result.query.filter_by(student_id=current_user.id).order_by(Result.submitted_at.desc()).all())

    @app.route("/results/<int:result_id>")
    @login_required
    def exam_result(result_id):
        result = db.get_or_404(Result, result_id)
        if result.student_id != current_user.id and not (current_user.role == "teacher" and result.exam.teacher_id == current_user.id): abort(403)
        return render_template("exam_result.html", result=result)

    @app.route("/teacher/results")
    @role_required("teacher")
    def teacher_results(): return render_template("my_results.html", results=Result.query.join(Exam).filter(Exam.teacher_id == current_user.id).all())

    @app.route("/leaderboard")
    @login_required
    def leaderboard():
        courses_list = Course.query.all() if current_user.role == "teacher" else [e.course for e in current_user.enrollments]
        selected = db.session.get(Course, request.args.get("course_id", type=int)) if request.args.get("course_id", type=int) else (courses_list[0] if courses_list else None)
        rows = leaderboard_rows(selected.id) if selected else []
        return render_template("teacher_leaderboard.html" if current_user.role == "teacher" else "student_leaderboard.html", courses=courses_list, selected=selected, rows=rows)

    def leaderboard_rows(course_id):
        return db.session.query(User, func.sum(Result.score).label("score"), func.sum(Result.total_marks).label("total"), func.count(Result.id).label("completed"), func.max(Result.submitted_at).label("latest")).join(Result).join(Exam).filter(Exam.course_id == course_id, User.role == "student").group_by(User.id).order_by(func.sum(Result.score).desc()).all()

    @app.route("/analytics")
    @role_required("teacher")
    def analytics():
        results = Result.query.join(Exam).filter(Exam.teacher_id == current_user.id).all()
        average = sum(r.percentage for r in results) / len(results) if results else 0
        return render_template("analytics.html", results=results, average=average, highest=max((r.percentage for r in results), default=0), lowest=min((r.percentage for r in results), default=0))

    @app.route("/notifications")
    @login_required
    def notifications(): return render_template("notifications.html")

    @app.errorhandler(403)
    def forbidden(_error): return render_template("404.html", message="You do not have permission to view this page."), 403
    @app.errorhandler(404)
    def not_found(_error): return render_template("404.html"), 404
    @app.errorhandler(500)
    def server_error(_error): db.session.rollback(); return render_template("500.html"), 500
    return app


def _prepare_database():
    inspector = db.inspect(db.engine)
    if "user" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("user")}
    if "first_name" in columns and "student_id" in columns and "teacher_id" in columns:
        return

    with db.engine.begin() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        rows = connection.exec_driver_sql(
            "SELECT id, full_name, username, password_hash, role, avatar, created_at FROM user ORDER BY id"
        ).mappings().all()
        connection.exec_driver_sql(
            """CREATE TABLE user_new (
                id INTEGER NOT NULL PRIMARY KEY,
                student_id VARCHAR(20),
                teacher_id VARCHAR(20),
                first_name VARCHAR(80) NOT NULL,
                last_name VARCHAR(80) NOT NULL,
                username VARCHAR(80) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL,
                avatar VARCHAR(255),
                created_at DATETIME NOT NULL,
                CONSTRAINT uq_user_student_id UNIQUE (student_id),
                CONSTRAINT uq_user_teacher_id UNIQUE (teacher_id)
            )"""
        )
        student_number = 0
        teacher_number = 0
        for row in rows:
            parts = (row["full_name"] or "User").strip().split()
            first_name = parts[0] if parts else "User"
            last_name = " ".join(parts[1:]) if len(parts) > 1 else "User"
            student_id = None
            teacher_id = None
            if row["role"] == "student":
                student_number += 1
                student_id = f"STU{student_number:04d}"
            elif row["role"] == "teacher":
                teacher_number += 1
                teacher_id = f"TCH{teacher_number:04d}"
            connection.exec_driver_sql(
                "INSERT INTO user_new (id, student_id, teacher_id, first_name, last_name, username, password_hash, role, avatar, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (row["id"], student_id, teacher_id, first_name, last_name, row["username"], row["password_hash"], row["role"], row["avatar"], row["created_at"]),
            )
        connection.exec_driver_sql("DROP TABLE user")
        connection.exec_driver_sql("ALTER TABLE user_new RENAME TO user")
        connection.exec_driver_sql("CREATE INDEX ix_user_username ON user (username)")
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
