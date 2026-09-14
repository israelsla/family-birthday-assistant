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


_TENS = [(90, "צ"), (80, "פ"), (70, "ע"), (60, "ס"), (50, "נ"), (40, "מ"), (30, "ל"), (20, "כ"), (10, "י")]
_UNITS = [(9, "ט"), (8, "ח"), (7, "ז"), (6, "ו"), (5, "ה"), (4, "ד"), (3, "ג"), (2, "ב"), (1, "א")]
_FINAL_FORMS = {"כ": "ך", "מ": "ם", "נ": "ן", "פ": "ף", "צ": "ץ"}


def _letters_for_number(n):
    """Raw Hebrew letters (no punctuation) for a positive integer, e.g. 27 -> 'כז'."""
    letters = ""
    remaining = n
    while remaining >= 400:
        letters += "ת"
        remaining -= 400
    for value, letter in [(300, "ש"), (200, "ר"), (100, "ק")]:
        if remaining >= value:
            letters += letter
            remaining -= value
            break

    if remaining in (15, 16):
        # avoid יה/יו, which look like God's name - use טו/טז instead
        letters += "טו" if remaining == 15 else "טז"
        return letters

    for value, letter in _TENS:
        if remaining >= value:
            letters += letter
            remaining -= value
            break
    for value, letter in _UNITS:
        if remaining >= value:
            letters += letter
            remaining -= value
            break
    return letters


def _punctuate(letters):
    """Single letter gets a geresh (א׳); multiple letters get gershayim before the last (כ״ז)."""
    if len(letters) <= 1:
        return letters + "׳"
    return letters[:-1] + "״" + letters[-1]


def format_hebrew_day(day):
    """27 -> 'כ״ז', 1 -> 'א׳', 30 -> 'ל׳'. No final-letter forms - a lone day numeral never uses them."""
    return _punctuate(_letters_for_number(day))


def format_hebrew_year(year, era_offset=HEBREW_YEAR_ERA_OFFSET):
    """5750 -> 'תש״ן' (final nun, since it ends a year abbreviation, unlike a standalone day letter)."""
    letters = _letters_for_number(year - era_offset)
    if letters and letters[-1] in _FINAL_FORMS:
        letters = letters[:-1] + _FINAL_FORMS[letters[-1]]
    return _punctuate(letters)


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

    # the reverse direction: numbers back into Hebrew letters
    assert format_hebrew_day(19) == "י״ט"
    assert format_hebrew_day(22) == "כ״ב"
    assert format_hebrew_day(16) == "ט״ז"
    assert format_hebrew_day(1) == "א׳"
    assert format_hebrew_day(30) == "ל׳"
    assert format_hebrew_year(5707) == "תש״ז"
    assert format_hebrew_year(5786) == "תשפ״ו"
    assert format_hebrew_year(5750) == "תש״ן"  # final-nun, matches the source PDF's own spelling
    print("כל בדיקות הסניטי עברו בהצלחה")
