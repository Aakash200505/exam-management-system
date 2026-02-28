from app import create_app
from extensions import db
from models import User

app = create_app()

def verify_login():
    with app.app_context():
        # Clean up existing test users if they exist
        existing_student = User.query.filter_by(username='student_test').first()
        if existing_student:
            db.session.delete(existing_student)
        
        existing_teacher = User.query.filter_by(username='teacher_test').first()
        if existing_teacher:
            db.session.delete(existing_teacher)
        
        db.session.commit()

        # Create test users
        student = User(username='student_test', email='student_test@example.com', role='student')
        student.set_password('password')
        
        teacher = User(username='teacher_test', email='teacher_test@example.com', role='teacher')
        teacher.set_password('password')
        
        db.session.add(student)
        db.session.add(teacher)
        db.session.commit()
        
        client = app.test_client()
        
        print("Starting verification...")

        # Test 1: Student login with correct role
        response = client.post('/auth/login', data={
            'username': 'student_test',
            'password': 'password',
            'role': 'student'
        }, follow_redirects=True)
        
        if b'Login successful!' in response.data:
            print("[PASS] Student login with correct role successful.")
        else:
            print("[FAIL] Student login with correct role failed.")
            print(response.data)

        # Test 2: Student login with incorrect role
        client.get('/auth/logout') # Logout first
        response = client.post('/auth/login', data={
            'username': 'student_test',
            'password': 'password',
            'role': 'teacher'
        }, follow_redirects=True)
        
        if b'Invalid role selected for this user.' in response.data or b'Login successful!' not in response.data:
             print("[PASS] Student login with incorrect role failed as expected.")
        else:
             print("[FAIL] Student login with incorrect role succeeded unexpectedly.")
        
        # Test 3: Teacher login with correct role
        client.get('/auth/logout')
        response = client.post('/auth/login', data={
            'username': 'teacher_test',
            'password': 'password',
            'role': 'teacher'
        }, follow_redirects=True)
        
        if b'Login successful!' in response.data:
            print("[PASS] Teacher login with correct role successful.")
        else:
            print("[FAIL] Teacher login with correct role failed.")

        # Test 4: Teacher login with incorrect role
        client.get('/auth/logout')
        response = client.post('/auth/login', data={
            'username': 'teacher_test',
            'password': 'password',
            'role': 'student'
        }, follow_redirects=True)
        
        if b'Invalid role selected for this user.' in response.data or b'Login successful!' not in response.data:
             print("[PASS] Teacher login with incorrect role failed as expected.")
        else:
             print("[FAIL] Teacher login with incorrect role succeeded unexpectedly.")

        # Clean up
        db.session.delete(student)
        db.session.delete(teacher)
        db.session.commit()
        print("Verification complete.")

if __name__ == '__main__':
    verify_login()
