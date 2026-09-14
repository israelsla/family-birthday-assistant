import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
    app.config["DATABASE_PATH"] = os.environ.get(
        "DATABASE_PATH", str(BASE_DIR / "instance" / "family.db")
    )

    from app.db import register_db
    register_db(app)

    from app.hebrew_numerals import format_hebrew_day, format_hebrew_year
    app.jinja_env.filters["hebrew_day"] = format_hebrew_day
    app.jinja_env.filters["hebrew_year"] = format_hebrew_year

    from app.routes import bp
    app.register_blueprint(bp)

    return app
