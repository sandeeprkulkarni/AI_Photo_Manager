# backend/modules/recognition.py
import numpy as np
import sqlite3
from .index_store import DB_PATH

class RecognitionEngine:
    def __init__(self):
        self.known_embeddings = [] 
        self.known_names = []      
        self.threshold = 0.6       

    async def load_training_data(self):
        """Reloads labeled faces from DB into memory."""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT embedding, identity_name FROM faces WHERE identity_name IS NOT NULL")
            rows = cursor.fetchall()
            
            if not rows:
                return

            self.known_embeddings = [np.frombuffer(r[0], dtype=np.float64) for r in rows]
            self.known_names = [r[1] for r in rows]
            print(f"RecognitionEngine: Loaded {len(self.known_names)} faces.")

    def identify_face(self, target_embedding: np.ndarray):
        """Distance-based matching."""
        if not self.known_embeddings:
            return "Unknown"

        distances = np.linalg.norm(self.known_embeddings - target_embedding, axis=1)
        min_idx = np.argmin(distances)
        
        return self.known_names[min_idx] if distances[min_idx] < self.threshold else "Unknown"

    async def update_unlabeled_faces(self):
        """Background task to auto-label similar faces."""
        if not self.known_embeddings:
            return

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, embedding FROM faces WHERE identity_name IS NULL")
            unlabeled = cursor.fetchall()
            
            updates = []
            for face_id, emb_blob in unlabeled:
                emb = np.frombuffer(emb_blob, dtype=np.float64)
                name = self.identify_face(emb)
                if name != "Unknown":
                    updates.append((name, face_id))
            
            if updates:
                cursor.executemany("UPDATE faces SET identity_name = ? WHERE id = ?", updates)
                conn.commit()
                
    async def load_training_data(self):
        """Reloads labeled faces from DB into memory."""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # We fetch all labeled faces, including the ones we just added via /api/train
            cursor.execute("SELECT embedding, identity_name FROM faces WHERE identity_name IS NOT NULL")
            rows = cursor.fetchall()
            
            if not rows:
                print("RecognitionEngine: No training data found.")
                return

            self.known_embeddings = [np.frombuffer(r[0], dtype=np.float64) for r in rows]
            self.known_names = [r[1] for r in rows]
            print(f"RecognitionEngine: Loaded {len(self.known_names)} faces for identification.")            