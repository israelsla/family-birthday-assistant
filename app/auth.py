"""Login, signup, and logout. This blueprint is deliberately the only part
of the site reachable without being logged in - see routes.py's
before_request, which guards everything in the `main` blueprint.
"""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from app import models

bp = Blueprint("auth", __name__)


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    """Public self-signup is closed - new families are created by the site
    owner via tools/create_family.py. This route just explains that."""
    flash("ההרשמה העצמאית סגורה כרגע. לבקשת משפחה חדשה, פנה למנהל המערכת.", "error")
    return redirect(url_for("auth.login"))


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
