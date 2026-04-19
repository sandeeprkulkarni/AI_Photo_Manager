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
def label_face_identity(face_id: int, name: str):
    """
    Assigns a name to a specific face and creates/links a person record.
    Also updates the cluster_id if this face belongs to one.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # 1. Ensure the person exists in the 'persons' table
        cursor.execute(
            "INSERT OR IGNORE INTO persons (name) VALUES (?)", 
            (name,)
        )
        
        # 2. Get the person_id and current cluster_id of this face
        cursor.execute("SELECT id FROM persons WHERE name = ?", (name,))
        person_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT cluster_id FROM faces WHERE id = ?", (face_id,))
        result = cursor.fetchone()
        cluster_id = result[0] if result else -1

        # 3. Update the specific face with the identity name
        cursor.execute(
            "UPDATE faces SET identity_name = ? WHERE id = ?", 
            (name, face_id)
        )

        # 4. If the face is part of a cluster, link that cluster to the person
        if cluster_id != -1:
            cursor.execute(
                "UPDATE persons SET cluster_id = ? WHERE id = ?", 
                (cluster_id, person_id)
            )
            
        conn.commit()

def get_labeled_embeddings():
    """
    Retrieves all embeddings that have been manually labeled.
    Used by recognition.py to 'train' the local inference model.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT embedding, identity_name FROM faces WHERE identity_name IS NOT NULL"
        )
        return cursor.fetchall()

def get_person_id_by_name(name: str):
    """Helper to find person metadata by name."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, cluster_id FROM persons WHERE name = ?", (name,))
        return cursor.fetchone()