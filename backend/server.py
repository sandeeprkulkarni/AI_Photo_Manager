# backend/server.py
import uvicorn
import sqlite3
import os, shutil
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pathlib import Path
from PIL import Image, ImageOps
import io

from modules.index_store import init_db, DB_PATH
from modules.face_detector import extract_faces_from_file, extract_faces
from modules.scanner import Scanner
from modules.index_store import save_manual_training_face, label_face_identity
from config import PHOTO_DIR

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/library", StaticFiles(directory=PHOTO_DIR), name="library")

@app.on_event("startup")
def startup():
    init_db()

# --- NEW: Trigger a Library Scan ---
@app.post("/api/scan")
async def scan_library():
    """Scans the folder for new photos and extracts faces."""
    try:
        scanner = Scanner(PHOTO_DIR)
        scanner.scan()
        extract_faces(use_cnn=False) # Process un-scanned photos
        return {"status": "success", "message": "Library scanned successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/faces/unlabeled")
async def get_unlabeled_faces():
    """Fetches faces that have been detected but not yet named."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # REMOVED face_path. We now just send the ID.
            cursor.execute("""
                SELECT id, cluster_id 
                FROM faces 
                WHERE identity_name IS NULL AND photo_id != -1
                LIMIT 100
            """)
            faces = cursor.fetchall()
            return [
                {"id": f[0], "url": f"/api/faces/{f[0]}/image", "cluster": f[1]} 
                for f in faces
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))    

# --- NEW: Dynamic Face Cropping ---
@app.get("/api/faces/{face_id}/image")
async def get_face_image(face_id: int):
    """Dynamically crops the face from the original image and serves it."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("""
                SELECT p.path, f.rect_x, f.rect_y, f.rect_w, f.rect_h 
                FROM faces f 
                JOIN photos p ON f.photo_id = p.id 
                WHERE f.id = ?
            """, (face_id,))
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Face not found")
                
            path, x, y, w, h = row
            
            # Open, fix orientation, and crop
            img = Image.open(path)
            img = ImageOps.exif_transpose(img)
            face_img = img.crop((x, y, x + w, y + h))
            
            # Save to memory buffer and serve
            buf = io.BytesIO()
            face_img.save(buf, format="JPEG")
            buf.seek(0)
            
            return StreamingResponse(buf, media_type="image/jpeg")
            
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
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        faces = extract_faces_from_file(temp_path)
        if not faces:
            return {"status": "error", "message": "No face detected in the image."}

        embedding = faces[0]['embedding']
        save_manual_training_face(name, embedding)

        return {"status": "success", "message": f"Successfully trained model for {name}"}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
# --- NEW: Assign Name to Existing Face ---
@app.post("/api/faces/{face_id}/label")
async def label_existing_face(face_id: int, name: str = Form(...)):
    """Assigns a typed name to a face already in the database."""
    try:
        label_face_identity(face_id, name)
        return {"status": "success", "message": f"Successfully assigned name: {name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)