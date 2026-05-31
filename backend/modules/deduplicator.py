# backend/modules/deduplicator.py
import os
import sqlite3
import cv2
import re
import numpy as np
from datetime import datetime
from modules.index_store import DB_PATH

def parse_flexible_timestamp(timestamp_str: str) -> datetime:
    """Safely converts database timestamps into Python datetimes."""
    if not timestamp_str:
        return datetime.min
    try:
        normalized = re.sub(r'[T_Z]', ' ', timestamp_str).split('.')[0].strip()
        if len(normalized) >= 10 and normalized[4] == ':' and normalized[7] == ':':
            normalized = normalized[:4] + '-' + normalized[5:7] + '-' + normalized[8:]
        return datetime.strptime(normalized, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.min

def calculate_blur_score(image_path: str) -> float:
    try:
        if not os.path.exists(image_path): return 0.0
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None: return 0.0
        return float(cv2.Laplacian(img, cv2.CV_64F).var())
    except Exception:
        return 0.0

def calculate_light_score(image_path: str) -> float:
    try:
        if not os.path.exists(image_path): return 0.0
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None: return 0.0
        mean_brightness = np.mean(img)
        return float(127.0 - abs(127.0 - mean_brightness))
    except Exception:
        return 0.0

def check_visual_duplicate(path1: str, path2: str) -> bool:
    """Uses OpenCV to determine if two images are exact or near-exact visual matches."""
    try:
        if not os.path.exists(path1) or not os.path.exists(path2): return False
        img1 = cv2.imread(path1, cv2.IMREAD_GRAYSCALE)
        img2 = cv2.imread(path2, cv2.IMREAD_GRAYSCALE)
        if img1 is None or img2 is None: return False
        
        # Resize to a 32x32 thumbnail for extremely fast perceptual comparison
        img1 = cv2.resize(img1, (32, 32))
        img2 = cv2.resize(img2, (32, 32))
        diff = cv2.absdiff(img1, img2)
        return float(np.mean(diff)) < 3.0
    except Exception:
        return False

def run_deduplication_job(target_folder: str, status_tracker: dict):
    status_tracker.update({
        "is_processing": True,
        "current": 0,
        "total": 0,
        "duplicates_found": 0,
        "message": "Initializing AI Visual duplicate scan..."
    })

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # FIX: Resilient path matching for Windows (\) and Mac/Linux (/)
            folder_win = target_folder.replace('/', '\\')
            folder_unix = target_folder.replace('\\', '/')

            # FIX: Using %wildcards% so it matches regardless of absolute path formatting
            cursor.execute("""
                SELECT id, path, taken_at, location_name, size_kb, hash,
                       (SELECT COUNT(*) FROM faces WHERE photo_id = photos.id) as face_count
                FROM photos
                WHERE path LIKE ? OR path LIKE ?
                ORDER BY taken_at ASC, path ASC
            """, (f"%{folder_win}%", f"%{folder_unix}%"))
            
            photos = cursor.fetchall()
            total_count = len(photos)
            status_tracker["total"] = total_count

            if total_count == 0:
                status_tracker.update({
                    "is_processing": False,
                    "message": "No photos found. Ensure you ran the 'Scanner' on this exact folder first!"
                })
                return

            cursor.execute("""
                UPDATE photos 
                SET duplicate_group_id = NULL, is_best_variant = 1 
                WHERE path LIKE ? OR path LIKE ?
            """, (f"%{folder_win}%", f"%{folder_unix}%"))
            conn.commit()

            groups = []
            if total_count > 0:
                current_group = [photos[0]]

                for i in range(1, total_count):
                    prev = photos[i - 1]
                    curr = photos[i]

                    t1 = parse_flexible_timestamp(prev['taken_at'])
                    t2 = parse_flexible_timestamp(curr['taken_at'])
                    
                    is_duplicate = False

                    # 1. AI FALLBACK: Exact Database File Hash Match (Ignores Naming Entirely)
                    if prev['hash'] and curr['hash'] and prev['hash'] == curr['hash']:
                        is_duplicate = True
                        
                    # 2. EXIF Duplicate logic (within 45s at same location)
                    elif t1 != datetime.min and t2 != datetime.min:
                        time_delta = abs((t2 - t1).total_seconds())
                        same_loc = prev['location_name'] == curr['location_name']
                        if time_delta <= 45.0 and same_loc:
                            is_duplicate = True
                            
                    # 3. AI FALLBACK: Same file size or OpenCV visual match (For WhatsApp Forwards)
                    if not is_duplicate:
                        if prev['size_kb'] and prev['size_kb'] == curr['size_kb']:
                            is_duplicate = True
                        elif check_visual_duplicate(prev['path'], curr['path']):
                            is_duplicate = True

                    if is_duplicate:
                        current_group.append(curr)
                    else:
                        if len(current_group) > 1:
                            groups.append(current_group)
                        current_group = [curr]

                if len(current_group) > 1:
                    groups.append(current_group)

            duplicate_counter = 0
            for idx, group in enumerate(groups):
                group_id = f"ai_burst_{idx}_{int(datetime.now().timestamp())}"
                best_photo_id = None
                highest_score = -1.0

                status_tracker["message"] = f"Evaluating quality in cluster {idx + 1} of {len(groups)}..."

                for item in group:
                    status_tracker["current"] += 1
                    
                    blur = calculate_blur_score(item['path'])
                    light = calculate_light_score(item['path'])

                    location_weight = 60.0 if item['location_name'] else 0.0
                    people_weight = float(item['face_count'] * 40.0)
                    blur_weight = float(blur * 0.15)
                    light_weight = float(light * 0.5)

                    total_score = location_weight + people_weight + blur_weight + light_weight

                    conn.execute("""
                        UPDATE photos 
                        SET duplicate_group_id = ?, is_best_variant = 0 
                        WHERE id = ?
                    """, (group_id, item['id']))
                    duplicate_counter += 1

                    if total_score > highest_score:
                        highest_score = total_score
                        best_photo_id = item['id']

                # Elevate the highest quality version
                if best_photo_id:
                    conn.execute("UPDATE photos SET is_best_variant = 1 WHERE id = ?", (best_photo_id,))
                    duplicate_counter -= 1 

                status_tracker["duplicates_found"] = duplicate_counter
                conn.commit()

            status_tracker.update({
                "message": f"Deduplication complete! Isolated {duplicate_counter} duplicate photos.",
                "current": total_count
            })

    except Exception as e:
        status_tracker["message"] = f"Pipeline execution failure: {str(e)}"
    finally:
        status_tracker["is_processing"] = False