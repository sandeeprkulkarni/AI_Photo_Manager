import sqlite3
import base64
import io
from PIL import Image, ImageOps
from llama_cpp import Llama
from llama_cpp.llama_chat_format import PixtralChatCompletionHandler
from modules.index_store import DB_PATH

def image_to_base64(path):
    """Convert and resize image to base64 for the model"""
    with Image.open(path) as img:
        img = ImageOps.exif_transpose(img)
        # Resize to 512px for faster vision processing
        img.thumbnail((512, 512))
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
        
def analyze_photo_context(model_path, photo_id, path_str):
    """Uses Pixtral for Fallback Location and Event Detection"""
    llm = Llama(model_path=model_path, n_ctx=2048, n_gpu_layers=-1, chat_format="pixtral")
    b64_image = image_to_base64(path_str)
    
    # Prompt for Location and Event
    prompt = "Identify the location/landmark and any event (e.g. Wedding, Festival, Party). Format: Location: [Name], Event: [Name]"
    
    response = llm.create_chat_completion(
        messages=[{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
        ]}]
    )
    
    content = response["choices"][0]["message"]["content"]
    # Simple parsing logic (can be made more robust with regex)
    loc = content.split("Location:")[1].split(",")[0].strip() if "Location:" in content else "Unknown"
    evt = content.split("Event:")[1].strip() if "Event:" in content else None
    
    return loc, evt
    
def run_context_analysis(model_path):
    """
    Uses Pixtral to describe the event or subject of 'Unknown' photos.
    """
    llm = Llama(
        model_path=model_path,
        n_ctx=2048,
        n_gpu_layers=-1, 
        chat_format="pixtral"
    )

    with sqlite3.connect(DB_PATH) as conn:
        # Target photos that are 'real photos' but have no identified faces
        query = """
            SELECT p.id, p.path FROM photos p
            LEFT JOIN faces f ON p.id = f.photo_id
            WHERE p.is_forward = 2 AND (f.id IS NULL OR f.cluster_id < 0)
            AND p.context_label IS NULL
        """
        cursor = conn.execute(query)
        rows = cursor.fetchall()
        
        for photo_id, path_str in rows:
            try:
                b64_image = image_to_base64(path_str)
                
                # Prompting for Event/Subject context
                response = llm.create_chat_completion(
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text", 
                                    "text": "What is the main subject or event in this photo? (e.g. Wedding, Beach, Birthday, Nature). Answer in exactly one word."
                                },
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
                            ]
                        }
                    ]
                )
                
                label = response["choices"][0]["message"]["content"].strip().capitalize()
                
                # Update the database with the event tag
                conn.execute("UPDATE photos SET context_label = ? WHERE id = ?", (label, photo_id))
                print(f"Tagged {Path(path_str).name} as: {label}")
                
            except Exception as e:
                print(f"Context error for {path_str}: {e}")
        
        conn.commit()        

def run_classification(model_path):
    """
    Pass the path to your Pixtral-12B-GGUF file.
    Requires: pip install llama-cpp-python
    """
    # Initialize the model with vision support
    # Note: Ensure you have the corresponding clip/mmproj file if required by your GGUF
    llm = Llama(
        model_path=model_path,
        n_ctx=2048,
        n_gpu_layers=-1, # Use -1 for full GPU acceleration
        chat_format="pixtral"
    )

    with sqlite3.connect(DB_PATH) as conn:
        # Select photos that haven't been classified (is_forward = 0)
        cursor = conn.execute("SELECT id, path FROM photos WHERE is_forward = 0")
        rows = cursor.fetchall()
        
        for photo_id, path_str in rows:
            try:
                b64_image = image_to_base64(path_str)
                
                response = llm.create_chat_completion(
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Is this a real_photo, meme, forward, or document? Answer in one word."},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
                            ]
                        }
                    ]
                )
                
                tag = response["choices"][0]["message"]["content"].lower().strip()
                
                # 1 = Junk (Meme/Forward/Doc), 2 = Real Photo
                is_junk = 1 if any(x in tag for x in ["meme", "forward", "document", "screenshot"]) else 2
                
                conn.execute("UPDATE photos SET is_forward = ? WHERE id = ?", (is_junk, photo_id))
                print(f"Classified {Path(path_str).name}: {tag}")
                
            except Exception as e:
                print(f"Error classifying {path_str}: {e}")
        
        conn.commit()