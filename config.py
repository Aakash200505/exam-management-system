import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def _database_uri():
    """Return a local SQLite URI unless a local SQLite URI is explicitly set."""
    database_url = os.environ.get("DATABASE_URL")
    if database_url and database_url.startswith("sqlite:///"):
        path = database_url.removeprefix("sqlite:///")
        db_path = Path(path) if os.path.isabs(path) else BASE_DIR / path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return "sqlite:///" + db_path.as_posix()
    return "sqlite:///" + (BASE_DIR / "instance" / "app.db").as_posix()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "local-development-change-me"
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
