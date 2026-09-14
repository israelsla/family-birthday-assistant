from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import hebrew_calendar, models

bp = Blueprint("main", __name__)


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

    todays_events = (
        [{"icon": "🎂", "label": member["name"]} for member in todays_birthdays]
        + [{"icon": "💍", "label": label} for label in todays_anniversaries]
    )
    upcoming_events = sorted(
        [{"icon": "🎂", "label": member["name"], "days": days} for member, days in upcoming_birthdays]
        + [{"icon": "💍", "label": label, "days": days} for label, days in upcoming_anniversaries],
        key=lambda event: event["days"],
    )

    return render_template(
        "dashboard.html",
        active_count=active_count,
        today_hebrew_date=models.today_hebrew_string(),
        todays_events=todays_events,
        upcoming_events=upcoming_events,
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
