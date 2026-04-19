# backend/server.py
import uvicorn
import sqlite3
import io
import face_recognition
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from contextlib import asynccontextmanager
from modules.index_store import init_db, DB_PATH

# New Lifespan handler replaces @app.on_event("startup")
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run startup logic
    init_db()
    yield
    # Run shutdown logic if needed (e.g., closing DB connections)

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PHOTO_DIR = "E:/Photos"
app.mount("/library", StaticFiles(directory=PHOTO_DIR), name="library")

@app.get("/api/stats")
def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    photos = cursor.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
    faces = cursor.execute("SELECT COUNT(*) FROM faces").fetchone()[0]
    people = cursor.execute("SELECT COUNT(*) FROM persons").fetchone()[0]
    locs = cursor.execute("SELECT COUNT(DISTINCT location_name) FROM photos WHERE location_name IS NOT NULL").fetchone()[0]
    conn.close()
    
    return {
        "photos": photos,
        "faces": faces,
        "people": people,
        "locations": locs
    }

@app.post("/api/train")
async def train_face(name: str = Form(...), file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = face_recognition.load_image_file(io.BytesIO(contents))
        encodings = face_recognition.face_encodings(image, num_jitters=1)
        
        if not encodings:
            return {"status": "error", "message": "No face detected."}
        
        embedding_blob = encodings[0].tobytes()

        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("INSERT OR IGNORE INTO persons (name) VALUES (?)", (name,))
            person_id = conn.execute("SELECT id FROM persons WHERE name = ?", (name,)).fetchone()[0]
            conn.execute("""
                INSERT INTO faces (photo_id, embedding, cluster_id, identity_name) 
                VALUES (NULL, ?, ?, ?)
            """, (embedding_blob, person_id, name))
            conn.commit()
            
        return {"status": "success", "message": f"Trained model for {name}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)