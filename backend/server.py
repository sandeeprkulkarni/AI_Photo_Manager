import os
import sqlite3
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Import from your modules
from modules.index_store import DB_PATH

# --- Global State for Scanning Progress ---
scan_status = {
    "is_scanning": False,
    "current": 0,
    "total": 0,
    "message": ""
}

# 1. Setup Lifespan 
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("========================================")
    print("🚀 AI Photo Manager Backend is running! ")
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
    scan_status.update({
        "is_scanning": True, 
        "current": 0, 
        "total": 0, 
        "message": "Initializing and counting files..."
    })
    
    try:
        from modules.scanner import PhotoScanner
        print(f"Starting background scan for: {folder_path}")
        
        scanner = PhotoScanner()
        
        # INJECT THE TRACKER: Passes the global dictionary into the scanner class
        # so the scanner can update the React UI without breaking its own logic.
        scanner.status_tracker = scan_status
        
        scanner.scan_directory(folder_path)
        
        scan_status["message"] = "Scan completed successfully!"
        print("Scan completed successfully!")
    except Exception as e:
        print(f"Background scanner failed: {e}")
        scan_status["message"] = f"Error: {str(e)}"
    finally:
        # Mark as finished after a brief delay so the UI hits 100% before disappearing
        scan_status["is_scanning"] = False


# --- API Endpoints ---

@app.get("/api/scan/status")
async def get_scan_status():
    """Allows the React frontend to check scan progress."""
    return scan_status

@app.post("/api/scan")
async def start_folder_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    Triggers the scanner as a background task.
    """
    global scan_status
    if not os.path.exists(request.folder_path):
        raise HTTPException(status_code=400, detail="Directory does not exist.")
    
    if scan_status["is_scanning"]:
        raise HTTPException(status_code=400, detail="A scan is already in progress.")
    
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
    """
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path)

@app.get("/api/stats")
async def get_dashboard_stats():
    """
    Returns aggregate statistics for the React Dashboard.
    """
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
        cursor.execute("""
            SELECT strftime('%Y-%m', taken_at) as period, COUNT(*) as count 
            FROM photos 
            WHERE taken_at IS NOT NULL 
            GROUP BY period 
            ORDER BY period
        """)
        
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
        print(f"Stats Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stats")

# =====================================================================
# YOUR EXISTING UNLABELED / TRAIN ROUTES
# =====================================================================

@app.get("/api/faces/unlabeled")
async def get_unlabeled_faces():
    # Paste your logic here
    pass 

@app.post("/api/train")
async def train_face(request: TrainRequest):
    # Paste your logic here
    pass


# =====================================================================
# STARTUP BLOCK 
# =====================================================================
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)