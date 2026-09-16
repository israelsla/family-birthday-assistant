"""Login, signup, and logout. This blueprint is deliberately the only part
of the site reachable without being logged in - see routes.py's
before_request, which guards everything in the `main` blueprint.
"""
import time
from collections import defaultdict

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app import models

bp = Blueprint("auth", __name__)

MIN_PASSWORD_LENGTH = 8

# Lightweight anti-spam for the public signup form: no external service, no
# new dependency. Not a real security boundary (an attacker who controls
# many IPs can get around it) - just enough friction to stop a naive bot
# hammering the form. Resets whenever the process restarts, which is fine
# for this scale.
RATE_LIMIT_WINDOW_SECONDS = 3600
RATE_LIMIT_MAX_SIGNUPS_PER_IP = 3
_recent_signup_attempts = defaultdict(list)


def _is_rate_limited(ip):
    now = time.time()
    attempts = _recent_signup_attempts[ip]
    attempts[:] = [t for t in attempts if now - t < RATE_LIMIT_WINDOW_SECONDS]
    if len(attempts) >= RATE_LIMIT_MAX_SIGNUPS_PER_IP:
        return True
    attempts.append(now)
    return False


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        # honeypot: a field hidden from real users via CSS. A filled-in value
        # means a bot filled every field it found - pretend it worked so the
        # bot doesn't learn to look for this specific trick, but create nothing.
        if request.form.get("website"):
            flash("ברוכים הבאים!", "success")
            return redirect(url_for("main.dashboard"))

        if _is_rate_limited(request.remote_addr):
            flash("יותר מדי נסיונות הרשמה. נסה שוב בעוד שעה.", "error")
            return render_template("signup.html", family_name="", email="")

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
