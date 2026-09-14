from datetime import date

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


def get_all_marriages():
    """Every couple, joined with both spouses' names."""
    db = get_db()
    return db.execute(
        """
        SELECT m.id, m.spouse1_id, m.spouse2_id, m.hebrew_day, m.hebrew_month, m.hebrew_year,
               s1.name AS spouse1_name, s2.name AS spouse2_name
        FROM marriages m
        JOIN family_members s1 ON s1.id = m.spouse1_id
        JOIN family_members s2 ON s2.id = m.spouse2_id
        """
    ).fetchall()


def get_marriage(marriage_id):
    db = get_db()
    return db.execute(
        """
        SELECT m.id, m.spouse1_id, m.spouse2_id, m.hebrew_day, m.hebrew_month, m.hebrew_year,
               s1.name AS spouse1_name, s2.name AS spouse2_name
        FROM marriages m
        JOIN family_members s1 ON s1.id = m.spouse1_id
        JOIN family_members s2 ON s2.id = m.spouse2_id
        WHERE m.id = ?
        """,
        (marriage_id,),
    ).fetchone()


def update_marriage_date(marriage_id, hebrew_day, hebrew_month, hebrew_year):
    db = get_db()
    db.execute(
        "UPDATE marriages SET hebrew_day = ?, hebrew_month = ?, hebrew_year = ? WHERE id = ?",
        (hebrew_day, hebrew_month, hebrew_year, marriage_id),
    )
    db.commit()


def create_marriage(spouse1_id, spouse2_id, hebrew_day, hebrew_month, hebrew_year):
    db = get_db()
    db.execute(
        """
        INSERT INTO marriages (spouse1_id, spouse2_id, hebrew_day, hebrew_month, hebrew_year)
        VALUES (?, ?, ?, ?, ?)
        """,
        (spouse1_id, spouse2_id, hebrew_day, hebrew_month, hebrew_year),
    )
    db.commit()


def get_anniversaries_by_member_id():
    """Map each member id in a couple to (partner_name, marriage_row) for the members list."""
    result = {}
    for marriage in get_all_marriages():
        result[marriage["spouse1_id"]] = (marriage["spouse2_name"], marriage)
        result[marriage["spouse2_id"]] = (marriage["spouse1_name"], marriage)
    return result


def get_anniversary_summary(within_days=UPCOMING_WINDOW_DAYS):
    """Same idea as get_birthday_summary(), but for couples with a known anniversary date."""
    today_list = []
    upcoming_list = []

    for marriage in get_all_marriages():
        if not marriage["hebrew_day"]:
            continue  # date not filled in yet

        label = f'{marriage["spouse1_name"]} ו{marriage["spouse2_name"]}'
        days = days_until(marriage["hebrew_day"], marriage["hebrew_month"])
        if days == 0:
            today_list.append(label)
        elif days <= within_days:
            upcoming_list.append((label, days))

    upcoming_list.sort(key=lambda pair: pair[1])
    return today_list, upcoming_list


def get_all_family_events():
    db = get_db()
    return db.execute("SELECT * FROM family_events ORDER BY event_date").fetchall()


def get_family_event(event_id):
    db = get_db()
    return db.execute("SELECT * FROM family_events WHERE id = ?", (event_id,)).fetchone()


def create_family_event(title, event_date, description):
    db = get_db()
    db.execute(
        "INSERT INTO family_events (title, event_date, description) VALUES (?, ?, ?)",
        (title, event_date, description),
    )
    db.commit()


def update_family_event(event_id, title, event_date, description):
    db = get_db()
    db.execute(
        "UPDATE family_events SET title = ?, event_date = ?, description = ? WHERE id = ?",
        (title, event_date, description, event_id),
    )
    db.commit()


def delete_family_event(event_id):
    db = get_db()
    db.execute("DELETE FROM family_events WHERE id = ?", (event_id,))
    db.commit()


def get_upcoming_family_events():
    """Custom events (Bar Mitzvah, wedding, a gathering...) from today onward, soonest first."""
    today_iso = date.today().isoformat()
    db = get_db()
    events = db.execute(
        "SELECT * FROM family_events WHERE event_date >= ? ORDER BY event_date", (today_iso,)
    ).fetchall()

    result = []
    for event in events:
        days = (date.fromisoformat(event["event_date"]) - date.today()).days
        result.append((event, days))
    return result
