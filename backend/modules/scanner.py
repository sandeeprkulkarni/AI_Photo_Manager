import os
import hashlib
import sqlite3
import shutil  # <-- Added this missing import
from pathlib import Path
from modules.index_store import DB_PATH

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()

def scan_folder(root: Path):
    discarded_dir = root / "discarded_duplicates"
    discarded_dir.mkdir(exist_ok=True)
    
    with sqlite3.connect(DB_PATH) as conn:
        for root_dir, _, files in os.walk(root):
            # Skip the discarded folder so we don't scan it
            if "discarded_duplicates" in root_dir: 
                continue 
            
            for f in files:
                path = Path(root_dir) / f
                if path.suffix.lower() not in IMAGE_EXTS: 
                    continue
                
                # Check if this specific file path is already in the DB
                existing = conn.execute("SELECT id FROM photos WHERE path = ?", (str(path),)).fetchone()
                if existing:
                    continue # Skip if already indexed

                h = file_hash(path)
                try:
                    conn.execute(
                        "INSERT INTO photos (path, hash, size_kb) VALUES (?, ?, ?)",
                        (str(path), h, path.stat().st_size // 1024)
                    )
                except sqlite3.IntegrityError:
                    # If the hash (UNIQUE constraint) fails, it's a content duplicate
                    try:
                        shutil.move(str(path), discarded_dir / f)
                        print(f"🗑️ Duplicate content moved: {f}")
                    except Exception as move_err:
                        print(f"❌ Error moving duplicate {f}: {move_err}")
        
        conn.commit()