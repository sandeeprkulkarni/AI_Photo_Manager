# modules/index_store.py
import sqlite3
from pathlib import Path

DB_PATH = Path("data/db/index.db")

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY, 
            path TEXT UNIQUE, 
            hash TEXT UNIQUE, 
            size_kb INTEGER, 
            taken_at DATETIME, 
            is_photo INTEGER DEFAULT 1,
            is_forward INTEGER DEFAULT 0, 
            has_faces INTEGER DEFAULT 0,
            gps_lat REAL,          -- New: Latitude
            gps_lon REAL,          -- New: Longitude
            location_name TEXT,    -- New: Resolved City/Place
            event_type TEXT        -- New: Wedding, Festival, etc.
        )""")
        
        conn.execute("""
        CREATE TABLE IF NOT EXISTS faces (
            id INTEGER PRIMARY KEY, photo_id INTEGER REFERENCES photos(id),
            rect_x INTEGER, rect_y INTEGER, rect_w INTEGER, rect_h INTEGER,
            embedding BLOB, cluster_id INTEGER DEFAULT -1,
            identity_name TEXT,     -- New: Explicitly trained identity
            UNIQUE(photo_id, rect_x, rect_y) 
        )""")
        
        conn.execute("""
        CREATE TABLE IF NOT EXISTS persons (
            id INTEGER PRIMARY KEY, name TEXT UNIQUE, cluster_id INTEGER UNIQUE 
        )""")
        conn.commit()