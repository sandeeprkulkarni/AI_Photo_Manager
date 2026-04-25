# backend/modules/recognition.py
import numpy as np
import sqlite3
from scipy.spatial.distance import euclidean
from modules.index_store import DB_PATH

class RecognitionEngine:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []

    async def load_training_data(self):
        """Loads labeled faces from the database into memory."""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("""
                SELECT f.embedding, p.name 
                FROM faces f 
                JOIN persons p ON f.cluster_id = p.cluster_id
            """)
            rows = cursor.fetchall()
            self.known_face_encodings = [np.frombuffer(r[0], dtype=np.float64) for r in rows]
            self.known_face_names = [r[1] for r in rows]
            print(f"Loaded {len(self.known_face_names)} labeled faces.")

    def identify_face(self, new_embedding, threshold=0.6):
        if not self.known_face_encodings:
            return None
        
        distances = [euclidean(new_embedding, known) for known in self.known_face_encodings]
        min_dist = min(distances)
        
        if min_dist < threshold:
            index = distances.index(min_dist)
            return self.known_face_names[index]
        return None