from app import create_app, db
from models import User, Course, Exam, Question

app = create_app()

def verify_delete_question():
    with app.app_context():
        print("Starting Verification...")
        
        # Setup Data
        teacher = User.query.filter_by(username='teacher_test').first()
        if not teacher:
            teacher = User(username='teacher_test', email='teacher_test@example.com', role='teacher')
            teacher.set_password('password')
            db.session.add(teacher)
            
        db.session.commit()
        
        course = Course(name='Question Bank Course', description='Test Course', teacher_id=teacher.id)
        db.session.add(course)
        db.session.commit()
        
        exam = Exam(title='Question Bank Exam', course_id=course.id, duration_minutes=30)
        db.session.add(exam)
        db.session.commit()
        
        question = Question(exam_id=exam.id, text='Question to Delete', option_a='A', option_b='B', option_c='C', option_d='D', correct_option='A', marks=5)
        db.session.add(question)
        db.session.commit()
        
        question_id = question.id
        print(f"Created question with ID: {question_id}")
        
        client = app.test_client()
        client.post('/auth/login', data={'username': 'teacher_test', 'password': 'password', 'role': 'teacher'})
        
        # Verify Delete
        print("Deleting Question...")
        response = client.post(f'/exam/question/delete/{question_id}', follow_redirects=True)
        
        if b'Question deleted successfully!' in response.data:
            print("[PASS] Flash message confirmed.")
        else:
             print("[FAIL] Flash message missing.")
             
        deleted_q = Question.query.get(question_id)
        if deleted_q is None:
            print("[PASS] Question successfully removed from database.")
        else:
            print("[FAIL] Question still exists in database.")
            
        # Cleanup
        db.session.delete(exam)
        db.session.delete(course)
        db.session.commit()
        print("Verification Complete.")

if __name__ == '__main__':
    verify_delete_question()
