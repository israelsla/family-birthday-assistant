"""Turn data/family_raw.csv into data/family_import_review.csv for human review.

This does NOT touch the SQLite database - it only converts Hebrew-letter
dates into the numeric/normalized form our schema expects, and flags any
row a human needs to look at before it's safe to import.
"""
import csv
from pathlib import Path

from hebrew_numerals import is_hebrew_leap_year, normalize_month, parse_hebrew_day, parse_hebrew_year

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_PATH = BASE_DIR / "data" / "family_raw.csv"
REVIEW_PATH = BASE_DIR / "data" / "family_import_review.csv"


def build_review_rows():
    rows = []
    with open(RAW_PATH, encoding="utf-8-sig", newline="") as f:
        for raw_row in csv.DictReader(f):
            name = raw_row["name"].strip()
            hebrew_month = normalize_month(raw_row["hebrew_month_raw"])
            hebrew_day = parse_hebrew_day(raw_row["hebrew_day_raw"])
            hebrew_year = parse_hebrew_year(raw_row["hebrew_year_raw"])

            notes = []
            if hebrew_day is None:
                notes.append(
                    f"יום לא חד-משמעי במקור ('{raw_row['hebrew_day_raw']}') - נא לבחור יום סופי"
                )
            if hebrew_month == "אדר" and is_hebrew_leap_year(hebrew_year):
                notes.append(
                    "שנה מעוברת אך המקור כתב 'אדר' סתם - נא לאשר אם הכוונה לאדר א׳ או אדר ב׳"
                )

            rows.append({
                "name": name,
                "hebrew_day": hebrew_day if hebrew_day is not None else "",
                "hebrew_month": hebrew_month,
                "hebrew_year": hebrew_year,
                "phone": "",
                "note": " | ".join(notes),
            })
    return rows


def main():
    rows = build_review_rows()

    with open(REVIEW_PATH, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "hebrew_day", "hebrew_month", "hebrew_year", "phone", "note"])
        writer.writeheader()
        writer.writerows(rows)

    flagged = [r for r in rows if r["note"]]
    print(f"נכתבו {len(rows)} רשומות אל {REVIEW_PATH.relative_to(BASE_DIR)}")
    print(f"{len(flagged)} רשומות דורשות בדיקה שלך לפני Import:")
    for r in flagged:
        print(f"  - {r['name']}: {r['note']}")


if __name__ == "__main__":
    main()
