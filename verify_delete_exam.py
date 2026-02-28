from app import create_app, db
from models import User, Course, Exam, Question

app = create_app()

def verify_delete_exam():
    with app.app_context():
        print("Starting Exam Delete Verification...")
        
        # Setup Data
        teacher = User.query.filter_by(username='teacher_test_exam').first()
        if not teacher:
            teacher = User(username='teacher_test_exam', email='teacher_test_exam@example.com', role='teacher')
            teacher.set_password('password')
            db.session.add(teacher)
        db.session.commit()
        
        course = Course(name='Exam Delete Course', description='Test Course', teacher_id=teacher.id)
        db.session.add(course)
        db.session.commit()
        
        exam = Exam(title='Exam to Delete', course_id=course.id, duration_minutes=30)
        db.session.add(exam)
        db.session.commit()
        
        question = Question(exam_id=exam.id, text='Question to be deleted by cascade', option_a='A', option_b='B', option_c='C', option_d='D', correct_option='A', marks=5)
        db.session.add(question)
        db.session.commit()
        
        exam_id = exam.id
        question_id = question.id
        print(f"Created exam with ID: {exam_id} and question with ID: {question_id}")
        
        client = app.test_client()
        client.post('/auth/login', data={'username': 'teacher_test_exam', 'password': 'password', 'role': 'teacher'})
        
        # Verify Delete Exam
        print("Deleting Exam...")
        response = client.post(f'/exam/delete/{exam_id}', follow_redirects=True)
        
        if b'Exam deleted successfully!' in response.data:
            print("[PASS] Flash message confirmed.")
        else:
             print("[FAIL] Flash message missing.")
             
        deleted_exam = Exam.query.get(exam_id)
        if deleted_exam is None:
            print("[PASS] Exam successfully removed from database.")
        else:
            print("[FAIL] Exam still exists in database.")
            
        deleted_question = Question.query.get(question_id)
        if deleted_question is None:
            print("[PASS] Associated question successfully removed by cascade.")
        else:
            print("[FAIL] Question still exists in database (cascade failed).")
            
        # Cleanup
        db.session.delete(course)
        db.session.commit()
        print("Verification Complete.")

if __name__ == '__main__':
    verify_delete_exam()
