import os
import sqlite3
import uvicorn  # <-- NEW: Required to run the server
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Import from your modules
from modules.index_store import DB_PATH

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
    """Runs the scanner in the background so the UI doesn't freeze."""
    try:
        from modules.scanner import scan_directory
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
        
        # 1. Total Photos
        cursor.execute("SELECT COUNT(id) FROM photos")
        total_photos = cursor.fetchone()[0]
        
        # 2. Total Faces Found
        cursor.execute("SELECT COUNT(id) FROM faces")
        total_faces = cursor.fetchone()[0]
        
        # 3. Total Events
        cursor.execute("SELECT COUNT(DISTINCT event_type) FROM photos WHERE event_type IS NOT NULL AND event_type != ''")
        total_events = cursor.fetchone()[0]
        
        # 4. Total Locations
        cursor.execute("SELECT COUNT(DISTINCT location_name) FROM photos WHERE location_name IS NOT NULL AND location_name != ''")
        total_locations = cursor.fetchone()[0]
        
        # 5. Chart Data: Photos grouped by Month/Year
        # SQLite's strftime extracts the Year-Month (e.g., '2023-10') from the taken_at DATETIME
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT strftime('%Y-%m', taken_at) as period, COUNT(*) as count 
            FROM photos 
            WHERE taken_at IS NOT NULL 
            GROUP BY period 
            ORDER BY period
        """)
        
        # Format specifically for Recharts in React: [{name: "2023-10", photos: 45}, ...]
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
# YOUR EXISTING ROUTES
# =====================================================================

@app.get("/api/faces/unlabeled")
async def get_unlabeled_faces():
    # Replace with your logic
    pass 

@app.post("/api/train")
async def train_face(request: TrainRequest):
    # Replace with your logic
    pass


# =====================================================================
# STARTUP BLOCK (This is what was missing!)
# =====================================================================
if __name__ == "__main__":
    # This block tells Python to actually start the web server on port 8000
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)