# backend/modules/classifier.py
import sqlite3
from .ai_provider import VisionProvider
from .metadata_extractor import extract_gps #
from config import MODEL_TYPE, MODEL_PATH, MMPROJ_PATH, DB_PATH

# Initialize the global provider once
ai = VisionProvider(MODEL_TYPE, MODEL_PATH, MMPROJ_PATH)

def run_classification():
    """Classifies junk vs real photos using the universal provider"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT id, path FROM photos WHERE is_forward = 0")
        for photo_id, path_str in cursor.fetchall():
            b64 = image_to_base64(path_str) #
            
            tag = ai.analyze_image(b64, "Is this a real_photo, meme, or document? One word.")
            
            is_junk = 1 if any(x in tag.lower() for x in ["meme", "document", "screenshot"]) else 2
            conn.execute("UPDATE photos SET is_forward = ? WHERE id = ?", (is_junk, photo_id))