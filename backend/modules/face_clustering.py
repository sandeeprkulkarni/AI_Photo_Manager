import sqlite3
import numpy as np
from sklearn.cluster import DBSCAN
from modules.index_store import DB_PATH

def cluster_faces(eps=0.55, min_samples=1):
    with sqlite3.connect(DB_PATH) as conn:
        # 1. Load all embeddings from DB
        cursor = conn.execute("SELECT id, embedding FROM faces")
        rows = cursor.fetchall()
        
        if not rows:
            print("No faces found to cluster.")
            return

        face_ids = [row[0] for row in rows]
        # Convert BLOBs back to numpy arrays
        embeddings = [np.frombuffer(row[1], dtype=np.float64) for row in rows]
        
        # 2. Run DBSCAN Clustering
        # eps: lower is stricter (closer match), higher is looser
        clt = DBSCAN(eps=eps, min_samples=min_samples, metric="euclidean")
        clt.fit(embeddings)
        
        # 3. Update Database with new Cluster IDs
        for face_id, label in zip(face_ids, clt.labels_):
            conn.execute("UPDATE faces SET cluster_id = ? WHERE id = ?", (int(label), face_id))
        
        conn.commit()
        print(f"Clustering complete. Found {len(set(clt.labels_)) - (1 if -1 in clt.labels_ else 0)} unique people.")