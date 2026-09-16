from datetime import date

from app.db import get_db
from app.hebrew_calendar import days_until, today as hebrew_today

HEBREW_MONTHS = [
    "תשרי", "חשוון", "כסלו", "טבת", "שבט",
    "אדר", "אדר א׳", "אדר ב׳",
    "ניסן", "אייר", "סיון", "תמוז", "אב", "אלול",
]

UPCOMING_WINDOW_DAYS = 14


def get_all_members(family_id):
    """Return every family member, active and inactive, oldest (highest age) first."""
    db = get_db()
    return db.execute(
        "SELECT * FROM family_members WHERE family_id = ? ORDER BY hebrew_year IS NULL, hebrew_year ASC",
        (family_id,),
    ).fetchall()


def get_member(member_id, family_id):
    """Return a single family member by id, scoped to this family, or None if not found."""
    db = get_db()
    return db.execute(
        "SELECT * FROM family_members WHERE id = ? AND family_id = ?", (member_id, family_id)
    ).fetchone()


def count_active_members(family_id):
    """Return how many family members are currently active."""
    db = get_db()
    row = db.execute(
        "SELECT COUNT(*) AS count FROM family_members WHERE active = 1 AND family_id = ?", (family_id,)
    ).fetchone()
    return row["count"]


def create_member(family_id, name, hebrew_day, hebrew_month, hebrew_year, phone):
    db = get_db()
    db.execute(
        """
        INSERT INTO family_members (family_id, name, hebrew_day, hebrew_month, hebrew_year, phone, active)
        VALUES (?, ?, ?, ?, ?, ?, 1)
        """,
        (family_id, name, hebrew_day, hebrew_month, hebrew_year, phone),
    )
    db.commit()


def update_member(member_id, family_id, name, hebrew_day, hebrew_month, hebrew_year, phone, active):
    db = get_db()
    db.execute(
        """
        UPDATE family_members
        SET name = ?, hebrew_day = ?, hebrew_month = ?, hebrew_year = ?, phone = ?, active = ?
        WHERE id = ? AND family_id = ?
        """,
        (name, hebrew_day, hebrew_month, hebrew_year, phone, active, member_id, family_id),
    )
    db.commit()


def deactivate_member(member_id, family_id):
    db = get_db()
    db.execute(
        "UPDATE family_members SET active = 0 WHERE id = ? AND family_id = ?", (member_id, family_id)
    )
    db.commit()


def get_active_members(family_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM family_members WHERE active = 1 AND family_id = ? ORDER BY name", (family_id,)
    ).fetchall()


def get_birthday_summary(family_id, within_days=UPCOMING_WINDOW_DAYS):
    """Split active members into who has a Hebrew birthday today vs within the next N days."""
    today_list = []
    upcoming_list = []

    for member in get_active_members(family_id):
        days = days_until(member["hebrew_day"], member["hebrew_month"])
        if days == 0:
            today_list.append(member)
        elif days <= within_days:
            upcoming_list.append((member, days))

    upcoming_list.sort(key=lambda pair: pair[1])
    return today_list, upcoming_list


def today_hebrew_string():
    return hebrew_today().hebrew_date_string()


def get_all_marriages(family_id):
    """Every couple in this family, joined with both spouses' names."""
    db = get_db()
    return db.execute(
        """
        SELECT m.id, m.spouse1_id, m.spouse2_id, m.hebrew_day, m.hebrew_month, m.hebrew_year,
               s1.name AS spouse1_name, s2.name AS spouse2_name
        FROM marriages m
        JOIN family_members s1 ON s1.id = m.spouse1_id
        JOIN family_members s2 ON s2.id = m.spouse2_id
        WHERE m.family_id = ?
        """,
        (family_id,),
    ).fetchall()


