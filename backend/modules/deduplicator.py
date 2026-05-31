# backend/modules/deduplicator.py
import sqlite3
import cv2
import numpy as np
from datetime import datetime
from config import DB_PATH


def calculate_blur_score(image_path: str) -> float:
    """Calculates image sharpness using variance of the Laplacian method."""
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return 0.0
        # A higher score indicates sharper focus (less blur)
        return float(cv2.Laplacian(img, cv2.CV_64F).var())
    except Exception:
        return 0.0


def calculate_light_score(image_path: str) -> float:
    """Evaluates lighting quality by penalizing under-exposure and over-exposure."""
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return 0.0
        mean_brightness = np.mean(img)
        # Optimal balanced middle exposure is around 127
        return float(127.0 - abs(127.0 - mean_brightness))
    except Exception:
        return 0.0


def process_duplicates_and_triage():
    """
    Groups items captured inside short intervals (within 45 seconds) at identical spots,
    compares quality parameters, and flags the optimal capture to keep active.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Pull all images to evaluate chronologically
        cursor.execute("""
                       SELECT p.id,
                              p.path,
                              p.taken_at,
                              p.location_name,
                              (SELECT COUNT(*) FROM faces f WHERE f.photo_id = p.id) as face_count
                       FROM photos p
                       WHERE p.taken_at IS NOT NULL
                       ORDER BY p.taken_at ASC
                       """)
        photos = cursor.fetchall()

        if not photos:
            return

        groups = []
        current_group = [photos[0]]

        # Group near-duplicate bursts
        for i in range(1, len(photos)):
            prev = photos[i - 1]
            curr = photos[i]

            try:
                t1 = datetime.strptime(prev['taken_at'].split(".")[0], "%Y-%m-%d %H:%M:%S")
                t2 = datetime.strptime(curr['taken_at'].split(".")[0], "%Y-%m-%d %H:%M:%S")
                time_delta = abs((t2 - t1).total_seconds())
            except Exception:
                time_delta = 9999

            same_loc = prev['location_name'] == curr['location_name']

            # If taken within 45s at the same venue, count as part of a duplicate cluster group
            if time_delta <= 45 and same_loc:
                current_group.append(curr)
            else:
                if len(current_group) > 1:
                    groups.append(current_group)
                current_group = [curr]

        if len(current_group) > 1:
            groups.append(current_group)

        # Score elements inside duplicate sets
        for idx, group in enumerate(groups):
            group_id = f"ai_group_{idx}_{int(datetime.now().timestamp())}"
            best_photo_id = None
            highest_score = -1.0

            for item in group:
                blur = calculate_blur_score(item['path'])
                light = calculate_light_score(item['path'])

                # Apply criteria multipliers
                location_weight = 60.0 if item['location_name'] else 0.0
                people_weight = float(item['face_count'] * 40.0)
                blur_weight = float(blur * 0.15)
                light_weight = float(light * 0.5)

                total_score = location_weight + people_weight + blur_weight + light_weight

                # Mark initially as subset variant
                conn.execute("""
                             UPDATE photos
                             SET duplicate_group_id = ?,
                                 is_best_variant    = 0
                             WHERE id = ?
                             """, (group_id, item['id']))

                if total_score > highest_score:
                    highest_score = total_score
                    best_photo_id = item['id']

            # Mark the top-scoring image as the primary variant
            if best_photo_id:
                conn.execute("UPDATE photos SET is_best_variant = 1 WHERE id = ?", (best_photo_id,))

        conn.commit()