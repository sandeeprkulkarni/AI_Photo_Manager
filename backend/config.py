# backend/config.py
from pathlib import Path

# AI Settings
MODEL_TYPE = "gemma"  # Options: "pixtral", "gemma", "llava"
MODEL_PATH = "E:/AI_Models/gemma-2-2b-it-v2.gguf"
# Required if using Gemma/Llava for vision tasks
MMPROJ_PATH = "E:/AI_Models/gemma-vision-clip.projector.gguf" 

# Library Settings
PHOTO_DIR = "E:/Photos"
DB_PATH = Path("backend/data/db/index.db")