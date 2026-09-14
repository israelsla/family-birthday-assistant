from app.db import get_db
from app.hebrew_calendar import days_until, today as hebrew_today

HEBREW_MONTHS = [
    "תשרי", "חשוון", "כסלו", "טבת", "שבט",
    "אדר", "אדר א׳", "אדר ב׳",
    "ניסן", "אייר", "סיון", "תמוז", "אב", "אלול",
]

UPCOMING_WINDOW_DAYS = 14


def get_all_members():
    """Return every family member, active and inactive, oldest (highest age) first."""
    db = get_db()
    return db.execute(
        "SELECT * FROM family_members ORDER BY hebrew_year IS NULL, hebrew_year ASC"
    ).fetchall()


def get_member(member_id):
    """Return a single family member by id, or None if not found."""
    db = get_db()
    return db.execute(
        "SELECT * FROM family_members WHERE id = ?", (member_id,)
    ).fetchone()


def count_active_members():
    """Return how many family members are currently active."""
    db = get_db()
    row = db.execute(
        "SELECT COUNT(*) AS count FROM family_members WHERE active = 1"
    ).fetchone()
    return row["count"]


def create_member(name, hebrew_day, hebrew_month, hebrew_year, phone):
    db = get_db()
    db.execute(
        """
        INSERT INTO family_members (name, hebrew_day, hebrew_month, hebrew_year, phone, active)
        VALUES (?, ?, ?, ?, ?, 1)
        """,
        (name, hebrew_day, hebrew_month, hebrew_year, phone),
    )
    db.commit()


def update_member(member_id, name, hebrew_day, hebrew_month, hebrew_year, phone, active):
    db = get_db()
    db.execute(
        """
        UPDATE family_members
        SET name = ?, hebrew_day = ?, hebrew_month = ?, hebrew_year = ?, phone = ?, active = ?
        WHERE id = ?
        """,
        (name, hebrew_day, hebrew_month, hebrew_year, phone, active, member_id),
    )
    db.commit()


def deactivate_member(member_id):
    db = get_db()
    db.execute("UPDATE family_members SET active = 0 WHERE id = ?", (member_id,))
    db.commit()


def get_active_members():
    db = get_db()
    return db.execute(
        "SELECT * FROM family_members WHERE active = 1 ORDER BY name"
    ).fetchall()


def get_birthday_summary(within_days=UPCOMING_WINDOW_DAYS):
    """Split active members into who has a Hebrew birthday today vs within the next N days."""
    today_list = []
    upcoming_list = []

    for member in get_active_members():
        days = days_until(member["hebrew_day"], member["hebrew_month"])
        if days == 0:
            today_list.append(member)
        elif days <= within_days:
            upcoming_list.append((member, days))

    upcoming_list.sort(key=lambda pair: pair[1])
    return today_list, upcoming_list


def today_hebrew_string():
    return hebrew_today().hebrew_date_string()
