from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app import hebrew_calendar, models

bp = Blueprint("main", __name__)


@bp.before_request
def require_login():
    """Every route in this blueprint requires a logged-in session. auth.py's
    routes (/login, /signup, /logout) live in a separate blueprint and are
    the only pages reachable without one."""
    if "user_id" not in session:
        return redirect(url_for("auth.login"))


def _parse_member_form(form):
    """Pull and lightly validate the fields shared by the add/edit forms."""
    name = form.get("name", "").strip()
    hebrew_month = form.get("hebrew_month", "")
    phone = form.get("phone", "").strip() or None

    try:
        hebrew_day = int(form.get("hebrew_day", ""))
    except ValueError:
        hebrew_day = None

    hebrew_year_raw = form.get("hebrew_year", "").strip()
    hebrew_year = int(hebrew_year_raw) if hebrew_year_raw.isdigit() else None

    is_valid = (
        bool(name)
        and hebrew_month in models.HEBREW_MONTHS
        and hebrew_day is not None
        and 1 <= hebrew_day <= 30
    )

    return {
        "name": name,
        "hebrew_day": hebrew_day,
        "hebrew_month": hebrew_month,
        "hebrew_year": hebrew_year,
        "phone": phone,
        "is_valid": is_valid,
    }


@bp.route("/")
def dashboard():
    active_count = models.count_active_members()
    todays_birthdays, upcoming_birthdays = models.get_birthday_summary()
    todays_anniversaries, upcoming_anniversaries = models.get_anniversary_summary()
    upcoming_custom_events = models.get_upcoming_family_events()

    family_events = sorted(
        [{"icon": "💍", "label": label, "days": days, "custom_id": None} for label, days in upcoming_anniversaries]
        + [
            {"icon": "🎊", "label": event["title"], "days": days, "custom_id": event["id"]}
            for event, days in upcoming_custom_events
        ],
        key=lambda event: event["days"],
    )

    return render_template(
        "dashboard.html",
        active_count=active_count,
        today_hebrew_date=models.today_hebrew_string(),
        todays_birthdays=todays_birthdays,
        upcoming_birthdays=upcoming_birthdays,
        todays_anniversaries=todays_anniversaries,
        family_events=family_events,
    )


@bp.route("/members")
def members_list():
    anniversaries = models.get_anniversaries_by_member_id()

    members_with_age = []
    for member in models.get_all_members():
        age = None
        if member["hebrew_year"]:
            age = hebrew_calendar.age_in_years(
                member["hebrew_day"], member["hebrew_month"], member["hebrew_year"]
            )
        members_with_age.append((member, age, anniversaries.get(member["id"])))

    return render_template("members_list.html", members=members_with_age)


@bp.route("/members/add", methods=["GET", "POST"])
def add_member():
    if request.method == "POST":
        data = _parse_member_form(request.form)
        if not data["is_valid"]:
            flash("נא למלא שם, יום עברי תקין (1-30) וחודש עברי", "error")
            return render_template(
                "member_form.html",
                member=data,
                hebrew_months=models.HEBREW_MONTHS,
                mode="add",
            )

        models.create_member(
            data["name"], data["hebrew_day"], data["hebrew_month"],
            data["hebrew_year"], data["phone"],
        )
        flash(f'{data["name"]} נוסף/ה בהצלחה', "success")
        return redirect(url_for("main.members_list"))

    return render_template(
        "member_form.html", member=None, hebrew_months=models.HEBREW_MONTHS, mode="add"
    )


@bp.route("/members/<int:member_id>/edit", methods=["GET", "POST"])
def edit_member(member_id):
    member = models.get_member(member_id)
    if member is None:
        flash("בן המשפחה לא נמצא", "error")
        return redirect(url_for("main.members_list"))

    if request.method == "POST":
        data = _parse_member_form(request.form)
        data["active"] = 1 if request.form.get("active") == "on" else 0

        if not data["is_valid"]:
            flash("נא למלא שם, יום עברי תקין (1-30) וחודש עברי", "error")
            return render_template(
                "member_form.html",
                member=data,
                hebrew_months=models.HEBREW_MONTHS,
                mode="edit",
                member_id=member_id,
            )

        models.update_member(
            member_id, data["name"], data["hebrew_day"], data["hebrew_month"],
            data["hebrew_year"], data["phone"], data["active"],
        )
        flash(f'{data["name"]} עודכן/ה בהצלחה', "success")
        return redirect(url_for("main.members_list"))

    return render_template(
        "member_form.html",
        member=member,
        hebrew_months=models.HEBREW_MONTHS,
        mode="edit",
        member_id=member_id,
    )


@bp.route("/members/<int:member_id>/deactivate", methods=["POST"])
def deactivate_member_route(member_id):
    models.deactivate_member(member_id)
    flash("בן המשפחה הושבת", "success")
    return redirect(url_for("main.members_list"))


