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
