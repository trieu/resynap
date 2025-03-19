import os
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate
from langdetect import detect, LangDetectException

LANGUAGE_MAPPING = {
    "en": "English",
    "vi": "Vietnamese",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "zh-cn": "Chinese (Simplified)",
    "zh-tw": "Chinese (Traditional)",
    "ja": "Japanese",
    "ko": "Korean",
    "ru": "Russian"
}

def detect_language(text):
    """Detects the language code of the given text."""
    try:
        return detect(text)
    except LangDetectException:
        return 'en'

def get_language_name(text):
    """Detects the language and returns its full name."""
    lang_code = detect_language(text)
    return LANGUAGE_MAPPING.get(lang_code, "English")


class TextToSpeechConverter:
    """Converts text to speech using Google Cloud Text-to-Speech API with language detection."""

    def __init__(self, credentials_path=None):
        """Initializes the TextToSpeechConverter."""
        if credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        self.tts_client = texttospeech.TextToSpeechClient()
        self.translate_client = translate.Client()



    def get_voice_params(self, language_code, gender):
        """Gets voice parameters based on the language code and gender, prioritizing naturalness.

        Args:
            language_code: A short language code (e.g., "en", "vi").
            gender: "male", "female", or any other string for neutral.

        Returns:
            A dictionary containing voice parameters suitable for Google Cloud Text-to-Speech.
        """

        # Map short language code to Google Cloud-supported voice locales
        language_map = {
            "en": "en-US",
            "vi": "vi-VN",
            "fr": "fr-FR",  # Example: French
            # Add more language mappings as needed
        }

        locale = language_map.get(language_code, "en-US")  # Default to English

        # Prioritize Neural2 voices for enhanced naturalness, then Wavenet, then standard.
        # Adapt this list to the most current and highest quality voices available in Google Cloud Text-to-Speech.  Check the documentation!
        voice_options = {
            "en-US": {
                "female": ["en-US-Neural2-F", "en-US-Wavenet-F", "en-US-Standard-F"],
                "male":   ["en-US-Neural2-D", "en-US-Wavenet-D", "en-US-Standard-D"],
                "neutral": ["en-US-Neural2-D", "en-US-Wavenet-D", "en-US-Standard-D"]  # Or another suitable neutral voice
            },
            "vi-VN": {
                "female": ["vi-VN-Neural2-A", "vi-VN-Standard-A"],  # Vietnamese has fewer Neural2 options
                "male":   ["vi-VN-Wavenet-D", "vi-VN-Standard-B"],  # Vietnamese has fewer Neural2 options
                "neutral": ["vi-VN-Wavenet-D", "vi-VN-Standard-B"]
            },
            "fr-FR": {  # Example for French
                "female": ["fr-FR-Neural2-C", "fr-FR-Wavenet-C", "fr-FR-Standard-C"],
                "male":   ["fr-FR-Neural2-D", "fr-FR-Wavenet-D", "fr-FR-Standard-D"],
                "neutral":["fr-FR-Neural2-D", "fr-FR-Wavenet-D", "fr-FR-Standard-D"]
            },
            # Add more locales and voice options as needed, checking Google Cloud documentation for available voices.
        }

        gender_lower = gender.lower()
        if gender_lower in ("male", "female"):
            ssml_gender = texttospeech.SsmlVoiceGender.MALE if gender_lower == "male" else texttospeech.SsmlVoiceGender.FEMALE
        else:
            ssml_gender = texttospeech.SsmlVoiceGender.NEUTRAL

        # Select the voice: try Neural2, then Wavenet, then Standard.
        try:
            voice_name = voice_options[locale][gender_lower][0]  # Try Neural2 first
        except KeyError:
            # If no specific gendered voice is found, try a neutral option
            try:
                voice_name = voice_options[locale]["neutral"][0]
                ssml_gender = texttospeech.SsmlVoiceGender.NEUTRAL # Ensure gender is neutral
            except KeyError:  # Handle cases where even a neutral voice is missing
                voice_name = "en-US-Neural2-D" # Fallback to US English Neural2, male (common default)
                locale = "en-US"
                ssml_gender = texttospeech.SsmlVoiceGender.NEUTRAL

        print(f"Detected language: {locale}, gender: {ssml_gender.name}, using voice: {voice_name}")
        return {"name": voice_name, "gender": ssml_gender, "language_code": locale}

    def synthesize_speech(self, text, output_file="output.mp3", speaking_rate=1.0, pitch=0.0, gender="neutral", audio_encoding=texttospeech.AudioEncoding.MP3):
        """Synthesizes speech from the given text with language detection."""
        language_code = detect_language(text)
        if not language_code:
            print("Could not detect language. Using default English voice.")
            language_code = "en"

        voice_params = self.get_voice_params(language_code, gender)
        voice_name = voice_params["name"]
        ssml_gender = voice_params["gender"]
        language_code = voice_params["language_code"]  # Use full locale code

        try:
            synthesis_input = texttospeech.SynthesisInput(text=text)

            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_name,
                ssml_gender=ssml_gender,
            )

            audio_config = texttospeech.AudioConfig(
                audio_encoding=audio_encoding,
                speaking_rate=speaking_rate,  # Adjust speaking rate for more naturalness
                pitch=pitch  # Adjust pitch for more naturalness
            )

            print(f"Using voice: {voice.name}, Language: {voice.language_code}, Gender: {voice.ssml_gender.name}, Speaking Rate: {speaking_rate}, Pitch: {pitch}")
            response = self.tts_client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )

            with open(output_file, "wb") as out:
                out.write(response.audio_content)
            print(f"Audio content written to file: {output_file}")
            return True

        except Exception as e:
            print(f"Error synthesizing speech: {e}")
            return False

if __name__ == "__main__":
    credentials_path = None  # Or "path/to/your/credentials.json"
    converter = TextToSpeechConverter(credentials_path)


    texts_to_synthesize = [
        "Xin chào, đây là văn bản tiếng Việt.",
        "Hello, this is English text."
    ]

    for i, text in enumerate(texts_to_synthesize):
        output_file = f"output_{i}.mp3"
        if converter.synthesize_speech(text, output_file, 0.9, 0.7, 'female'):
            print(f"Text-to-speech conversion for '{text}' successful.")
        else:
            print(f"Text-to-speech conversion for '{text}' failed.")
