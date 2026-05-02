import os
from pathlib import Path
import sqlite3
import hashlib
from datetime import datetime

# Import your database path
from modules.index_store import DB_PATH

class PhotoScanner:
    def __init__(self):
        self.supported_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.heic'}
        self.status_tracker = None

    def get_file_hash(self, file_path):
        """Generates MD5 hash to prevent adding duplicate photos."""
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
                self.status_tracker["message"] = "No images found."
            return

        current_count = 0
        
        # CRITICAL FIX: check_same_thread=False required for BackgroundTasks
        try:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            cursor = conn.cursor()
        except Exception as e:
            print(f"Database connection error: {e}")
            return
        
        for file_path in all_files:
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
                
                # Check for duplicates
                cursor.execute("SELECT id FROM photos WHERE hash = ?", (file_hash,))
                if cursor.fetchone():
                    continue 
                    
                # Get file size
                try:
                    size_kb = os.path.getsize(file_path) // 1024
                except OSError:
                    size_kb = 0
                
                # Save Photo to Database
                cursor.execute("""
                    INSERT INTO photos (path, hash, size_kb, taken_at)
                    VALUES (?, ?, ?, ?)
                """, (file_path, file_hash, size_kb, datetime.now()))
                
                # Commit frequently for real-time UI updates
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
        
        if self.status_tracker:
            self.status_tracker["message"] = "Scan completed successfully!"
            self.status_tracker["current"] = total_files