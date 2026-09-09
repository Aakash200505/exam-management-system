from datetime import datetime

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db
from models import Exam, Result
from . import taking_bp


def _student_exam_or_redirect(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if exam.course not in current_user.enrolled_courses:
        flash("You are not enrolled in this course", "danger")
        return exam, redirect(url_for("taking.index"))
    return exam, None


@taking_bp.route("/")
@login_required
def index():
    if current_user.role != "student":
        flash("Only students can take exams", "warning")
        return redirect(url_for("dashboard.index"))
    available = []
    for course in current_user.enrolled_courses:
        for exam in course.exams:
            if not Result.query.filter_by(student_id=current_user.id, exam_id=exam.id).first():
                available.append(exam)
    return render_template("taking/index.html", exams=available)


@taking_bp.route("/start/<int:exam_id>")
@login_required
def start_exam(exam_id):
    if current_user.role != "student":
        return redirect(url_for("dashboard.index"))
    exam, denied = _student_exam_or_redirect(exam_id)
    if denied:
        return denied
    if Result.query.filter_by(student_id=current_user.id, exam_id=exam.id).first():
        flash("You have already taken this exam", "warning")
        return redirect(url_for("result.index"))
    return render_template("taking/exam.html", exam=exam)


@taking_bp.route("/submit/<int:exam_id>", methods=["POST"])
@login_required
def submit_exam(exam_id):
    if current_user.role != "student":
        return redirect(url_for("dashboard.index"))
    exam, denied = _student_exam_or_redirect(exam_id)
    if denied:
        return denied
    if Result.query.filter_by(student_id=current_user.id, exam_id=exam.id).first():
        flash("You have already taken this exam", "warning")
        return redirect(url_for("result.index"))
    questions = exam.questions.all()
    score = sum(question.marks for question in questions if request.form.get(f"question_{question.id}") == question.correct_option)
    total_marks = sum(question.marks for question in questions)
    db.session.add(Result(student_id=current_user.id, exam_id=exam.id, score=score, total_marks=total_marks, date_taken=datetime.utcnow()))
    db.session.commit()
    flash(f"Exam submitted! You scored {score}/{total_marks}", "success")
    return redirect(url_for("result.index"))
