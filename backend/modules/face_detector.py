import sqlite3
import face_recognition
from PIL import Image, ImageOps # Added ImageOps
import numpy as np
from pathlib import Path
from modules.index_store import DB_PATH

def extract_faces(use_cnn=False):
    model_type = "cnn" if use_cnn else "hog" # CNN requires GPU for reasonable speed
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT id, path FROM photos WHERE has_faces = 0")
        rows = cursor.fetchall()
        
        for photo_id, path_str in rows:
            try:
                # Load and FIX orientation before AI sees it
                pil_img = Image.open(path_str)
                pil_img = ImageOps.exif_transpose(pil_img) 
                image = np.array(pil_img.convert("RGB"))
                
                # number_of_times_to_upsample=1 helps find smaller faces
                face_locs = face_recognition.face_locations(image, number_of_times_to_upsample=1) 
                face_embs = face_recognition.face_encodings(image, face_locs)
                
                for (top, right, bottom, left), emb in zip(face_locs, face_embs):
                    w, h = right - left, bottom - top
                    
                    # 🛑 NOISE FILTER: Skip anything smaller than 60x60 pixels
                    # This removes the "non-face" small blurry crops you saw
                    if w < 80 or h < 80: continue 

                    rect = (left, top, w, h)
                    conn.execute("""
                        INSERT OR IGNORE INTO faces (photo_id, rect_x, rect_y, rect_w, rect_h, embedding) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (photo_id, *rect, emb.tobytes()))
                
                conn.execute("UPDATE photos SET has_faces = 1 WHERE id = ?", (photo_id,))
                
            except Exception as e:
                print(f"Error processing {path_str}: {e}")
        conn.commit()