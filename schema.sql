CREATE TABLE IF NOT EXISTS family_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    hebrew_day INTEGER NOT NULL CHECK (hebrew_day BETWEEN 1 AND 30),
    hebrew_month TEXT NOT NULL CHECK (hebrew_month IN (
        'תשרי', 'חשוון', 'כסלו', 'טבת', 'שבט',
        'אדר', 'אדר א׳', 'אדר ב׳',
        'ניסן', 'אייר', 'סיון', 'תמוז', 'אב', 'אלול'
    )),
    hebrew_year INTEGER,
    phone TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS marriages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    spouse1_id INTEGER NOT NULL REFERENCES family_members(id),
    spouse2_id INTEGER NOT NULL REFERENCES family_members(id),
    hebrew_day INTEGER CHECK (hebrew_day IS NULL OR hebrew_day BETWEEN 1 AND 30),
    hebrew_month TEXT CHECK (hebrew_month IS NULL OR hebrew_month IN (
        'תשרי', 'חשוון', 'כסלו', 'טבת', 'שבט',
        'אדר', 'אדר א׳', 'אדר ב׳',
        'ניסן', 'אייר', 'סיון', 'תמוז', 'אב', 'אלול'
    )),
    hebrew_year INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS family_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    event_date TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
