from app import create_app, db
from models import User, Course, Exam, Question

app = create_app()

def reproduce_error():
    with app.app_context():
        print("--- Testing question deletion logic ---")
        q = Question.query.first()
        if not q:
            print("No questions found. Creating one...")
            # Need a course and exam first
            c = Course.query.first()
            if not c:
                u = User.query.first()
                c = Course(name="Test Course", teacher_id=u.id if u else None)
                db.session.add(c)
                db.session.commit()
            e = Exam.query.first()
            if not e:
                e = Exam(title="Test Exam", course_id=c.id)
                db.session.add(e)
                db.session.commit()
            q = Question(text="Test Q", exam_id=e.id)
            db.session.add(q)
            db.session.commit()
        
        print(f"Testing Question ID: {q.id}")
        print(f"Question object: {q}")
        
        try:
            print(f"Accessing q.exam: {q.exam}")
            print(f"Type of q.exam: {type(q.exam)}")
            exam = q.exam
            if exam:
                print(f"Accessing exam.id: {exam.id}")
                print(f"Accessing exam.course: {exam.course}")
                print(f"Type of exam.course: {type(exam.course)}")
                if exam.course:
                    if hasattr(exam.course, 'teacher_id'):
                        print(f"Accessing exam.course.teacher_id: {exam.course.teacher_id}")
                    else:
                        print("exam.course has NO teacher_id attribute!")
                        # List attributes of exam.course
                        print(f"Attributes of exam.course: {dir(exam.course)}")
                else:
                    print("exam.course is None")
            else:
                print("q.exam is None")
        except Exception as e:
            print(f"Caught exception: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()



if __name__ == '__main__':
    reproduce_error()
