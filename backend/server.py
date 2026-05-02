import os
import sqlite3
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Import from your modules
from modules.index_store import DB_PATH

# 1. Setup Lifespan (Replaces the deprecated on_event("startup"))
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up AI Photo Manager Backend...")
    # Add any startup logic here (e.g., checking DB connection)
    yield
    print("Shutting down AI Photo Manager Backend...")

app = FastAPI(lifespan=lifespan)

# 2. CORS Middleware (Allows React to communicate with FastAPI)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class ScanRequest(BaseModel):
    folder_path: str

class TrainRequest(BaseModel):
    face_id: int
    name: str

# --- Background Task Functions ---
def run_scanner_job(folder_path: str):
    """Runs the scanner in the background so the UI doesn't freeze."""
    try:
        from modules.scanner import scan_directory # Adjust if your import/function name differs
        print(f"Starting background scan for: {folder_path}")
        scan_directory(folder_path)
        print("Scan completed successfully!")
    except Exception as e:
        print(f"Background scanner failed: {e}")


# --- API Endpoints ---

@app.post("/api/scan")
async def start_folder_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    Triggers the scanner as a background task.
    """
    if not os.path.exists(request.folder_path):
        raise HTTPException(status_code=400, detail="Directory does not exist.")
    
    # Add the scan to background tasks and return immediately to React
    background_tasks.add_task(run_scanner_job, request.folder_path)
    
    return {
        "status": "success", 
        "message": f"Scanning started in the background for {request.folder_path}"
    }

@app.get("/api/faces/labeled")
async def get_labeled_faces():
    """
    Retrieves a unique list of labeled faces with a sample image for each.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # CORRECTED SQL: Joins the 'faces' and 'photos' tables to get the path
        cursor.execute("""
            SELECT f.identity_name as name, MIN(p.path) as sample_image
            FROM faces f
            JOIN photos p ON f.photo_id = p.id
            WHERE f.identity_name IS NOT NULL AND f.identity_name != ''
            GROUP BY f.identity_name
        """)
        
        rows = cursor.fetchall()
        labeled_faces = [{"name": row["name"], "image": row["sample_image"]} for row in rows]
        
        conn.close()
        return {"status": "success", "faces": labeled_faces}
    except Exception as e:
        print(f"Database error in /api/faces/labeled: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/image")
async def serve_image(path: str):
    """
    Serves local image files to the React frontend securely.
    Required because browsers block direct access to local C:/ or /Users/ paths.
    """
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path)


# =====================================================================
# YOUR EXISTING ROUTES: Paste your logic for these inside the functions
# =====================================================================

@app.get("/api/faces/unlabeled")
async def get_unlabeled_faces():
    """
    PASTE YOUR EXISTING UNLABELED FACES LOGIC HERE
    """
    pass 

@app.post("/api/train")
async def train_face(request: TrainRequest):
    """
    PASTE YOUR EXISTING FACE TRAINING LOGIC HERE
    """
    pass