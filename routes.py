from flask import render_template, redirect, url_for, flash, request
from . import taking_bp
from models import Exam, Question, Result, db
from flask_login import login_required, current_user
from datetime import datetime

@taking_bp.route('/')
@login_required
def index():
    if current_user.role != 'student':
        flash('Only students can take exams', 'warning')
        return redirect(url_for('dashboard.index'))
    
    # Get exams for courses the student is enrolled in
    # This requires more complex query or filtering in python
    enrolled_courses = current_user.enrolled_courses
    available_exams = []
    for course in enrolled_courses:
        for exam in course.exams:
            # Check if already taken
            existing_result = Result.query.filter_by(student_id=current_user.id, exam_id=exam.id).first()
            if not existing_result:
                available_exams.append(exam)
                
    return render_template('taking/index.html', exams=available_exams)

@taking_bp.route('/start/<int:exam_id>')
@login_required
def start_exam(exam_id):
    if current_user.role != 'student':
        return redirect(url_for('dashboard.index'))
        
    exam = Exam.query.get_or_404(exam_id)
    # Check eligibility again
    if exam.course not in current_user.enrolled_courses:
        flash('You are not enrolled in this course', 'danger')
        return redirect(url_for('taking.index'))
        
    existing_result = Result.query.filter_by(student_id=current_user.id, exam_id=exam.id).first()
    if existing_result:
        flash('You have already taken this exam', 'warning')
        return redirect(url_for('result.index'))
        
    return render_template('taking/exam.html', exam=exam)

@taking_bp.route('/submit/<int:exam_id>', methods=['POST'])
@login_required
def submit_exam(exam_id):
    if current_user.role != 'student':
        return redirect(url_for('dashboard.index'))
        
    exam = Exam.query.get_or_404(exam_id)
    questions = exam.questions.all()
    score = 0
    total_marks = 0
    
    for q in questions:
        selected_option = request.form.get(f'question_{q.id}')
        if selected_option == q.correct_option:
            score += q.marks
        total_marks += q.marks
        
    # Save Result
    result = Result(
        student_id=current_user.id,
        exam_id=exam.id,
        score=score,
        total_marks=total_marks,
        date_taken=datetime.utcnow()
    )
    db.session.add(result)
    db.session.commit()
    
    flash(f'Exam submitted! You scored {score}/{total_marks}', 'success')
    return redirect(url_for('result.index'))
