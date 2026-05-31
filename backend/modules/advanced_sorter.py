# backend/modules/advanced_sorter.py
import os
import shutil
import imagehash
import torch
import numpy as np
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path

# Load CLIP locally (Downloads ~600MB on first run, then runs offline)
device = "cuda" if torch.cuda.is_available() else "cpu"
model_id = "openai/clip-vit-base-patch32"
model = CLIPModel.from_pretrained(model_id).to(device)
processor = CLIPProcessor.from_pretrained(model_id)

# Define our classification prompts based on your rules
JUNK_LABELS = [
    "a political poster, rally, or politician",
    "a good morning, good night, or motivational quote card",
    "a religious greeting or blessing image",
    "a birthday cake or anniversary celebration card",
    "a holiday or festival greeting card like Diwali, Christmas, or New Year",
    "an advertisement, discount banner, or promotional flyer",
    "a frequently shared internet meme or viral forward",
    "a screenshot of text, news, or a chat conversation",
    "adult, abusive, or explicit content",
    "a scam, fake job offer, or phishing attempt warning"
]

PERSONAL_LABELS = [
    "a personal family photo or group of relatives",
    "a selfie of a person",
    "a personal travel or nature photograph",
    "a photo of a pet or animal",
    "a candid photo from a real-life event or party"
]

ALL_LABELS = JUNK_LABELS + PERSONAL_LABELS

def is_whatsapp_junk(image_path: str) -> bool:
    """Uses Zero-Shot classification to determine if an image is junk."""
    try:
        image = Image.open(image_path).convert("RGB")
        inputs = processor(text=ALL_LABELS, images=image, return_tensors="pt", padding=True).to(device)
        
        with torch.no_grad():
            outputs = model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1).cpu().numpy()[0]
            
        # Get the index of the highest probability
        best_match_idx = np.argmax(probs)
        best_label = ALL_LABELS[best_match_idx]
        
        # If the best matching description is in our Junk list, it's junk!
        return best_label in JUNK_LABELS
    except Exception as e:
        print(f"Error classifying {image_path}: {e}")
        return False # Default to keep if unreadable

def extract_image_features(image_path: str):
    """Extracts both pHash and CLIP embeddings for deduplication."""
    try:
        image = Image.open(image_path).convert("RGB")
        
        # 1. pHash: Great for exact matches, resizes, and minor compressions
        p_hash = str(imagehash.phash(image))
        
        # 2. Embedding: Great for crops, filters, and bursts of the same scene
        inputs = processor(images=image, return_tensors="pt").to(device)
        with torch.no_grad():
            embedding = model.get_image_features(**inputs).cpu().numpy()
            # Normalize the embedding for cosine similarity
            embedding = embedding / np.linalg.norm(embedding)
            
        return p_hash, embedding[0]
    except Exception:
        return None, None

def process_and_sort_library(source_folder: str, junk_folder: str, personal_folder: str):
    """Phase 1: Filter out the Junk. Phase 2: Find Duplicates in Personal."""
    
    Path(junk_folder).mkdir(parents=True, exist_ok=True)
    Path(personal_folder).mkdir(parents=True, exist_ok=True)
    
    valid_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    personal_images = []
    
    print("--- PHASE 1: JUNK FILTERING ---")
    for root, _, files in os.walk(source_folder):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext not in valid_extensions: continue
                
            file_path = os.path.join(root, file)
            print(f"Analyzing: {file}...")
            
            if is_whatsapp_junk(file_path):
                print("   -> 🗑️ Classified as JUNK. Moving.")
                shutil.move(file_path, os.path.join(junk_folder, file))
            else:
                print("   -> 📸 Classified as PERSONAL. Moving.")
                dest_path = os.path.join(personal_folder, file)
                shutil.move(file_path, dest_path)
                personal_images.append(dest_path)

    print("\n--- PHASE 2: ADVANCED DUPLICATE DETECTION ---")
    if not personal_images:
        return
        
    features = []
    paths = []
    
    # Extract features for all personal photos
    for path in personal_images:
        p_hash, emb = extract_image_features(path)
        if p_hash is not None and emb is not None:
            features.append({"path": path, "phash": p_hash, "emb": emb})
            paths.append(path)
            
    # Matrix calculation
    embeddings_matrix = np.array([f["emb"] for f in features])
    similarity_matrix = cosine_similarity(embeddings_matrix)
    
    visited = set()
    duplicate_groups = []
    
    for i in range(len(features)):
        if i in visited: continue
        visited.add(i)
        
        current_group = [features[i]["path"]]
        
        for j in range(i + 1, len(features)):
            if j in visited: continue
            
            # Check 1: Structural Match (Resized, compressed, exact copies)
            # If the hamming distance of the hash is < 4, it's essentially identical
            hash_diff = imagehash.hex_to_hash(features[i]["phash"]) - imagehash.hex_to_hash(features[j]["phash"])
            is_structurally_identical = hash_diff < 4
            
            # Check 2: Semantic Match (Cropped, burst mode, filtered)
            # Cosine similarity > 0.92 indicates highly similar visual content
            is_semantically_identical = similarity_matrix[i][j] > 0.92
            
            if is_structurally_identical or is_semantically_identical:
                current_group.append(features[j]["path"])
                visited.add(j)
                
        if len(current_group) > 1:
            duplicate_groups.append(current_group)
            
    print("\n--- RESULTS ---")
    print(f"Found {len(duplicate_groups)} groups of duplicates!")
    for idx, group in enumerate(duplicate_groups):
        print(f"Group {idx + 1}:")
        for p in group:
            print(f"  - {os.path.basename(p)}")

# Example Usage:
# process_and_sort_library("D:/TestPhotos/Input", "D:/TestPhotos/Junk", "D:/TestPhotos/Personal")