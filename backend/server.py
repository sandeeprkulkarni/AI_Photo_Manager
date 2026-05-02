import os
from pathlib import Path
import sqlite3
import hashlib
from datetime import datetime

# Import your database path
from modules.index_store import DB_PATH

class PhotoScanner:
    def __init__(self):
        # We define valid image extensions to filter out non-image files
        self.supported_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.heic'}
        
        # The status_tracker gets injected by server.py automatically
        self.status_tracker = None

    def get_file_hash(self, file_path):
        """Generates a quick MD5 hash of the file to prevent adding duplicates to the DB."""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()

    def scan_directory(self, folder_path: str):
        """
        Scans a directory recursively, updates the status tracker, and processes images.
        """
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
        
        if total_files == 0:
            if self.status_tracker:
                self.status_tracker["message"] = "No images found in directory."
            return

        current_count = 0
        
        # --- CONNECT TO DATABASE ---
        # We open the connection before the loop to save the files as we find them.
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
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
                
                # Check if this exact photo is already in the database
                cursor.execute("SELECT id FROM photos WHERE hash = ?", (file_hash,))
                if cursor.fetchone():
                    continue # Skip duplicate and move to the next file
                    
                # 2. Get basic file metadata
                size_kb = os.path.getsize(file_path) // 1024
                
                # 3. Save the Photo to the Database
                cursor.execute("""
                    INSERT INTO photos (path, hash, size_kb, taken_at)
                    VALUES (?, ?, ?, ?)
                """, (file_path, file_hash, size_kb, datetime.now()))
                
                photo_id = cursor.lastrowid
                
                # ==========================================================
                # FACE DETECTION LOGIC HOOK
                # If you have face_detector.py ready, you would call it here!
                #
                # Example:
                # faces = my_face_detector.find_faces(file_path)
                # for face in faces:
                #     cursor.execute("""
                #         INSERT INTO faces (photo_id, embedding, rect_x, rect_y, rect_w, rect_h)
                #         VALUES (?, ?, ?, ?, ?, ?)
                #     """, (photo_id, face.embedding, face.x, face.y, face.w, face.h))
                # ==========================================================
                
                # Commit to the database every 10 photos so the UI updates smoothly
                if current_count % 10 == 0:
                    conn.commit()
                    
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                continue
                
        # Final database commit and cleanup after the loop finishes
        conn.commit()
        conn.close()
        
        if self.status_tracker:
            self.status_tracker["message"] = "Scan completed successfully!"