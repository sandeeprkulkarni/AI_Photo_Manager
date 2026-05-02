import os
from pathlib import Path
import sqlite3
import hashlib
from datetime import datetime

# Import your database path
from modules.index_store import DB_PATH

class PhotoScanner:
    def __init__(self):
        # Define valid image extensions to filter out non-image files
        self.supported_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.heic'}
        
        # The status_tracker gets injected by server.py automatically
        self.status_tracker = None

    def get_file_hash(self, file_path):
        """Generates a quick MD5 hash of the file to prevent adding duplicates to the DB."""
        hasher = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                buf = f.read(65536)
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = f.read(65536)
            return hasher.hexdigest()
        except Exception as e:
            print(f"Failed to hash {file_path}: {e}")
            return None

    def scan_directory(self, folder_path: str):
        """
        Scans a directory recursively, updates the status tracker, and processes images.
        """
        print(f"Scanner initialized for: {folder_path}")
        
        if self.status_tracker:
            self.status_tracker["message"] = "Locating image files..."
            
        all_files = []
        # Safely walk the directory, ignoring permission errors
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
        
        # --- CONNECT TO DATABASE ---
        # CRITICAL FIX: check_same_thread=False is required for FastAPI BackgroundTasks
        try:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            cursor = conn.cursor()
        except Exception as e:
            print(f"Failed to connect to database: {e}")
            if self.status_tracker:
                self.status_tracker["message"] = "Database connection error."
            return
        
        for file_path in all_files:
            current_count += 1
            filename = os.path.basename(file_path)
            
            # --- UPDATE PROGRESS UI ---
            if self.status_tracker:
                self.status_tracker["current"] = current_count
                self.status_tracker["total"] = total_files
                self.status_tracker["message"] = f"Analyzing {filename}..."
            
            try:
                # 1. Generate hash to avoid processing the same photo twice
                file_hash = self.get_file_hash(file_path)
                if not file_hash:
                    continue # Skip if hashing failed
                
                # Check if this exact photo is already in the database
                cursor.execute("SELECT id FROM photos WHERE hash = ?", (file_hash,))
                if cursor.fetchone():
                    continue # Skip duplicate and move to the next file
                    
                # 2. Get basic file metadata safely
                try:
                    size_kb = os.path.getsize(file_path) // 1024
                except OSError:
                    size_kb = 0
                
                # 3. Save the Photo to the Database
                cursor.execute("""
                    INSERT INTO photos (path, hash, size_kb, taken_at)
                    VALUES (?, ?, ?, ?)
                """, (file_path, file_hash, size_kb, datetime.now()))
                
                # We need the ID for future face insertions
                photo_id = cursor.lastrowid
                
                # ==========================================================
                # 4. FACE DETECTION LOGIC HOOK
                # ==========================================================
                # IMPORTANT: Replace the comment below with your actual face 
                # detection logic. 
                
                # Example using a hypothetical face_detector:
                # try:
                #     from modules.face_detector import detect_faces
                #     faces = detect_faces(file_path)
                #     for face in faces:
                #         # Insert into the 'faces' table WITHOUT an identity_name.
                #         # This is what makes it show up in the "Unidentified Faces" tab!
                #         cursor.execute("""
                #             INSERT INTO faces (photo_id, embedding, rect_x, rect_y, rect_w, rect_h)
                #             VALUES (?, ?, ?, ?, ?, ?)
                #         """, (photo_id, face.embedding, face.x, face.y, face.w, face.h))
                # except Exception as fd_err:
                #     print(f"Face detection failed for {filename}: {fd_err}")
                
                # ==========================================================

                # Commit frequently so the UI dashboard updates in real-time
                if current_count % 5 == 0:
                    conn.commit()
                    
            except sqlite3.Error as sqle:
                print(f"Database error on {filename}: {sqle}")
                continue
            except Exception as e:
                print(f"Unexpected error processing {filename}: {e}")
                continue
                
        # Final database commit and cleanup after the loop finishes
        try:
            conn.commit()
        except Exception as e:
            print(f"Final commit failed: {e}")
        finally:
            conn.close()
        
        if self.status_tracker:
            self.status_tracker["message"] = "Scan completed successfully!"
            self.status_tracker["current"] = total_files