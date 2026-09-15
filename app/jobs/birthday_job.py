"""The daily birthday job: find who has a Hebrew birthday, build a greeting, "send" it.

Runs in the evening (see run_scheduler.py) and checks *tomorrow's* Hebrew
date, not today's - a Hebrew day begins at nightfall, so someone born on
א' ניסן should get their greeting during the evening of כ"ט אדר, which is
already religiously "א' ניסן" even though the Gregorian calendar still
says "today."

generate_greeting() builds the message from a fixed set of Hebrew templates
- no AI, no external calls, no cost, nothing that can be "down." (An AI
version was considered, but Anthropic's Consumer Terms only allow automated/
unattended account access via a paid API key, which is exactly what this
project avoids - see the commit message for details.)

send_greeting() is still a placeholder on purpose: this is where the real
WhatsApp send will plug in later, without touching find_members_with_birthday_on()
or run_birthday_job().

Since Stage 4 (multi-family support), this job loops over every family
separately - each family's members are only ever compared against that
same family's data.
"""
import logging
import random

from app import hebrew_calendar, models

logger = logging.getLogger(__name__)

_GREETING_TEMPLATES_WITH_AGE = [
    "🎉 מזל טוב ל{name}! היום חוגגים {age} שנים לפי הלוח העברי - שתהיה שנה מתוקה ומלאה בשמחה! 🎂",
    "🎂 מזל טוב {name}! גיל {age} מתחיל היום - איחולים לשנה טובה, בריאה ומאושרת מכל המשפחה! 🎉",
    "✨ {name} היקר/ה, מזל טוב ליום ההולדת ה-{age}! שתזכה/י לשנה של אהבה, בריאות והצלחה. 🎈",
    "🎁 יום הולדת שמח ל{name}! היום נחגוג {age} שנים - כל הכבוד וכל האהבה מכל המשפחה! 🎊",
]

_GREETING_TEMPLATES_NO_AGE = [
    "🎉 מזל טוב ל{name}! היום יום ההולדת העברי שלך - שתהיה שנה מתוקה ומלאה בשמחה! 🎂",
    "🎂 מזל טוב {name}! איחולים לשנה טובה, בריאה ומאושרת, מכל המשפחה! 🎉",
]


def find_members_with_birthday_on(check_date, family_id):
    return [
        member
        for member in models.get_active_members(family_id)
        if hebrew_calendar.is_birthday_on(member["hebrew_day"], member["hebrew_month"], check_date)
    ]


def generate_greeting(member):
    """A warm Hebrew birthday greeting, picked from a fixed template set. No AI, no cost."""
    if member["hebrew_year"]:
        age = hebrew_calendar.age_in_years(member["hebrew_day"], member["hebrew_month"], member["hebrew_year"])
        template = random.choice(_GREETING_TEMPLATES_WITH_AGE)
        return template.format(name=member["name"], age=age)

    template = random.choice(_GREETING_TEMPLATES_NO_AGE)
    return template.format(name=member["name"])


def send_greeting(member, greeting_text):
    """Placeholder 'send' - this is where the WhatsApp integration plugs in later."""
    logger.info("BIRTHDAY GREETING (not actually sent yet) -> %s: %s", member["name"], greeting_text)


def run_birthday_job(check_date=None):
    """The nightly job. check_date defaults to the Hebrew date that starts tonight.

    Runs once per family - families never see each other's members.
    """
    check_date = check_date or hebrew_calendar.tomorrow()
    families = models.get_all_families()

    all_members_with_birthday = []
    for family in families:
        members = find_members_with_birthday_on(check_date, family["id"])
        for member in members:
            send_greeting(member, generate_greeting(member))
        all_members_with_birthday.extend(members)

    logger.info(
        "Birthday job checked %s across %d family/families - found %d birthday(s)",
        check_date, len(families), len(all_members_with_birthday),
    )
    return all_members_with_birthday


if __name__ == "__main__":
    # manual test: `python -m app.jobs.birthday_job` runs the job once, right now,
    # without waiting for the scheduler or the real evening.
    from app import create_app

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    app = create_app()
    with app.app_context():
        run_birthday_job()
