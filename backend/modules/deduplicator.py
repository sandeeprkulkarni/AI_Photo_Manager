# backend/modules/deduplicator.py
import os
import sqlite3
import cv2
import numpy as np
import imagehash
from PIL import Image
from datetime import datetime
from config import DB_PATH

def get_image_hash(image_path: str):
    """Generates a perceptual hash to detect near-duplicates."""
    try:
        if not os.path.exists(image_path):
            return None
        with Image.open(image_path) as img:
            return imagehash.phash(img)
    except Exception:
        return None

def run_deduplication_job(target_folder: str, status_tracker: dict):
    """
    Scans internal indexed pictures, uses pHash for content-based duplicate detection,
    and ranks quality.
    """
    status_tracker.update({
        "is_processing": True,
        "current": 0,
        "total": 0,
        "duplicates_found": 0,
        "message": "Initializing content-aware duplicate scan..."
    })

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Removed 'taken_at IS NOT NULL' to include metadata-stripped images
            cursor.execute("""
                           SELECT id, path, location_name,
                                  (SELECT COUNT(*) FROM faces WHERE photo_id = photos.id) as face_count
                           FROM photos
                           WHERE path LIKE ?
                           """, (f"{target_folder}%",))

            photos = cursor.fetchall()
            total_count = len(photos)
            status_tracker["total"] = total_count

            if total_count == 0:
                status_tracker.update({
                    "is_processing": False,
                    "message": "No indexed photographs match the provided file path."
                })
                return

            # Grouping by content similarity
            hash_map = {}
            for photo in photos:
                img_hash = get_image_hash(photo['path'])
                if img_hash:
                    # Grouping images with similar hashes (Hamming distance < 4)
                    found_group = False
                    for existing_hash, group in hash_map.items():
                        if img_hash - existing_hash < 4:
                            group.append(photo)
                            found_group = True
                            break
                    if not found_group:
                        hash_map[img_hash] = [photo]

            # Process groups
            duplicate_counter = 0
            for group_id_base, group in enumerate(hash_map.values()):
                if len(group) > 1:
                    group_id = f"ai_content_dup_{group_id_base}_{int(datetime.now().timestamp())}"
                    best_photo_id = None
                    highest_score = -1.0

                    for item in group:
                        status_tracker["current"] += 1
                        # Quality calculation remains consistent
                        score = (60.0 if item['location_name'] else 0.0) + (item['face_count'] * 40.0)
                        
                        conn.execute("""
                                     UPDATE photos
                                     SET duplicate_group_id = ?,
                                         is_best_variant    = 0
                                     WHERE id = ?
                                     """, (group_id, item['id']))
                        duplicate_counter += 1

                        if score > highest_score:
                            highest_score = score
                            best_photo_id = item['id']

                    if best_photo_id:
                        conn.execute("UPDATE photos SET is_best_variant = 1 WHERE id = ?", (best_photo_id,))
                        duplicate_counter -= 1

                    conn.commit()

            status_tracker.update({
                "message": f"Deduplication complete! Isolated {duplicate_counter} visual duplicates.",
                "current": total_count
            })

    except Exception as e:
        status_tracker["message"] = f"Pipeline execution failure: {str(e)}"
    finally:
        status_tracker["is_processing"] = False