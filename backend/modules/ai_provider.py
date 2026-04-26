# backend/modules/ai_provider.py
from llama_cpp import Llama

class VisionProvider:
    def __init__(self, model_path, mmproj_path=None, model_type="gemma"):
        self.model_type = model_type
        # Gemma requires the 'gemma' chat format; Pixtral uses 'pixtral'
        chat_format = "gemma" if "gemma" in model_type.lower() else "pixtral"
        
        self.llm = Llama(
            model_path=model_path,
            chat_format=chat_format,
            n_ctx=2048,
            n_gpu_layers=-1, # Enable GPU acceleration
            clip_model_path=mmproj_path # Required for vision-capable Gemma
        )

    def analyze(self, image_path, prompt):
        """Generic method to handle image analysis regardless of the model."""
        # Logic to convert image to base64 and get completion...
        pass