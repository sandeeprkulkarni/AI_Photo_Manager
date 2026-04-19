import shutil
import sqlite3
import os
from pathlib import Path
from modules.index_store import DB_PATH
from modules.people_tagger import get_person_name

def export_photos(output_dir="Organized_Library", copy_not_move=True):
    """
    Enhanced Exporter: Groups photos by Location/Event and filters by recognized people.
    Replaces the previous basic export logic.
    """
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Export Photos with Recognized People (Grouped by Location or Event)
    # This fulfills the requirement to only include recognized individuals in primary folders.
    print("🌍 Exporting recognized people by Location/Event...")
    query = """
        SELECT DISTINCT p.id, p.path, p.location_name, p.event_type 
        FROM photos p
        JOIN faces f ON p.id = f.photo_id
        WHERE f.cluster_id >= 0  -- Filters for images with recognized and grouped individuals
    """
    cursor = conn.execute(query)
    recognized_photos = cursor.fetchall()
    
    exported_ids = set()
    
    for pid, path_str, loc, evt in recognized_photos:
        p_path = Path(path_str)
        if not p_path.exists():
            continue

        # Determine folder structure: Location (GPS) -> Event (AI Fallback) -> Default
        if loc and loc != "Unknown":
            folder_name = f"Locations/{loc}"
        elif evt:
            folder_name = f"Events/{evt}"
        else:
            folder_name = "Recognized_Other"

        target_dir = output_root / folder_name
        target_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            dest = target_dir / p_path.name
            if copy_not_move:
                shutil.copy2(path_str, dest)
            else:
                shutil.move(path_str, dest)
            exported_ids.add(pid)
        except Exception as e:
            print(f"Error exporting {path_str}: {e}")

    # 2. Export Unknown Faces to a separate "Unidentified" subfolder
    # This keeps your main location/event folders clean.
    print("❓ Exporting unidentified photos...")
    unidentified_query = """
        SELECT id, path FROM photos 
        WHERE id NOT IN (SELECT DISTINCT photo_id FROM faces WHERE cluster_id >= 0)
    """
    unid_cursor = conn.execute(unidentified_query)
    unid_photos = unid_cursor.fetchall()
    
    unid_dir = output_root / "Unidentified_or_Unknown"
    unid_dir.mkdir(parents=True, exist_ok=True)
    
    for pid, path_str in unid_photos:
        if pid in exported_ids:
            continue
            
        p_path = Path(path_str)
        if not p_path.exists():
            continue
            
        try:
            dest = unid_dir / p_path.name
            if copy_not_move:
                shutil.copy2(path_str, dest)
            else:
                shutil.move(path_str, dest)
        except Exception as e:
            print(f"Error exporting unidentified {path_str}: {e}")

    conn.close()
    print(f"✅ Export complete! Library organized at: '{output_root.absolute()}'")