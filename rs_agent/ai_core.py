import os
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.api_core.exceptions import GoogleAPIError

# Load environment variables from .env file
load_dotenv(override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default fallback values
DEFAULT_MODEL_ID = os.getenv("GEMINI_TEXT_MODEL_ID", "gemini-2.0-flash-001")
DEFAULT_API_KEY = os.getenv("GEMINI_API_KEY")

# Error message used when required config is missing
INIT_FAIL_MSG = "Both `model_name` and `api_key` must be provided or set in the environment."


class GeminiClient:
    """
    A wrapper class for interacting with Google Gemini API.
    Handles text generation via a specified model.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL_ID, api_key: str = DEFAULT_API_KEY):
        if not model_name or not api_key:
            logger.critical(INIT_FAIL_MSG)
            raise ValueError(INIT_FAIL_MSG)

        self.model_name = model_name
        self.api_key = api_key

        try:
            self.client = genai.Client(api_key=self.api_key)
            logger.info(f"Gemini client initialized with model '{self.model_name}'")
        except Exception as e:
            logger.exception("Failed to initialize Gemini client.")
            raise

    def generate_content(self, prompt: str, temperature: float = 0.6, on_error: str = '') -> str:
        """
        Generates text content from a given prompt using the Gemini API.

        Args:
            prompt (str): The input prompt to send to the model.
            temperature (float): Sampling temperature for creativity.
            on_error (str): Fallback string if generation fails.

        Returns:
            str: Generated content or fallback string.
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                ),
            )

            if response.candidates and response.candidates[0].content.parts:
                text = response.candidates[0].content.parts[0].text.strip()
                logger.debug(f"Generated content: {text}")
                return text
            else:
                logger.warning("Empty response received from Gemini API.")
                return on_error

        except GoogleAPIError as e:
            logger.error(f"Google API error during content generation: {e}")
            return on_error
        except Exception as e:
            logger.exception("Unexpected error during content generation.")
            return on_error
