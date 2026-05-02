import os
import sqlite3
import time
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Import from your modules
from modules.index_store import DB_PATH, init_db, label_face_identity

# --- Global State for Scanning Progress ---
scan_status = {
    "is_scanning": False,
    "current": 0,
    "total": 0,
    "message": ""
}

# 1. Setup Lifespan (Ensures Database is created before server starts!)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("========================================")
    print("🚀 Booting AI Photo Manager...")
    try:
        init_db() # Forces the creation of data/db/index.db and all tables
        print("✅ Database initialized successfully.")
    except Exception as e:
        print(f"❌ Database error during startup: {e}")
    print("========================================")
    yield
    print("Shutting down AI Photo Manager Backend...")

app = FastAPI(lifespan=lifespan)

# 2. CORS Middleware
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
    """Runs the scanner in the background and updates the global status."""
    global scan_status
    scan_status.update({"is_scanning": True, "current": 0, "total": 0, "message": "Initializing..."})
    
    try:
        from modules.scanner import PhotoScanner
        scanner = PhotoScanner()
        scanner.status_tracker = scan_status # Inject progress tracker
        scanner.scan_directory(folder_path)
        
        if scan_status["message"] != "No images found in directory.":
            scan_status["message"] = "Scan completed successfully!"
            
    except Exception as e:
        print(f"Background scanner failed: {e}")
        scan_status["message"] = f"Error: {str(e)}"
    finally:
        # Pause for 2 seconds so the React UI has time to catch the 100% state
        time.sleep(2)
        scan_status["is_scanning"] = False

# --- API Endpoints ---
@app.get("/api/scan/status")
async def get_scan_status():
    return scan_status

@app.post("/api/scan")
async def start_folder_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    global scan_status
    if not os.path.exists(request.folder_path):
        raise HTTPException(status_code=400, detail="Directory does not exist.")
    if scan_status["is_scanning"]:
        raise HTTPException(status_code=400, detail="Scan in progress.")
    
    background_tasks.add_task(run_scanner_job, request.folder_path)
    return {"status": "success"}

@app.get("/api/stats")
async def get_dashboard_stats():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(id) FROM photos")
        total_photos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(id) FROM faces")
        total_faces = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT event_type) FROM photos WHERE event_type IS NOT NULL AND event_type != ''")
        total_events = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT location_name) FROM photos WHERE location_name IS NOT NULL AND location_name != ''")
        total_locations = cursor.fetchone()[0]
        
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT strftime('%Y-%m', taken_at) as period, COUNT(*) as count FROM photos WHERE taken_at IS NOT NULL GROUP BY period ORDER BY period")
        chart_data = [{"name": row["period"], "photos": row["count"]} for row in cursor.fetchall()]
        
        conn.close()
        return {
            "totalPhotos": total_photos,
            "facesFound": total_faces,
            "events": total_events,
            "locations": total_locations,
            "chartData": chart_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/faces/labeled")
async def get_labeled_faces():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.identity_name as name, MIN(p.path) as sample_image
            FROM faces f JOIN photos p ON f.photo_id = p.id
            WHERE f.identity_name IS NOT NULL AND f.identity_name != ''
            GROUP BY f.identity_name
        """)
        faces = [{"name": r["name"], "image": r["sample_image"]} for r in cursor.fetchall()]
        conn.close()
        return {"status": "success", "faces": faces}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/faces/unlabeled")
async def get_unlabeled_faces():
    """Fetches faces without names for the UI to train."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.id, p.path 
            FROM faces f JOIN photos p ON f.photo_id = p.id
            WHERE f.identity_name IS NULL OR f.identity_name = ''
            LIMIT 50
        """)
        faces = [{"id": r["id"], "image": r["path"]} for r in cursor.fetchall()]
        conn.close()
        return {"status": "success", "faces": faces}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/train")
async def train_face(request: TrainRequest):
    """Uses your index_store logic to name a face."""
    try:
        label_face_identity(request.face_id, request.name)
        return {"status": "success", "message": "Face labeled!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/image")
async def serve_image(path: str):
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path)

# =====================================================================
# STARTUP BLOCK 
# =====================================================================
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)