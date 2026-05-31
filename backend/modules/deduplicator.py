# backend/modules/deduplicator.py
import os
import sqlite3
import cv2
import re
import numpy as np
from datetime import datetime
from config import DB_PATH


def parse_flexible_timestamp(timestamp_str: str) -> datetime:
    """
    Safely converts variable database timestamp formats into Python datetimes.
    Handles space delimiters, sub-seconds, and timezone symbols without crashing.
    """
    if not timestamp_str:
        return datetime.min
    try:
        # Standardize formatting by substituting delimiters
        normalized = re.sub(r'[T_Z]', ' ', timestamp_str).split('.')[0].strip()
        # Clean colons out of dates if written as YYYY:MM:DD
        if len(normalized) >= 10 and normalized[4] == ':' and normalized[7] == ':':
            normalized = normalized[:4] + '-' + normalized[5:7] + '-' + normalized[8:]
        return datetime.strptime(normalized, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.min


def calculate_blur_score(image_path: str) -> float:
    """Calculates image sharpness using the variance of the Laplacian method."""
    try:
        if not os.path.exists(image_path):
            return 0.0
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return 0.0
        return float(cv2.Laplacian(img, cv2.CV_64F).var())
    except Exception:
        return 0.0


def calculate_light_score(image_path: str) -> float:
    """Evaluates photo contrast balancing by scoring pixel deviations from absolute middle gray."""
    try:
        if not os.path.exists(image_path):
            return 0.0
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return 0.0
        mean_brightness = np.mean(img)
        return float(127.0 - abs(127.0 - mean_brightness))
    except Exception:
        return 0.0


def run_deduplication_job(target_folder: str, status_tracker: dict):
    """
    Scans internal indexed pictures inside a given folder, pairs chronological
    near-captures together, ranks their physical quality values, and flags duplicates.
    """
    status_tracker.update({
        "is_processing": True,
        "current": 0,
        "total": 0,
        "duplicates_found": 0,
        "message": "Initializing photo sorting job..."
    })

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Retrieve only photos residing inside the user-specified input directory
            cursor.execute("""
                           SELECT id,
                                  path,
                                  taken_at,
                                  location_name,
                                  (SELECT COUNT(*) FROM faces WHERE photo_id = photos.id) as face_count
                           FROM photos
                           WHERE path LIKE ?
                             AND taken_at IS NOT NULL
                           ORDER BY taken_at ASC
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

            # Reset prior evaluation state within this execution workspace directory
            conn.execute("""
                         UPDATE photos
                         SET duplicate_group_id = NULL,
                             is_best_variant    = 1
                         WHERE path LIKE ?
                         """, (f"{target_folder}%",))
            conn.commit()

            groups = []
            if total_count > 0:
                current_group = [photos[0]]

                # Sequential time-burst aggregation loop
                for i in range(1, total_count):
                    prev = photos[i - 1]
                    curr = photos[i]

                    t1 = parse_flexible_timestamp(prev['taken_at'])
                    t2 = parse_flexible_timestamp(curr['taken_at'])

                    if t1 == datetime.min or t2 == datetime.min:
                        time_delta = 99999.0
                    else:
                        time_delta = abs((t2 - t1).total_seconds())

                    same_loc = prev['location_name'] == curr['location_name']

                    # Consider photos duplicates if captured within 45 seconds at the same location
                    if time_delta <= 45.0 and same_loc:
                        current_group.append(curr)
                    else:
                        if len(current_group) > 1:
                            groups.append(current_group)
                        current_group = [curr]

                if len(current_group) > 1:
                    groups.append(current_group)

            # Evaluate each duplicate group
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

                    # Unified multi-parameter quality metrics calculation formula
                    location_weight = 60.0 if item['location_name'] else 0.0
                    people_weight = float(item['face_count'] * 40.0)
                    blur_weight = float(blur * 0.15)
                    light_weight = float(light * 0.5)

                    total_score = location_weight + people_weight + blur_weight + light_weight

                    # Downgrade item to a hidden duplicate variant
                    conn.execute("""
                                 UPDATE photos
                                 SET duplicate_group_id = ?,
                                     is_best_variant    = 0
                                 WHERE id = ?
                                 """, (group_id, item['id']))
                    duplicate_counter += 1

                    if total_score > highest_score:
                        highest_score = total_score
                        best_photo_id = item['id']

                # Restore and elevate the high-scoring champion photo of this cluster group
                if best_photo_id:
                    conn.execute("UPDATE photos SET is_best_variant = 1 WHERE id = ?", (best_photo_id,))
                    duplicate_counter -= 1  # Subtract the single retained photo

                status_tracker["duplicates_found"] = duplicate_counter
                conn.commit()

            status_tracker.update({
                "message": f"Deduplication complete! Isolated {duplicate_counter} low-quality duplicate photos.",
                "current": total_count
            })

    except Exception as e:
        status_tracker["message"] = f"Pipeline execution failure: {str(e)}"
    finally:
        status_tracker["is_processing"] = False