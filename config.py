import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _database_uri():
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        if database_url.startswith('sqlite:///'):
            db_path = database_url.removeprefix('sqlite:///')
            if not os.path.isabs(db_path):
                db_path = os.path.join(BASE_DIR, db_path)
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            return 'sqlite:///' + db_path.replace('\\', '/')
        return database_url

    return 'sqlite:///' + os.path.join(BASE_DIR, 'app.db').replace('\\', '/')


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
