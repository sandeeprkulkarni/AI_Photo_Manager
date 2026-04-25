# backend/modules/ai_provider.py
from llama_cpp import Llama
from llama_cpp.llama_chat_format import PixtralChatCompletionHandler, Llava15ChatCompletionHandler

class VisionProvider:
    def __init__(self, model_type, model_path, mmproj_path=None):
        self.model_type = model_type
        
        # Determine chat format based on model type
        chat_format = "gemma" if model_type == "gemma" else "pixtral"
        
        # Initialize Llama with vision support if mmproj is provided
        self.llm = Llama(
            model_path=model_path,
            chat_format=chat_format,
            n_ctx=2048,
            n_gpu_layers=-1,
            clip_model_path=mmproj_path # Necessary for Gemma vision
        )

    def analyze_image(self, b64_image, prompt):
        """Generic method to get a one-word answer or description"""
        response = self.llm.create_chat_completion(
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
                ]
            }]
        )
        return response["choices"][0]["message"]["content"].strip()