@bp.route("/marriages/<int:marriage_id>/edit", methods=["GET", "POST"])
def edit_marriage(marriage_id):
    marriage = models.get_marriage(marriage_id)
    if marriage is None:
        flash("הזוג לא נמצא", "error")
        return redirect(url_for("main.members_list"))

    if request.method == "POST":
        hebrew_month = request.form.get("hebrew_month", "")
        try:
            hebrew_day = int(request.form.get("hebrew_day", ""))
        except ValueError:
            hebrew_day = None
        hebrew_year_raw = request.form.get("hebrew_year", "").strip()
        hebrew_year = int(hebrew_year_raw) if hebrew_year_raw.isdigit() else None

        is_valid = hebrew_month in models.HEBREW_MONTHS and hebrew_day is not None and 1 <= hebrew_day <= 30
        if not is_valid:
            flash("נא למלא יום עברי תקין (1-30) וחודש עברי", "error")
            return render_template(
                "marriage_form.html", marriage=marriage, hebrew_months=models.HEBREW_MONTHS
            )

        models.update_marriage_date(marriage_id, hebrew_day, hebrew_month, hebrew_year)
        flash("תאריך הנישואין עודכן בהצלחה", "success")
        return redirect(url_for("main.members_list"))

    return render_template("marriage_form.html", marriage=marriage, hebrew_months=models.HEBREW_MONTHS)


@bp.route("/marriages/add", methods=["GET", "POST"])
def add_marriage():
    preselected_id = request.args.get("member_id", type=int)
    all_members = models.get_all_members()

    if request.method == "POST":
        try:
            spouse1_id = int(request.form.get("spouse1_id", ""))
            spouse2_id = int(request.form.get("spouse2_id", ""))
        except ValueError:
            spouse1_id = spouse2_id = None

        hebrew_month = request.form.get("hebrew_month", "")
        hebrew_day_raw = request.form.get("hebrew_day", "").strip()
        hebrew_day = int(hebrew_day_raw) if hebrew_day_raw.isdigit() else None
        hebrew_year_raw = request.form.get("hebrew_year", "").strip()
        hebrew_year = int(hebrew_year_raw) if hebrew_year_raw.isdigit() else None

        date_given = hebrew_day is not None or hebrew_month or hebrew_year
        date_valid = not date_given or (
            hebrew_month in models.HEBREW_MONTHS and hebrew_day is not None and 1 <= hebrew_day <= 30
        )

        if not spouse1_id or not spouse2_id or spouse1_id == spouse2_id or not date_valid:
            flash("נא לבחור שני בני משפחה שונים, ואם ממלאים תאריך - שיהיה תקין במלואו", "error")
            return render_template(
                "marriage_add_form.html",
                members=all_members,
                preselected_id=preselected_id,
                hebrew_months=models.HEBREW_MONTHS,
            )

        if not hebrew_month:
            hebrew_month = None

        models.create_marriage(spouse1_id, spouse2_id, hebrew_day, hebrew_month, hebrew_year)
        flash("בן/בת הזוג נוספו בהצלחה", "success")
        return redirect(url_for("main.members_list"))

    return render_template(
        "marriage_add_form.html",
        members=all_members,
        preselected_id=preselected_id,
        hebrew_months=models.HEBREW_MONTHS,
    )


def _parse_event_form(form):
    title = form.get("title", "").strip()
    event_date = form.get("event_date", "").strip()
    description = form.get("description", "").strip() or None
    is_valid = bool(title) and bool(event_date)
    return {"title": title, "event_date": event_date, "description": description, "is_valid": is_valid}


@bp.route("/events/add", methods=["GET", "POST"])
def add_event():
    if request.method == "POST":
        data = _parse_event_form(request.form)
        if not data["is_valid"]:
            flash("נא למלא כותרת ותאריך לאירוע", "error")
            return render_template("event_form.html", event=data, mode="add")

        models.create_family_event(data["title"], data["event_date"], data["description"])
        flash("האירוע נוסף בהצלחה", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("event_form.html", event=None, mode="add")


@bp.route("/events/<int:event_id>/edit", methods=["GET", "POST"])
def edit_event(event_id):
    event = models.get_family_event(event_id)
    if event is None:
        flash("האירוע לא נמצא", "error")
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        data = _parse_event_form(request.form)
        if not data["is_valid"]:
            flash("נא למלא כותרת ותאריך לאירוע", "error")
            return render_template("event_form.html", event=data, mode="edit", event_id=event_id)

        models.update_family_event(event_id, data["title"], data["event_date"], data["description"])
        flash("האירוע עודכן בהצלחה", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("event_form.html", event=event, mode="edit", event_id=event_id)


@bp.route("/events/<int:event_id>/delete", methods=["POST"])
def delete_event(event_id):
    models.delete_family_event(event_id)
    flash("האירוע נמחק", "success")
    return redirect(url_for("main.dashboard"))
