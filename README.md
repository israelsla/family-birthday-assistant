# Family Birthday Assistant

מערכת Web משפחתית לניהול ימי הולדת עבריים. שלב 1 (Foundation) כולל:

- שמירת בני משפחה עם תאריך לידה **עברי** (יום/חודש/שנה) ב-SQLite.
- דשבורד ראשוני עם ספירת בני משפחה פעילים (ימי הולדת היום/קרובים הם Placeholder לשלב הבא).
- עמוד "כל בני המשפחה" עם הוספה, עריכה והשבתה (Soft Delete דרך שדה `active`).

חישוב יום ההולדת בפועל, ברכות AI, ואינטגרציית WhatsApp הם שלבים עתידיים ואינם קיימים עדיין.

## מבנה הפרויקט

```
app/
├── __init__.py     # יצירת אפליקציית Flask (application factory)
├── db.py           # חיבור ל-SQLite ואתחול הסכמה
├── models.py       # פונקציות CRUD מול טבלת family_members
├── routes.py       # ה-routes של האתר
├── templates/      # תבניות HTML (Jinja)
└── static/         # CSS ו-JS
schema.sql          # הגדרת טבלת family_members
run.py              # הרצת השרת
```

## התקנה והרצה מקומית

```bash
cd BirthdayProject
python3 -m venv venv
source venv/bin/activate          # ב-Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

לאחר מכן פותחים דפדפן בכתובת: http://127.0.0.1:5000

מסד הנתונים (`instance/family.db`) נוצר אוטומטית בהרצה הראשונה, לפי `schema.sql`.

## משתני סביבה

הקובץ `.env` (שנוצר מ-`.env.example`) מחזיק ערכים שלא נכנסים ל-Git:

- `SECRET_KEY` — מפתח סודי של Flask (לניהול session, flash messages).
- `DATABASE_PATH` — נתיב לקובץ ה-SQLite.

בעתיד, מפתחות API (כגון WhatsApp/AI) יתווספו לאותו קובץ `.env` ולא ייכנסו לקוד.
