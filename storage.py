"""Local human-review audit log; no external data transfer."""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path('data/reviews.sqlite3')

def initialize(db_path=DEFAULT_DB):
    path=Path(db_path)
    path.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute('''CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT, created_utc TEXT NOT NULL,
            dataset_hash TEXT NOT NULL, status TEXT NOT NULL,
            reviewer_note TEXT NOT NULL, analysis_json TEXT NOT NULL)''')

def save_review(dataset_hash, status, note, analysis, db_path=DEFAULT_DB):
    if status not in ('approved','rejected','needs_evidence'):
        raise ValueError('Unsupported review status.')
    if not note.strip():
        raise ValueError('Reviewer note is required.')
    initialize(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute('INSERT INTO reviews (created_utc,dataset_hash,status,reviewer_note,analysis_json) VALUES (?,?,?,?,?)',
            (datetime.now(timezone.utc).isoformat(),dataset_hash,status,note.strip(),json.dumps(analysis,ensure_ascii=False,allow_nan=False)))

def list_reviews(db_path=DEFAULT_DB):
    initialize(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.row_factory=sqlite3.Row
        return [dict(r) for r in connection.execute('SELECT * FROM reviews ORDER BY id DESC')]
