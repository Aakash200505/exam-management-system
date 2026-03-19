import sys
from pathlib import Path

from flask import Flask, render_template
from config import Config
from extensions import db, login_manager, migrate
from models import User, Result

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from modules.auth import auth_bp
    from modules.dashboard import dashboard_bp
    from modules.course import course_bp
    from modules.exam import exam_bp
    from modules.taking import taking_bp
    from modules.result import result_bp
    from modules.analytics import analytics_bp
    from modules.profile import profile_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(course_bp, url_prefix='/course')
    app.register_blueprint(exam_bp, url_prefix='/exam')
    app.register_blueprint(taking_bp, url_prefix='/taking')
    app.register_blueprint(result_bp, url_prefix='/result')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(profile_bp, url_prefix='/profile')

    @app.route('/')
    def index():
        exams_done = Result.query.count()
        return render_template('index.html', exams_done=exams_done)

    return app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
