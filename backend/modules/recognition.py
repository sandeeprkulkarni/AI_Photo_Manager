# modules/recognition.py
import numpy as np
import sqlite3
from scipy.spatial.distance import euclidean

def identify_face(new_embedding, threshold=0.6):
    """Matches a new face embedding against labeled database embeddings"""
    conn = sqlite3.connect(DB_PATH)
    # Get all faces already assigned to a person name
    cursor = conn.execute("""
        SELECT f.embedding, p.name, p.cluster_id 
        FROM faces f 
        JOIN persons p ON f.cluster_id = p.cluster_id
    """)
    known_faces = cursor.fetchall()
    conn.close()

    best_match = None
    min_dist = threshold

    for db_emb_blob, name, cid in known_faces:
        db_emb = np.frombuffer(db_emb_blob, dtype=np.float64)
        dist = euclidean(new_embedding, db_emb)
        if dist < min_dist:
            min_dist = dist
            best_match = (name, cid)
            
    return best_match # Returns (Name, Cluster_ID) or None