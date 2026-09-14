"""One-time seed: link the known couples in family_members via the marriages table.

Only Israel & Hadas's date is actually known (כ״ב אדר תשפ״ד); everyone else
is seeded with an unknown (NULL) date, editable later from the members page.

Safe to re-run: skips a couple that's already linked (checked either order).
"""
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "instance" / "family.db"

# (spouse1 name, spouse2 name, hebrew_day, hebrew_month, hebrew_year) - None = unknown
COUPLES = [
    ("יהודה יצחק", "רחל", None, None, None),
    ("אריה", "דבורה", None, None, None),
    ("דודי", "נטע", None, None, None),
    ("שמוליק", "עידית", None, None, None),
    ("מאיר יחיאל", "זוהרה מלכה", None, None, None),
    ("ידידיה אהרון", "רננה", None, None, None),
    ("אסף", "תמר", None, None, None),
    ("ישראל", "הדס", 22, "אדר", 5784),
    ("יהונתן", "יעל", None, None, None),
    ("אביטל", "מרדכי יאיר", None, None, None),  # מוטי = כינוי למרדכי
    ("נועם", "רעות הניה", None, None, None),
]


def get_member_id(conn, name):
    row = conn.execute("SELECT id FROM family_members WHERE name = ?", (name,)).fetchone()
    if row is None:
        raise ValueError(f"לא נמצא בן משפחה בשם {name!r}")
    return row[0]


def already_linked(conn, id1, id2):
    return conn.execute(
        """
        SELECT 1 FROM marriages
        WHERE (spouse1_id = ? AND spouse2_id = ?) OR (spouse1_id = ? AND spouse2_id = ?)
        """,
        (id1, id2, id2, id1),
    ).fetchone() is not None


def main():
    conn = sqlite3.connect(DB_PATH)
    inserted, skipped = 0, 0

    for name1, name2, day, month, year in COUPLES:
        id1 = get_member_id(conn, name1)
        id2 = get_member_id(conn, name2)

        if already_linked(conn, id1, id2):
            skipped += 1
            continue

        conn.execute(
            """
            INSERT INTO marriages (spouse1_id, spouse2_id, hebrew_day, hebrew_month, hebrew_year)
            VALUES (?, ?, ?, ?, ?)
            """,
            (id1, id2, day, month, year),
        )
        inserted += 1

    conn.commit()
    conn.close()
    print(f"נוספו {inserted} זוגות, {skipped} דולגו (כבר קיימים).")


if __name__ == "__main__":
    main()
