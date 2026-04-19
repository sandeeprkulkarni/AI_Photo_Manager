# backend/server.py
import os
import sqlite3
import shutil
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import face_recognition

# Import modular components
from modules.index_store import init_db, label_face_identity, DB_PATH
from modules.recognition import RecognitionEngine
from modules.scanner import Scanner 

# --- INITIALIZATION (Must come before routes) ---
app = FastAPI(title="Local-First AI Photo Manager")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

rec_engine = RecognitionEngine()

class FaceLabelRequest(BaseModel):
    face_id: int
    name: str

# --- LIFESPAN EVENTS ---
@app.on_event("startup")
async def startup_event():
    init_db()
    await rec_engine.load_training_data()

# --- ROUTES ---

@app.get("/api/stats")
async def get_stats():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM photos")
            total_photos = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM faces")
            total_faces = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM faces WHERE identity_name IS NOT NULL")
            labeled_faces = cursor.fetchone()[0]
            
            return {
                "total_photos": total_photos,
                "total_faces": total_faces,
                "labeled_faces": labeled_faces,
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/train")
async def train_new_face(
    name: str = Form(...), 
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """Handles multipart/form-data for manual training uploads."""
    temp_path = Path(f"data/temp_{file.filename}")
    try:
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        image = face_recognition.load_image_file(temp_path)
        encodings = face_recognition.face_encodings(image)

        if not encodings:
            raise HTTPException(status_code=400, detail="No face detected")

        embedding = encodings[0].tobytes()

        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO faces (photo_id, embedding, identity_name, cluster_id) 
                VALUES (?, ?, ?, ?)
            """, (-1, embedding, name, -1))
            conn.commit()

        await rec_engine.load_training_data()
        if background_tasks:
            background_tasks.add_task(rec_engine.update_unlabeled_faces)

        return {"status": "success"}
    finally:
        if temp_path.exists():
            temp_path.unlink()

@app.post("/api/faces/label")
async def label_existing_face(data: FaceLabelRequest, background_tasks: BackgroundTasks):
    """Handles JSON requests for labeling indexed faces."""
    label_face_identity(data.face_id, data.name)
    await rec_engine.load_training_data()
    background_tasks.add_task(rec_engine.update_unlabeled_faces)
    return {"status": "success"}

@app.get("/api/scan")
async def start_scan(path: str, background_tasks: BackgroundTasks):
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Path not found")
    scanner_instance = Scanner(path)
    background_tasks.add_task(scanner_instance.scan)
    return {"status": "scanning", "path": path}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)