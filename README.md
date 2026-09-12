# Examora Online Exam Platform

Examora is a Flask online examination platform with exactly two account roles: `teacher` and `student`.

## Features

- Username and password login with role verification
- Separate permanent IDs: `STU0001` for students and `TCH0001` for teachers
- Duplicate usernames are allowed; login resolves accounts by username, role, and password
- Strong password validation and secure Werkzeug hashes
- Teacher-owned courses, exams, and questions
- Student course enrollment with a separate confirmation email address
- Optional SMTP enrollment confirmations using environment variables
- Per-question timers stored in seconds and an overall exam timer
- One result per student per exam, with historical scores preserved
- Student course leaderboards and teacher analytics
- Shared read-only teacher question bank with ownership enforcement
- Avatar upload validation for PNG, JPG, JPEG, and WEBP
- Profile editing, username changes, and password changes
- Responsive Bootstrap-backed interface

## Structure

```text
app.py              Application factory and routes
models.py           User, Course, Enrollment, Exam, Question, Result
extensions.py       SQLAlchemy, Login Manager, and Migrate instances
config.py           Environment-based configuration
instance/exam.db   Local SQLite database
uploads/avatars/   Uploaded profile images
templates/          All page templates
static/             CSS, JavaScript, and default avatar
```

There is no `aak`, `project`, or `modules` package. The only application entry point is `app.py`.

## Local installation

Python 3.12 is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

The instance directory, upload directory, tables, and database are created automatically. Existing database data is not deleted. A legacy database is renamed internally to legacy tables once so the new schema can initialize without destructive cleanup.

## Accounts and login

Register as either a Teacher or Student. Login requires:

- Username
- Password
- Selected role

A role mismatch returns the generic message `Invalid username, password, or role.` Email is not used for login.

Registration collects first name, last name, username, password, confirmation, and role. Usernames are intentionally not globally unique. Each student receives a permanent `STU####` ID and each teacher receives a permanent `TCH####` ID. IDs are database-backed and are never editable from a profile.

Passwords must be at least 10 characters and include uppercase, lowercase, a number, and a special character. Example: `Abcd@12345`.

## Teacher workflow

Teachers can create and edit their own courses and exams, publish or unpublish exams, add timed MCQ questions, update question marks and answers after publishing, view student results, open analytics, and view the shared question bank. A teacher can edit or delete only questions that teacher created. Other teachers' questions are read-only.

## Student workflow

Students browse courses, open a course, enroll with a valid email address, and take available exams. Enrollment stores the supplied email separately from the login username. Students can view their own results and leaderboards for enrolled courses.

Each question has a teacher-defined timer in seconds or minutes. The exam also has an overall timer. JavaScript displays both timers, while the server records the exam start and rejects submissions that arrive materially after the overall deadline.

## Enrollment email configuration

Email delivery is optional during local development. Enrollment always records successfully when SMTP is unavailable and displays a clear notice.

Configure SMTP with environment variables; never put credentials in source code:

```text
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=your-user
MAIL_PASSWORD=your-password
MAIL_USE_TLS=true
MAIL_DEFAULT_SENDER=no-reply@example.com
```

`SECRET_KEY` and `DATABASE_URL` are also supported environment variables. SQLite is used by default.

## Render deployment

Push the repository to GitHub and create a Render Web Service with an empty Root Directory. `render.yaml` installs dependencies and uses:

```text
gunicorn app:app
```

Render generates `SECRET_KEY`. SQLite is appropriate for demos and small deployments; use a managed database through `DATABASE_URL` for persistent production data.

## Verification

```powershell
python -m compileall .
python -c "from app import app; print(app)"
gunicorn --version
gunicorn app:app
```

Gunicorn is a Unix production server. On Windows, use `python app.py` locally; Render runs `gunicorn app:app` on Linux.

## Troubleshooting

- **Import errors:** Run commands from the repository root.
- **Weak password:** Use 10 or more characters with all required character classes.
- **Enrollment email notice:** SMTP variables are missing or the SMTP server is unavailable; enrollment is still saved.
- **Upload rejected:** Use a real PNG, JPG, JPEG, or WEBP image under 2 MB.
- **Port in use:** Run `flask --app app run --port 5001`.
