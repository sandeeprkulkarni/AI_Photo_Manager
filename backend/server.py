# backend/server.py
import uvicorn
import sqlite3
import os, shutil
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from modules.index_store import init_db, DB_PATH
from modules.face_detector import extract_faces_from_file # Import the new function
from modules.index_store import save_manual_training_face

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

@app.post("/api/train")
async def train_face(name: str = Form(...), file: UploadFile = File(...)):
    # 1. Save uploaded file temporarily
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # 2. Extract faces from the single image using our new function
        faces = extract_faces_from_file(temp_path)
        
        if not faces:
            return {"status": "error", "message": "No face detected in the image. Please use a clearer photo."}

        # 3. Use the first detected face for training
        embedding = faces[0]['embedding']
        
        # 4. Save to DB (identity name and embedding)
        save_manual_training_face(name, embedding)

        return {"status": "success", "message": f"Successfully trained model for {name}"}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)