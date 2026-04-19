# backend/server.py
import os
import sqlite3
import shutil
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import face_recognition

# Import modular components
from modules.index_store import init_db, label_face_identity, DB_PATH
from modules.recognition import RecognitionEngine
from modules.scanner import Scanner 

# --- LIFESPAN HANDLER (Replaces on_event) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    init_db()
    # We initialize the engine here so it's accessible via app.state
    app.state.rec_engine = RecognitionEngine()
    await app.state.rec_engine.load_training_data()
    print("🚀 Backend Startup: Database initialized and Recognition Engine loaded.")
    yield
    # Shutdown logic (if any) goes here
    print("🛑 Backend Shutdown: Cleaning up resources.")

# --- INITIALIZATION ---
app = FastAPI(title="Local-First AI Photo Manager", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class FaceLabelRequest(BaseModel):
    face_id: int
    name: str

# --- ROUTES ---

@app.get("/api/stats")
async def get_stats():
    """Provides overview data for the Dashboard."""
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
    background_tasks: BackgroundTasks,
    name: str = Form(...), 
    file: UploadFile = File(...)
):
    """Handles manual training uploads via multipart/form-data."""
    temp_path = Path(f"data/temp_{file.filename}")
    try:
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Load image and attempt detection
        image = face_recognition.load_image_file(temp_path)
        
        # We upsample once (number_of_times_to_upsample=1) to help find smaller or less clear faces
        # This helps reduce the "400 Bad Request - No face detected" error
        encodings = face_recognition.face_encodings(image, num_jitters=1)

        if not encodings:
            # Throwing 400 specifically when the image is clear but no face is found
            raise HTTPException(status_code=400, detail=f"No face detected in {file.filename}. Please try a clearer front-facing photo.")

        embedding = encodings[0].tobytes()

        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO faces (photo_id, embedding, identity_name, cluster_id) 
                VALUES (?, ?, ?, ?)
            """, (-1, embedding, name, -1))
            conn.commit()

        # Reload engine from app state
        await app.state.rec_engine.load_training_data()
        background_tasks.add_task(app.state.rec_engine.update_unlabeled_faces)

        return {"status": "success", "message": f"Trained identity for {name}"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path.exists():
            temp_path.unlink()

@app.post("/api/faces/label")
async def label_existing_face(data: FaceLabelRequest, background_tasks: BackgroundTasks):
    label_face_identity(data.face_id, data.name)
    await app.state.rec_engine.load_training_data()
    background_tasks.add_task(app.state.rec_engine.update_unlabeled_faces)
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