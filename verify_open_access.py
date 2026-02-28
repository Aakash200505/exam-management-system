from app import create_app, db
from models import User, Course, Exam, Result, Question

app = create_app()

def verify_open_access():
    with app.app_context():
        print("Starting Verification...")
        
        # Setup Data
        student = User.query.filter_by(username='student_test').first()
        if not student:
            student = User(username='student_test', email='student_test@example.com', role='student')
            student.set_password('password')
            db.session.add(student)
            
        teacher = User.query.filter_by(username='teacher_test').first()
        if not teacher:
            teacher = User(username='teacher_test', email='teacher_test@example.com', role='teacher')
            teacher.set_password('password')
            db.session.add(teacher)
            
        db.session.commit()
        
        # Create a course and exam (not enrolled)
        course = Course.query.filter_by(name='Open Access Course').first()
        if course:
            db.session.delete(course)
        
        course = Course(name='Open Access Course', description='Test Course', teacher_id=teacher.id)
        db.session.add(course)
        db.session.commit()
        
        exam = Exam(title='Open Access Exam', course_id=course.id, duration_minutes=30)
        db.session.add(exam)
        db.session.commit()
        
        question = Question(exam_id=exam.id, text='Q1', option_a='A', option_b='B', option_c='C', option_d='D', correct_option='A', marks=10)
        db.session.add(question)
        db.session.commit()
        
        client = app.test_client()
        client.post('/auth/login', data={'username': 'student_test', 'password': 'password', 'role': 'student'})
        
        # Verify 1: View Course (Open Access)
        print("Verifying Course View Access...")
        response = client.get(f'/course/view/{course.id}')
        if response.status_code == 200 and b'Open Access Exam' in response.data:
            print("[PASS] Course view accessible without enrollment.")
        else:
            print(f"[FAIL] Course view failed. Status: {response.status_code}")
            
        # Verify 2: Take Exam (Open Access)
        print("Verifying Exam Start (Open Access)...")
        response = client.get(f'/taking/start/{exam.id}')
        if response.status_code == 200 and b'Q1' in response.data: # Assuming exam.html shows first question or similar
             print("[PASS] Exam start accessible without enrollment.")
        else:
             print(f"[FAIL] Exam start failed. Status: {response.status_code}")
             
        # Verify 3: Submit Exam and Check Analytics (Admin)
        print("Verifying Exam Submission and Analytics...")
        response = client.post(f'/taking/submit/{exam.id}', data={'question_{}'.format(question.id): 'A'}, follow_redirects=True)
        
        if b'Exam submitted!' in response.data:
            print("[PASS] Exam submitted successfully.")
            
            client.get('/auth/logout')
            # Login as Admin
            # Create admin if not exists
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(username='admin', email='admin@example.com', role='admin')
                admin.set_password('admin')
                db.session.add(admin)
                db.session.commit()
                
            client.post('/auth/login', data={'username': 'admin', 'password': 'admin', 'role': 'admin'})
            response = client.get('/dashboard/')
            
            if b'student_test' in response.data and b'10.0' in response.data: # Average score should be 10.0
                print("[PASS] Admin analytics shows correct student data.")
            else:
                 print("[FAIL] Admin analytics missing or incorrect.")
                 # print(response.data)
        else:
             print("[FAIL] Exam submission failed.")

        # Cleanup
        # db.session.delete(course) # Keep for manual check if needed, or delete
        print("Verification Complete.")

if __name__ == '__main__':
    verify_open_access()
