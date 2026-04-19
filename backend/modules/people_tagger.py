import sqlite3
from modules.index_store import DB_PATH

def get_clusters():
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute("""
            SELECT cluster_id, COUNT(*), photo_id FROM faces 
            WHERE cluster_id >= 0 GROUP BY cluster_id ORDER BY COUNT(*) DESC
        """).fetchall()

def get_cluster_faces(cluster_id):
    """Returns photo paths for a specific person"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("""
            SELECT p.path FROM photos p JOIN faces f ON p.id = f.photo_id
            WHERE f.cluster_id = ?
        """, (cluster_id,))
        return [row[0] for row in cursor.fetchall()]

def get_person_name(cluster_id):
    with sqlite3.connect(DB_PATH) as conn:
        res = conn.execute("SELECT name FROM persons WHERE cluster_id = ?", (cluster_id,)).fetchone()
        return res[0] if res else f"Person {cluster_id}"

def rename_cluster(cluster_id, new_name):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO persons (name, cluster_id) VALUES (?, ?)
            ON CONFLICT(cluster_id) DO UPDATE SET name = excluded.name
        """, (new_name, cluster_id))
        conn.commit()