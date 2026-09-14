from app.db import get_db

HEBREW_MONTHS = [
    "תשרי", "חשוון", "כסלו", "טבת", "שבט",
    "אדר", "אדר א׳", "אדר ב׳",
    "ניסן", "אייר", "סיוון", "תמוז", "אב", "אלול",
]


def get_all_members():
    """Return every family member, active and inactive, sorted by name."""
    db = get_db()
    return db.execute("SELECT * FROM family_members ORDER BY name").fetchall()


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
