# backend/server.py
import uvicorn
import sqlite3
import numpy as np
import face_recognition
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from modules.index_store import init_db, DB_PATH

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Replace with your actual library path
PHOTO_DIR = "E:/Photos"
app.mount("/library", StaticFiles(directory=PHOTO_DIR), name="library")

@app.on_event("startup")
def startup():
    init_db()
    
@app.get("/api/faces/unlabeled")
async def get_unlabeled_faces():
    """Fetches faces detected but not yet named."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, face_path, cluster_id FROM faces WHERE identity_name IS NULL AND photo_id != -1")
            return [{"id": f[0], "url": f"/library/{f[1]}", "cluster": f[2]} for f in cursor.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/train")
async def train_new_face(name: str = Form(...), file: UploadFile = File(...)):
    # ... Face encoding and SQL INSERT logic ...
    return {"status": "success", "message": f"Trained identity for {name}"}

@app.get("/api/faces/unlabeled")
async def get_unlabeled_faces():
    """Fetches faces that have been detected but not yet named."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # photo_id != -1 filters out manual training samples
            cursor.execute("""
                SELECT id, face_path, cluster_id 
                FROM faces 
                WHERE identity_name IS NULL AND photo_id != -1
                LIMIT 100
            """)
            faces = cursor.fetchall()
            return [
                {"id": f[0], "url": f"/library/{f[1]}", "cluster": f[2]} 
                for f in faces
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))    

@app.get("/api/stats")
def get_stats():
    conn = sqlite3.connect(DB_PATH)
    photos = conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
    faces = conn.execute("SELECT COUNT(*) FROM faces").fetchone()[0]
    locs = conn.execute("SELECT COUNT(DISTINCT location_name) FROM photos WHERE location_name IS NOT NULL").fetchone()[0]
    evts = conn.execute("SELECT COUNT(DISTINCT event_type) FROM photos WHERE event_type IS NOT NULL").fetchone()[0]
    conn.close()
    return {"photos": photos, "faces": faces, "locations": locs, "events": evts}

# --- NEW: Face Identity Training Endpoint ---
@app.post("/api/train")
async def train_identity(name: str = Form(...), file: UploadFile = File(...)):
    try:
        # 1. Load the uploaded image
        image = face_recognition.load_image_file(file.file)
        
        # 2. Extract face encoding (embedding)
        encodings = face_recognition.face_encodings(image)
        
        if not encodings:
            raise HTTPException(status_code=400, detail="No face detected in the photo.")
        
        embedding = encodings[0]
        embedding_blob = embedding.tobytes()

        # 3. Save to Database
        conn = sqlite3.connect(DB_PATH)
        # Create a unique cluster_id for this person (using timestamp as a simple ID)
        import time
        cluster_id = int(time.time())
        
        # Add to persons table
        conn.execute("INSERT INTO persons (name, cluster_id) VALUES (?, ?)", (name, cluster_id))
        
        # Add a reference face to the faces table for future matching
        conn.execute("""
            INSERT INTO faces (photo_id, embedding, cluster_id) 
            VALUES (?, ?, ?)
        """, (-1, embedding_blob, cluster_id)) # photo_id -1 indicates a training sample
        
        conn.commit()
        conn.close()
        
        return {"status": "success", "message": f"Successfully trained identity for {name}"}
        
    except Exception as e:
        print(f"Training Error: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)