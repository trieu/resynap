import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv(override=True)

DEFAULT_MODEL_ID = os.getenv("GEMINI_TEXT_MODEL_ID", "gemini-2.0-flash-001")
DEFAULT_API_KEY = os.getenv("GEMINI_API_KEY")


class GeminiClient:
    def __init__(self, model_name: str = DEFAULT_MODEL_ID, api_key: str = DEFAULT_API_KEY):
        if not model_name or not api_key:
            raise ValueError("Both `model_name` and `api_key` must be provided or set in the environment.")
        
        self.model_name = model_name
        self.api_key = api_key
        self.client = genai.Client(api_key=self.api_key)

    def generate_content(self, prompt: str, temperature: float = 0.6) -> str:
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
            ),
        )
        return response.candidates[0].content.parts[0].text