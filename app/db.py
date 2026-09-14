import sqlite3
from pathlib import Path

from flask import current_app, g

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema.sql"


def get_db():
    """Return a SQLite connection for the current request, creating it on first use."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(exception=None):
    """Close the request's SQLite connection, if one was opened."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    """Create the database file and tables if they don't already exist."""
    db_path = Path(app.config["DATABASE_PATH"])
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    with open(SCHEMA_PATH, encoding="utf-8") as schema_file:
        conn.executescript(schema_file.read())
    conn.close()


def register_db(app):
    """Wire the database into the Flask app: init on startup, close after each request."""
    app.teardown_appcontext(close_db)
    init_db(app)
