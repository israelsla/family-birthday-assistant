"""Import data/family_import_review.csv (human-approved) into the SQLite database.

Safety rules:
- Refuses to run if any row still has a non-empty 'note' (unresolved ambiguity).
- Never inserts a duplicate: a row matching an existing (name, hebrew_day,
  hebrew_month, hebrew_year) is skipped, not re-inserted.
- Only touches family_members via INSERT - never deletes or edits existing rows.
"""
import csv
import os
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
REVIEW_PATH = BASE_DIR / "data" / "family_import_review.csv"
DB_PATH = Path(os.environ.get("DATABASE_PATH", BASE_DIR / "instance" / "family.db"))


def load_review_rows():
    with open(REVIEW_PATH, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main():
    rows = load_review_rows()

    unresolved = [r for r in rows if r.get("note", "").strip()]
    if unresolved:
        print("עצירה: יש עדיין רשומות עם הערה לא פתורה, לא מייבא כלום:")
        for r in unresolved:
            print(f"  - {r['name']}: {r['note']}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    inserted, skipped = 0, 0
    for r in rows:
        name = r["name"].strip()
        hebrew_day = int(r["hebrew_day"])
        hebrew_month = r["hebrew_month"].strip()
        hebrew_year = int(r["hebrew_year"]) if r["hebrew_year"] else None
        phone = r["phone"].strip() or None

        existing = conn.execute(
            """
            SELECT id FROM family_members
            WHERE name = ? AND hebrew_day = ? AND hebrew_month = ? AND hebrew_year IS ?
            """,
            (name, hebrew_day, hebrew_month, hebrew_year),
        ).fetchone()

        if existing:
            skipped += 1
            continue

        conn.execute(
            """
            INSERT INTO family_members (name, hebrew_day, hebrew_month, hebrew_year, phone, active)
            VALUES (?, ?, ?, ?, ?, 1)
            """,
            (name, hebrew_day, hebrew_month, hebrew_year, phone),
        )
        inserted += 1

    conn.commit()
    total = conn.execute("SELECT COUNT(*) AS c FROM family_members").fetchone()["c"]
    conn.close()

    print(f"הוכנסו {inserted} רשומות חדשות, {skipped} דולגו (כבר קיימות).")
    print(f"סה\"כ רשומות בטבלה כעת: {total}")


if __name__ == "__main__":
    main()
