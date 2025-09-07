-- Schema for podcast management app
CREATE TABLE episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    scheduled_date TIMESTAMP
);
