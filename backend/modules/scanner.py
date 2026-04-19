# backend/modules/scanner.py
import os
import hashlib
import sqlite3
import shutil
from pathlib import Path
from modules.index_store import DB_PATH

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

class Scanner:
    def __init__(self, root_path: str):
        self.root = Path(root_path)

    def _file_hash(self, path):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            h.update(f.read())
        return h.hexdigest()

    def scan(self):
        discarded_dir = self.root / "discarded_duplicates"
        discarded_dir.mkdir(exist_ok=True)
        
        with sqlite3.connect(DB_PATH) as conn:
            for root_dir, _, files in os.walk(self.root):
                if "discarded_duplicates" in root_dir: continue
                for f in files:
                    path = Path(root_dir) / f
                    if path.suffix.lower() not in IMAGE_EXTS: continue
                    
                    if conn.execute("SELECT id FROM photos WHERE path = ?", (str(path),)).fetchone():
                        continue 

                    h = self._file_hash(path)
                    try:
                        conn.execute(
                            "INSERT INTO photos (path, hash, size_kb) VALUES (?, ?, ?)",
                            (str(path), h, path.stat().st_size // 1024)
                        )
                    except sqlite3.IntegrityError:
                        shutil.move(str(path), discarded_dir / f)
            conn.commit()