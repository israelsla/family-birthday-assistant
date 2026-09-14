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
├── hebrew_numerals.py   # המרות בין מספרים לאותיות עבריות (יום/שנה)
├── hebrew_calendar.py   # חישובי לוח עברי (מתי הבא, גיל, יום הולדת בתאריך נתון)
├── jobs/
│   └── birthday_job.py  # ה-Job היומי: מוצא ימי הולדת, מכין ברכה, "שולח" (כרגע רק log)
├── templates/      # תבניות HTML (Jinja)
└── static/         # CSS ו-JS
schema.sql          # הגדרת טבלת family_members
run.py              # הרצת שרת האתר (Dashboard)
run_scheduler.py    # תהליך נפרד שמריץ את ה-Job היומי בשעה קבועה
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

## ה-Job היומי (Stage 3)

`run_scheduler.py` הוא תהליך **נפרד** מהאתר עצמו - צריך להריץ אותו בנוסף ל-`run.py`, לא במקומו:

```bash
python run_scheduler.py
```

הוא רץ ברקע ובודק כל ערב (ברירת מחדל: 19:00 שעון ישראל, ניתן לשינוי ב-`.env` דרך `BIRTHDAY_JOB_HOUR`/`BIRTHDAY_JOB_MINUTE`) האם מישהו חוגג יום הולדת עברי שמתחיל באותו ערב. בשלב הזה הוא רק **רושם ל-log** מי היה מקבל ברכה - עדיין אין AI ואין שליחה בפועל ל-WhatsApp.

לבדיקה מיידית בלי לחכות לשעה הקבועה:

```bash
python -m app.jobs.birthday_job
```
