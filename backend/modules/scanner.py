import os
from pathlib import Path
import sqlite3
import hashlib
from datetime import datetime
import numpy as np

from modules.index_store import DB_PATH

class PhotoScanner:
    def __init__(self):
        self.supported_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.heic'}
        self.status_tracker = None

    def get_file_hash(self, file_path):
        hasher = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                buf = f.read(65536)
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = f.read(65536)
            return hasher.hexdigest()
        except Exception:
            return None

    def scan_directory(self, folder_path: str):
        print(f"Scanner initialized for: {folder_path}")
        if self.status_tracker:
            self.status_tracker["message"] = "Locating image files..."
            
        all_files = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in self.supported_extensions:
                    all_files.append(os.path.join(root, file))
                    
        total_files = len(all_files)
        print(f"Found {total_files} images to process.")
        if total_files == 0:
            if self.status_tracker:
                self.status_tracker["message"] = "No images found in directory."
            return

        current_count = 0
        try:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            cursor = conn.cursor()
            
            # ==========================================================
            # 1. PRE-LOAD *ALL* KNOWN FACES FOR AUTO-TAGGING
            # ==========================================================
            # We fetch every single labeled face so the AI has multiple 
            # reference points for the same person (e.g., with/without hat)
            cursor.execute("SELECT identity_name, embedding FROM faces WHERE identity_name IS NOT NULL AND identity_name != ''")
            known_rows = cursor.fetchall()
            
            known_names = []
            known_encodings = []
            
            for name, emb in known_rows:
                if emb:
                    known_names.append(name)
                    known_encodings.append(np.frombuffer(emb, dtype=np.float64))
                    
        except Exception as e:
            print(f"Database connection error: {e}")
            return
        
        for file_path in all_files:
            if self.status_tracker and self.status_tracker.get("cancel_requested"):
                self.status_tracker["message"] = "Scan cancelled by user."
                break
                
            current_count += 1
            filename = os.path.basename(file_path)
            
            if self.status_tracker:
                self.status_tracker["current"] = current_count
                self.status_tracker["total"] = total_files
                self.status_tracker["message"] = f"Analyzing {filename}..."
            
            try:
                file_hash = self.get_file_hash(file_path)
                if not file_hash:
                    continue 
                
                cursor.execute("SELECT id FROM photos WHERE hash = ?", (file_hash,))
                if cursor.fetchone():
                    continue 
                    
                try:
                    size_kb = os.path.getsize(file_path) // 1024
                except OSError:
                    size_kb = 0
                
                cursor.execute("""
                    INSERT INTO photos (path, hash, size_kb, taken_at)
                    VALUES (?, ?, ?, ?)
                """, (file_path, file_hash, size_kb, datetime.now()))
                photo_id = cursor.lastrowid
                
                # --- FACE DETECTION & AUTO-MATCHING LOGIC ---
                try:
                    import face_recognition
                    image = face_recognition.load_image_file(file_path)
                    face_locations = face_recognition.face_locations(image)
                    
                    if face_locations:
                        face_encodings = face_recognition.face_encodings(image, face_locations)
                        for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
                            w = right - left
                            h = bottom - top
                            
                            identity = None
                            
                            # 2. COMPARE AGAINST EVERY SAVED FACE VARIATION
                            if known_encodings:
                                # face_distance gives us a mathematical score of how close the match is
                                # Lower numbers mean a better match. 0.5 is a standard strict threshold.
                                face_distances = face_recognition.face_distance(known_encodings, encoding)
                                best_match_index = np.argmin(face_distances)
                                
                                if face_distances[best_match_index] < 0.5:
                                    identity = known_names[best_match_index]
                            
                            # 3. SAVE TO DB 
                            cursor.execute("""
                                INSERT INTO faces (photo_id, embedding, rect_x, rect_y, rect_w, rect_h, identity_name)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (photo_id, encoding.tobytes(), left, top, w, h, identity))
                            
                except ImportError:
                    print("ERROR: Please run 'pip install face_recognition' to enable face scanning.")
                except Exception as fd_err:
                    print(f"Face detection failed for {filename}: {fd_err}")

                if current_count % 5 == 0:
                    conn.commit()
                    
            except sqlite3.Error as sqle:
                print(f"DB error on {filename}: {sqle}")
                continue
            except Exception as e:
                print(f"Processing error {filename}: {e}")
                continue
                
        try:
            conn.commit()
        finally:
            conn.close()
        
        if self.status_tracker and not self.status_tracker.get("cancel_requested"):
            self.status_tracker["current"] = total_files