"""One-time migration: add multi-family support to an existing database.

Creates the new `families` and `users` tables, adds a `family_id` column
to family_members/marriages/family_events (backfilled to the new family
for every existing row), and creates your first login.

Safe to run only once - refuses to run again if families/users already
exist. Always backs up the database (a binary copy AND a readable .sql
dump) before touching anything.

Run this yourself, interactively, from the project root:
    source venv/bin/activate
    python tools/migrate_to_multitenant.py

It will ask for your email and password directly in the terminal - never
paste real credentials into a chat.
"""
import getpass
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from werkzeug.security import generate_password_hash

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "instance" / "family.db"


def backup_database():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    binary_backup = DB_PATH.with_name(f"family.db.backup-{timestamp}")
    shutil.copy2(DB_PATH, binary_backup)

    sql_backup = DB_PATH.with_name(f"family.sql.backup-{timestamp}")
    conn = sqlite3.connect(DB_PATH)
    with open(sql_backup, "w", encoding="utf-8") as f:
        for line in conn.iterdump():
            f.write(f"{line}\n")
    conn.close()

    print(f"גיבוי נשמר: {binary_backup.name}")
    print(f"גיבוי קריא (טקסט): {sql_backup.name}")


def already_migrated(conn):
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    return "families" in tables and "users" in tables


def column_exists(conn, table, column):
    columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    return column in columns


def prompt_for_family_and_user():
    print("--- פרטי המשפחה שלך ---")
    family_name = input("שם המשפחה לתצוגה (לדוגמה: משפחת ישראלי): ").strip() or "המשפחה שלי"

    print("\n--- המשתמש הראשון שלך (האחראי) ---")
    email = input("אימייל להתחברות: ").strip()
    while True:
        password = getpass.getpass("סיסמה (לפחות 8 תווים, לא תוצג על המסך): ")
        password_confirm = getpass.getpass("אימות סיסמה: ")
        if password != password_confirm:
            print("הסיסמאות לא תואמות, נסה שוב.\n")
            continue
        if len(password) < 8:
            print("הסיסמה קצרה מדי (מינימום 8 תווים), נסה שוב.\n")
            continue
        break

    return family_name, email, password


def main():
    if not DB_PATH.exists():
        print(f"לא נמצא קובץ database ב-{DB_PATH}. אין מה למגר.")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)

    if already_migrated(conn):
        print("נראה שהמיגרציה כבר רצה בעבר (טבלאות families/users כבר קיימות). לא עושה כלום.")
        sys.exit(0)

    backup_database()

    family_name, email, password = prompt_for_family_and_user()

    conn.execute(
        """
        CREATE TABLE families (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            family_id INTEGER NOT NULL REFERENCES families(id),
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )

    cursor = conn.execute("INSERT INTO families (name) VALUES (?)", (family_name,))
    family_id = cursor.lastrowid

    conn.execute(
        "INSERT INTO users (family_id, email, password_hash, is_admin) VALUES (?, ?, ?, 1)",
        (family_id, email, generate_password_hash(password)),
    )

    for table in ("family_members", "marriages", "family_events"):
        if not column_exists(conn, table, "family_id"):
            conn.execute(
                f"ALTER TABLE {table} ADD COLUMN family_id INTEGER NOT NULL "
                f"DEFAULT {family_id} REFERENCES families(id)"
            )

    conn.commit()

    counts = {
        table: conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE family_id = ?", (family_id,)
        ).fetchone()[0]
        for table in ("family_members", "marriages", "family_events")
    }
    conn.close()

    print(f"\nהצלחה! נוצרה משפחה #{family_id}: {family_name}")
    print(
        f"שויכו אליה: {counts['family_members']} בני משפחה, "
        f"{counts['marriages']} זוגות, {counts['family_events']} אירועים."
    )
    print(f"המשתמש שלך: {email} (אחראי)")


if __name__ == "__main__":
    main()
