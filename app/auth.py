"""Login, signup, and logout. This blueprint is deliberately the only part
of the site reachable without being logged in - see routes.py's
before_request, which guards everything in the `main` blueprint.
"""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app import models

bp = Blueprint("auth", __name__)

MIN_PASSWORD_LENGTH = 8


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        family_name = request.form.get("family_name", "").strip() or "המשפחה שלי"
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        error = None
        if not email:
            error = "נא למלא אימייל"
        elif len(password) < MIN_PASSWORD_LENGTH:
            error = f"הסיסמה חייבת להיות באורך {MIN_PASSWORD_LENGTH} תווים לפחות"
        elif password != password_confirm:
            error = "הסיסמאות לא תואמות"
        elif models.get_user_by_email(email) is not None:
            error = "כבר קיים משתמש עם האימייל הזה"

        if error:
            flash(error, "error")
            return render_template("signup.html", family_name=family_name, email=email)

        family_id = models.create_family_with_user(family_name, email, generate_password_hash(password))
        user = models.get_user_by_email(email)
        session["user_id"] = user["id"]
        session["family_id"] = family_id
        flash(f"ברוכים הבאים, {family_name}!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("signup.html", family_name="", email="")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = models.get_user_by_email(email)
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("אימייל או סיסמה שגויים", "error")
            return render_template("login.html", email=email)

        session["user_id"] = user["id"]
        session["family_id"] = user["family_id"]
        return redirect(url_for("main.dashboard"))

    return render_template("login.html", email="")


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("התנתקת בהצלחה", "success")
    return redirect(url_for("auth.login"))
