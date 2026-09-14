"""Convert Hebrew-letter numerals (as used for Hebrew dates) to integers.

Handles gershayim/geresh punctuation and final-letter forms (e.g. ן = נ).
Does not need to special-case ט"ז/ט"ו (15/16) - those are writing
conventions for *producing* Hebrew numerals (avoiding letters that spell
God's name), not a parsing concern: summing the letters as written already
gives the right value.
"""

LETTER_VALUES = {
    "א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5, "ו": 6, "ז": 7, "ח": 8, "ט": 9,
    "י": 10, "כ": 20, "ל": 30, "מ": 40, "נ": 50, "ס": 60, "ע": 70, "פ": 80,
    "צ": 90, "ק": 100, "ר": 200, "ש": 300, "ת": 400,
    # final forms carry the same value as their regular counterpart
    "ך": 20, "ם": 40, "ן": 50, "ף": 80, "ץ": 90,
}

HEBREW_YEAR_ERA_OFFSET = 5000

MONTH_NORMALIZATION = {
    "תשרי": "תשרי",
    "חשוון": "חשוון",
    "חשון": "חשוון",
    "מרחשון": "חשוון",
    "מרחשוון": "חשוון",
    "כסלו": "כסלו",
    "טבת": "טבת",
    "שבט": "שבט",
    "אדר": "אדר",
    "אדר א": "אדר א׳",
    "אדר א'": "אדר א׳",
    "אדר א׳": "אדר א׳",
    "אדר ב": "אדר ב׳",
    "אדר ב'": "אדר ב׳",
    "אדר ב׳": "אדר ב׳",
    "ניסן": "ניסן",
    "אייר": "אייר",
    "סיון": "סיון",
    "סיוון": "סיון",
    "תמוז": "תמוז",
    "אב": "אב",
    "אלול": "אלול",
}


def hebrew_letters_to_number(raw):
    """Sum the gematria value of every Hebrew letter in raw, ignoring punctuation."""
    total = 0
    for ch in raw:
        if ch in LETTER_VALUES:
            total += LETTER_VALUES[ch]
    return total


def parse_hebrew_day(raw):
    """'כ"ז' -> 27, 'ל' -> 30, 'ו (ז)' -> None (ambiguous, needs a human decision)."""
    raw = raw.strip()
    if "(" in raw:
        return None
    return hebrew_letters_to_number(raw)


def parse_hebrew_year(raw):
    """'תשפ"ו' -> 5786 (assumes the 5000s era, standard for dates after ~1240 CE)."""
    return HEBREW_YEAR_ERA_OFFSET + hebrew_letters_to_number(raw.strip())


def is_hebrew_leap_year(year):
    """19-year Metonic cycle: leap years are those where year % 19 is one of these."""
    return (year % 19) in {0, 3, 6, 8, 11, 14, 17}


def normalize_month(raw):
    raw = raw.strip()
    if raw not in MONTH_NORMALIZATION:
        raise ValueError(f"חודש לא מוכר: {raw!r}")
    return MONTH_NORMALIZATION[raw]


if __name__ == "__main__":
    # quick sanity checks against known values before trusting this on real data
    assert hebrew_letters_to_number("ט\"ז") == 16
    assert hebrew_letters_to_number("ט\"ו") == 15
    assert parse_hebrew_day("כ\"ז") == 27
    assert parse_hebrew_day("ל") == 30
    assert parse_hebrew_day("ו (ז)") is None
    assert parse_hebrew_year("תש\"ז") == 5707
    assert parse_hebrew_year("תשפ\"ו") == 5786
    assert parse_hebrew_year("תש\"ן") == 5750  # final-nun (ן) must count as 50
    assert is_hebrew_leap_year(5776) is True
    assert is_hebrew_leap_year(5737) is False
    assert normalize_month("מרחשון") == "חשוון"
    assert normalize_month("אדר א") == "אדר א׳"
    print("כל בדיקות הסניטי עברו בהצלחה")
