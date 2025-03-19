from dotenv import load_dotenv
import os
from google.genai import types, Client

from test_text_to_speech import get_language_name

# Load environment variables
load_dotenv(override=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Use gemini-2.0-flash for fast mindmap generation
GEMINI_MODEL_ID = "gemini-2.0-flash"

genai_client = Client(api_key=GEMINI_API_KEY)


def generate_audio_script(name, description, type="group", gender="neutral"):
    """Generates audio_script based on content using Google GenAI."""

    if len(description) > 0 and len(name) > 0:
        print(f"Generating audio script for {type} with name '{name}' and description '{description}'")
        
        language_name = get_language_name(description)
        if not language_name:
            print("Could not detect language. Using default English")
            language_name = "English"
            
        # Generate audio script based on the description
        prompt = f"""
            Generate a speech content based on the given description: "{description}".  
            The content should be tailored for {type} named "{name}", gender "{gender}" and must be written exclusively in the language "{language_name}".  
            Just return text for AI can convert to audio file.
        """
        
        generate_content_config = types.GenerateContentConfig(
            temperature=0.5,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
            response_mime_type="text/plain",
        )
        
        response = genai_client.models.generate_content(model=GEMINI_MODEL_ID, contents=prompt, config=generate_content_config)
        return response.text.strip()
        
    else:
        print("Invalid input. Please provide a valid name and description.")
        return ""
    
if __name__ == "__main__":
    # Example usage
    name = "Triều"
    description = "Chúc mừng sinh nhật năm 40 tuổi"
    audio_script = generate_audio_script(name, description, type="project")
    print(audio_script)