def get_marriage(marriage_id, family_id):
    db = get_db()
    return db.execute(
        """
        SELECT m.id, m.spouse1_id, m.spouse2_id, m.hebrew_day, m.hebrew_month, m.hebrew_year,
               s1.name AS spouse1_name, s2.name AS spouse2_name
        FROM marriages m
        JOIN family_members s1 ON s1.id = m.spouse1_id
        JOIN family_members s2 ON s2.id = m.spouse2_id
        WHERE m.id = ? AND m.family_id = ?
        """,
        (marriage_id, family_id),
    ).fetchone()


def update_marriage_date(marriage_id, family_id, hebrew_day, hebrew_month, hebrew_year):
    db = get_db()
    db.execute(
        "UPDATE marriages SET hebrew_day = ?, hebrew_month = ?, hebrew_year = ? WHERE id = ? AND family_id = ?",
        (hebrew_day, hebrew_month, hebrew_year, marriage_id, family_id),
    )
    db.commit()


def create_marriage(family_id, spouse1_id, spouse2_id, hebrew_day, hebrew_month, hebrew_year):
    db = get_db()
    db.execute(
        """
        INSERT INTO marriages (family_id, spouse1_id, spouse2_id, hebrew_day, hebrew_month, hebrew_year)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (family_id, spouse1_id, spouse2_id, hebrew_day, hebrew_month, hebrew_year),
    )
    db.commit()


def get_anniversaries_by_member_id(family_id):
    """Map each member id in a couple to (partner_name, marriage_row) for the members list."""
    result = {}
    for marriage in get_all_marriages(family_id):
        result[marriage["spouse1_id"]] = (marriage["spouse2_name"], marriage)
        result[marriage["spouse2_id"]] = (marriage["spouse1_name"], marriage)
    return result


def get_anniversary_summary(family_id, within_days=UPCOMING_WINDOW_DAYS):
    """Same idea as get_birthday_summary(), but for couples with a known anniversary date."""
    today_list = []
    upcoming_list = []

    for marriage in get_all_marriages(family_id):
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


def get_all_family_events(family_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM family_events WHERE family_id = ? ORDER BY event_date", (family_id,)
    ).fetchall()


def get_family_event(event_id, family_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM family_events WHERE id = ? AND family_id = ?", (event_id, family_id)
    ).fetchone()


def create_family_event(family_id, title, event_date, description):
    db = get_db()
    db.execute(
        "INSERT INTO family_events (family_id, title, event_date, description) VALUES (?, ?, ?, ?)",
        (family_id, title, event_date, description),
    )
    db.commit()


def update_family_event(event_id, family_id, title, event_date, description):
    db = get_db()
    db.execute(
        "UPDATE family_events SET title = ?, event_date = ?, description = ? WHERE id = ? AND family_id = ?",
        (title, event_date, description, event_id, family_id),
    )
    db.commit()


def delete_family_event(event_id, family_id):
    db = get_db()
    db.execute("DELETE FROM family_events WHERE id = ? AND family_id = ?", (event_id, family_id))
    db.commit()


def get_upcoming_family_events(family_id):
    """Custom events (Bar Mitzvah, wedding, a gathering...) from today onward, soonest first."""
    today_iso = date.today().isoformat()
    db = get_db()
    events = db.execute(
        "SELECT * FROM family_events WHERE family_id = ? AND event_date >= ? ORDER BY event_date",
        (family_id, today_iso),
    ).fetchall()

    result = []
    for event in events:
        days = (date.fromisoformat(event["event_date"]) - date.today()).days
        result.append((event, days))
    return result


def get_user_by_email(email):
    db = get_db()
    return db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def get_family(family_id):
    db = get_db()
    return db.execute("SELECT * FROM families WHERE id = ?", (family_id,)).fetchone()


def create_family_with_user(family_name, email, password_hash):
    """Sign-up: a brand new family with its first (admin) user. Returns the new family_id."""
    db = get_db()
    cursor = db.execute("INSERT INTO families (name) VALUES (?)", (family_name,))
    family_id = cursor.lastrowid
    db.execute(
        "INSERT INTO users (family_id, email, password_hash, is_admin) VALUES (?, ?, ?, 1)",
        (family_id, email, password_hash),
    )
    db.commit()
    return family_id
