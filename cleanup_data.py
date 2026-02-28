from app import create_app, db
from models import Course, Exam, Question, Result

app = create_app()

def cleanup_data():
    with app.app_context():
        print("Starting cleanup...")
        
        # Find courses with 'Open Access' in name
        courses = Course.query.filter(Course.name.like('%Open Access%')).all()
        for course in courses:
            print(f"Deleting course: {course.name}")
            # Delete related exams and questions (cascade might handle this, but let's be safe)
            for exam in course.exams:
                Question.query.filter_by(exam_id=exam.id).delete()
                Result.query.filter_by(exam_id=exam.id).delete()
                db.session.delete(exam)
            
            # Delete enrollments (handled by association table, but explicit is good if needed, though db.relationship usually handles it)
            # course.students = [] 
            
            db.session.delete(course)
            
        # Also check for 'Restricted Access Course' from restore verification
        restricted_courses = Course.query.filter(Course.name.like('%Restricted Access%')).all()
        for course in restricted_courses:
             print(f"Deleting course: {course.name}")
             for exam in course.exams:
                Question.query.filter_by(exam_id=exam.id).delete()
                Result.query.filter_by(exam_id=exam.id).delete()
                db.session.delete(exam)
             db.session.delete(course)

        db.session.commit()
        print("Cleanup complete.")

if __name__ == '__main__':
    cleanup_data()
