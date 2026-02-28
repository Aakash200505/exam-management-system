from app import create_app, db
from models import User, Course, Exam, Result, Question

app = create_app()

def verify_enrollment_restore():
    with app.app_context():
        print("Starting Verification...")
        
        # Setup Data
        student = User.query.filter_by(username='student_test_revert').first()
        if not student:
            student = User(username='student_test_revert', email='student_revert@example.com', role='student')
            student.set_password('password')
            db.session.add(student)
            
        teacher = User.query.filter_by(username='teacher_test').first()
        if not teacher:
            teacher = User(username='teacher_test', email='teacher_test@example.com', role='teacher')
            teacher.set_password('password')
            db.session.add(teacher)
            
        db.session.commit()
        
        # Create a course and exam (not enrolled)
        course = Course.query.filter_by(name='Restricted Access Course').first()
        if course:
            db.session.delete(course)
        
        course = Course(name='Restricted Access Course', description='Test Course', teacher_id=teacher.id)
        db.session.add(course)
        db.session.commit()
        
        exam = Exam(title='Restricted Exam', course_id=course.id, duration_minutes=30)
        db.session.add(exam)
        db.session.commit()
        
        client = app.test_client()
        client.post('/auth/login', data={'username': 'student_test_revert', 'password': 'password', 'role': 'student'})
        
        # Verify 1: Try to start Exam WITHOUT enrollment
        print("Verifying Exam Start (Without Enrollment)...")
        response = client.get(f'/taking/start/{exam.id}', follow_redirects=True)
        if b'You are not enrolled in this course' in response.data:
            print("[PASS] Access denied as expected.")
        else:
            print("[FAIL] Access allowed without enrollment.")
            
        # Verify 2: Enroll
        print("Enrolling...")
        client.get(f'/course/enroll/{course.id}', follow_redirects=True)
        
        # Verify 3: Try to start Exam WITH enrollment
        print("Verifying Exam Start (With Enrollment)...")
        response = client.get(f'/taking/start/{exam.id}')
        if response.status_code == 200 and b'Restricted Exam' in response.data:
             print("[PASS] Access allowed after enrollment.")
        else:
             print(f"[FAIL] Access failed after enrollment. Status: {response.status_code}")
             
        # Cleanup
        db.session.delete(course)
        db.session.delete(student)
        db.session.commit()
        print("Verification Complete.")

if __name__ == '__main__':
    verify_enrollment_restore()
