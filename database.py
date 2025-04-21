import sqlite3
from flask import g
from pathlib import Path

DATABASE = Path(__file__).parent / 'crosswords.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    with get_db() as db:
        with open(Path(__file__).parent / 'schema.sql') as f:
            db.executescript(f.read())