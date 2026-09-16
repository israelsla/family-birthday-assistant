"""Admin tool: create a new family + its first login, now that public
self-signup (/signup) is closed.

Run this on whichever machine holds the database you want to add the
family to - locally for testing, or on the PythonAnywhere Bash console
for the real deployed site (they are two separate database files).

    source venv/bin/activate
    python tools/create_family.py

Asks for the family name, email, and password interactively - never
paste real credentials into a chat.
"""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from werkzeug.security import generate_password_hash

from app import create_app, models

MIN_PASSWORD_LENGTH = 8


def main():
    app = create_app()
    with app.app_context():
        family_name = input("שם המשפחה לתצוגה (לדוגמה: משפחת ישראלי): ").strip() or "משפחה חדשה"
        email = input("אימייל להתחברות: ").strip().lower()

        if models.get_user_by_email(email) is not None:
            print(f"כבר קיים משתמש עם האימייל {email!r}. לא נוצר כלום.")
            sys.exit(1)

        while True:
            password = getpass.getpass(f"סיסמה (לפחות {MIN_PASSWORD_LENGTH} תווים): ")
            password_confirm = getpass.getpass("אימות סיסמה: ")
            if password != password_confirm:
                print("הסיסמאות לא תואמות, נסה שוב.\n")
                continue
            if len(password) < MIN_PASSWORD_LENGTH:
                print(f"הסיסמה קצרה מדי (מינימום {MIN_PASSWORD_LENGTH} תווים), נסה שוב.\n")
                continue
            break

        family_id = models.create_family_with_user(family_name, email, generate_password_hash(password))
        print(f"\nהצלחה! נוצרה משפחה #{family_id}: {family_name}")
        print(f"אפשר להתחבר עם: {email}")


if __name__ == "__main__":
    main()
