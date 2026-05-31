# backend/server.py
import os
import sqlite3
import time
import io
import uvicorn
import threading
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from PIL import Image

from modules.index_store import DB_PATH, init_db, label_face_identity
from modules.deduplicator import run_deduplication_job

scan_status = {
    "is_scanning": False,
    "cancel_requested": False,
    "current": 0,
    "total": 0,
    "message": ""
}

# ==========================================
# GLOBAL TRACKING STATE FOR PHOTO DEDUPLICATION
# ==========================================
dedup_status = {
    "is_processing": False,
    "current": 0,
    "total": 0,
    "duplicates_found": 0,
    "message": "System idle. Input target directory folder to evaluate."
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("========================================")
    print("🚀 Booting AI Photo Manager...")
    try:
        init_db()
        print("✅ Database initialized successfully.")
    except Exception as e:
        print(f"❌ Database error during startup: {e}")
    print("========================================")
    yield
    print("Shutting down AI Photo Manager Backend...")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScanRequest(BaseModel):
    folder_path: str


class TrainRequest(BaseModel):
    face_id: int
    name: str


# Pydantic validation model for request payload mapping
class DeduplicateRequest(BaseModel):
    folder_path: str


def run_scanner_job(folder_path: str):
    global scan_status
    scan_status.update(
        {"is_scanning": True, "cancel_requested": False, "current": 0, "total": 0, "message": "Initializing..."})

    try:
        from modules.scanner import PhotoScanner
        scanner = PhotoScanner()
        scanner.status_tracker = scan_status
        scanner.scan_directory(folder_path)

        if not scan_status["cancel_requested"] and scan_status["message"] != "No images found in directory.":
            scan_status["message"] = "Scan completed successfully!"

    except Exception as e:
        print(f"Background scanner failed: {e}")
        scan_status["message"] = f"Error: {str(e)}"
    finally:
        time.sleep(2)
        scan_status["is_scanning"] = False
        scan_status["cancel_requested"] = False


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


@app.post("/api/scan/cancel")
async def cancel_scan():
    global scan_status
    if scan_status["is_scanning"]:
        scan_status["cancel_requested"] = True
    return {"status": "success", "message": "Cancel requested"}


@app.get("/api/stats")
async def get_dashboard_stats():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(id) FROM photos")
        total_photos = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(id) FROM faces")
        total_faces = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(DISTINCT event_type) FROM photos WHERE event_type IS NOT NULL AND event_type != ''")
        total_events = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(DISTINCT location_name) FROM photos WHERE location_name IS NOT NULL AND location_name != ''")
        total_locations = cursor.fetchone()[0]

        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT strftime('%Y-%m', taken_at) as period, COUNT(*) as count FROM photos WHERE taken_at IS NOT NULL GROUP BY period ORDER BY period")
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


@app.get("/api/photos")
async def get_all_photos():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT id, path, size_kb, taken_at, event_type, location_name
                       FROM photos
                       ORDER BY id DESC
                       """)
        photos = [{
            "id": r["id"],
            "path": r["path"],
            "size_kb": r["size_kb"],
            "taken_at": r["taken_at"],
            "event": r["event_type"],
            "location": r["location_name"]
        } for r in cursor.fetchall()]
        conn.close()
        return {"status": "success", "photos": photos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/faces/labeled")
async def get_labeled_faces():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT f.identity_name as name, MAX(f.id) as face_id
                       FROM faces f
                                JOIN photos p ON f.photo_id = p.id
                       WHERE f.identity_name IS NOT NULL
                         AND f.identity_name != ''
                       GROUP BY f.identity_name
                       """)
        faces = [{"name": r["name"], "image": f"/api/faces/image/{r['face_id']}"} for r in cursor.fetchall()]
        conn.close()
        return {"status": "success", "faces": faces}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/faces/unlabeled")
async def get_unlabeled_faces():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT f.id, p.path
                       FROM faces f
                                JOIN photos p ON f.photo_id = p.id
                       WHERE (f.identity_name IS NULL OR f.identity_name = '')
                         AND p.is_best_variant = 1 LIMIT 100
                       """)
        faces = [{"id": r["id"], "image": r["path"]} for r in cursor.fetchall()]
        conn.close()
        return {"status": "success", "faces": faces}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/train")
async def train_face(request: TrainRequest):
    try:
        label_face_identity(request.face_id, request.name)
        return {"status": "success", "message": "Face labeled!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/photos/deduplicate")
async def start_deduplication(payload: dict):
    target = payload.get("folder_path")
    # This triggers the function in the file we just updated
    # It will run in the background so your UI doesn't freeze
    import threading
    threading.Thread(target=run_deduplication_job, args=(target, status_tracker)).start()
    return {"message": "Deduplication started"}        


@app.delete("/api/faces/{face_id}")
async def delete_face(face_id: int):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM faces WHERE id = ?", (face_id,))
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Face deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/image")
async def serve_image(path: str):
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path)


@app.get("/api/faces/image/{face_id}")
async def serve_face_image(face_id: int):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT p.path, f.rect_x, f.rect_y, f.rect_w, f.rect_h
                       FROM faces f
                                JOIN photos p ON f.photo_id = p.id
                       WHERE f.id = ?
                       """, (face_id,))
        row = cursor.fetchone()
        conn.close()

        if not row or not os.path.exists(row["path"]):
            raise HTTPException(status_code=404, detail="Image not found")

        with Image.open(row["path"]) as img:
            left = row["rect_x"]
            top = row["rect_y"]
            right = left + row["rect_w"]
            bottom = top + row["rect_h"]

            padding = int(row["rect_w"] * 0.2)
            left = max(0, left - padding)
            top = max(0, top - padding)
            right = min(img.width, right + padding)
            bottom = min(img.height, bottom + padding)

            face_crop = img.crop((left, top, right, bottom))

            if face_crop.mode != "RGB":
                face_crop = face_crop.convert("RGB")

            buf = io.BytesIO()
            face_crop.save(buf, format="JPEG")
            buf.seek(0)

            return StreamingResponse(buf, media_type="image/jpeg")
    except Exception as e:
        print(f"Error serving cropped face: {e}")
        raise HTTPException(status_code=500, detail="Failed to load face image")


# ==========================================
# PHOTO DEDUPLICATION ROUTE TARGETS
# ==========================================
@app.get("/api/photos/deduplicate/status")
async def get_deduplication_status():
    global dedup_status
    return dedup_status


@app.post("/api/photos/deduplicate")
async def trigger_deduplication(request: DeduplicateRequest):
    if not os.path.exists(request.folder_path):
        raise HTTPException(status_code=400, detail="Target processing path does not exist.")
    if dedup_status["is_processing"]:
        raise HTTPException(status_code=400, detail="Pipeline already running.")

    # Pass the global dedup_status to the thread
    threading.Thread(target=run_deduplication_job, args=(request.folder_path, dedup_status)).start()
    return {"status": "success", "message": "Deduplication started."}


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)