"""Figure out, for a stored Hebrew day/month, when it next falls this year or next.

Uses pyluach (github.com/simlist/pyluach) for the actual Hebrew<->Gregorian
math instead of hand-rolling it - leap years and month lengths are easy to
get subtly wrong.

Adar policy (confirmed with the family): someone recorded with a plain
"אדר" (born in a regular, non-leap year) celebrates in אדר ב׳ when the
current/target year is a leap year. Someone recorded as אדר א׳ or אדר ב׳
simply collapses to the single אדר in a year that has no leap month.
"""
from pyluach import hebrewcal
from pyluach.dates import HebrewDate

_MONTH_NUMBERS_NON_LEAP = {
    "ניסן": 1, "אייר": 2, "סיון": 3, "תמוז": 4, "אב": 5, "אלול": 6,
    "תשרי": 7, "חשוון": 8, "כסלו": 9, "טבת": 10, "שבט": 11,
    "אדר": 12, "אדר א׳": 12, "אדר ב׳": 12,
}

_MONTH_NUMBERS_LEAP = {
    **_MONTH_NUMBERS_NON_LEAP,
    "אדר": 13,    # policy: plain אדר -> אדר ב׳ in a leap year
    "אדר ב׳": 13,
    # "אדר א׳" stays 12 - that's the real Adar I month number in a leap year
}


def today():
    """Today's date as a pyluach HebrewDate."""
    return HebrewDate.today()


def tomorrow():
    """The Hebrew date that begins tonight at nightfall.

    A Hebrew day starts at sunset, not midnight - so an evening job checking
    "who has a birthday tonight" should compare against tomorrow's Hebrew
    date, not today's.
    """
    return today() + 1


def is_leap_year(hebrew_year):
    return hebrewcal.Year(hebrew_year).leap


def month_number_for(hebrew_month, target_hebrew_year):
    table = _MONTH_NUMBERS_LEAP if is_leap_year(target_hebrew_year) else _MONTH_NUMBERS_NON_LEAP
    return table[hebrew_month]


def next_occurrence(hebrew_day, hebrew_month, from_date=None):
    """The next HebrewDate (today or in the future) this day/month falls on."""
    from_date = from_date or today()

    for year_offset in (0, 1):
        target_year = from_date.year + year_offset
        month_number = month_number_for(hebrew_month, target_year)
        days_in_month = len(hebrewcal.Month(target_year, month_number))
        # a month can be shorter this year than the recorded day (e.g. day 30
        # of a Cheshvan that only has 29 days this year) - fall back to its
        # last day rather than raise an error
        day = min(hebrew_day, days_in_month)
        candidate = HebrewDate(target_year, month_number, day)
        if candidate >= from_date:
            return candidate

    raise RuntimeError("could not find a next occurrence within one year - this should not happen")


def is_birthday_on(hebrew_day, hebrew_month, on_date):
    """Does this recorded day/month fall exactly on on_date (a HebrewDate)?"""
    month_number = month_number_for(hebrew_month, on_date.year)
    days_in_month = len(hebrewcal.Month(on_date.year, month_number))
    day = min(hebrew_day, days_in_month)
    return on_date.month == month_number and on_date.day == day


def days_until(hebrew_day, hebrew_month, from_date=None):
    from_date = from_date or today()
    occurrence = next_occurrence(hebrew_day, hebrew_month, from_date)
    return occurrence - from_date


def age_in_years(hebrew_day, hebrew_month, hebrew_year, from_date=None):
    """Current age: years since birth, counting down by one until this year's birthday arrives."""
    from_date = from_date or today()

    month_number = month_number_for(hebrew_month, from_date.year)
    days_in_month = len(hebrewcal.Month(from_date.year, month_number))
    day = min(hebrew_day, days_in_month)
    this_years_birthday = HebrewDate(from_date.year, month_number, day)

    age = from_date.year - hebrew_year
    if this_years_birthday > from_date:
        age -= 1
    return age
