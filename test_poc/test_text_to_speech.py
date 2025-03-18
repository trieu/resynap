import os
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate
from langdetect import detect, LangDetectException

class TextToSpeechConverter:
    """Converts text to speech using Google Cloud Text-to-Speech API with language detection."""

    def __init__(self, credentials_path=None):
        """Initializes the TextToSpeechConverter."""
        if credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        self.tts_client = texttospeech.TextToSpeechClient()
        self.translate_client = translate.Client()

    def detect_language(self, text):
        """Detects the language of the given text."""
        try:
            return detect(text)
        except LangDetectException:
            return None

    def get_voice_params(self, language_code, gender):
        """Gets voice parameters based on the language code and gender."""
        
        # Map short language code to Google Cloud-supported voice locales
        language_map = {
            "en": "en-US",
            "vi": "vi-VN"
        }
        
        locale = language_map.get(language_code, "en-US")  # Default to English

        if gender.lower() == 'female':
            ssml_gender = texttospeech.SsmlVoiceGender.FEMALE
            voice_name = {
                "en-US": "en-US-Wavenet-F",
                "vi-VN": "vi-VN-Wavenet-A"
            }.get(locale, "en-US-Wavenet-F")
                
        elif gender.lower() == 'male':
            ssml_gender = texttospeech.SsmlVoiceGender.MALE
            voice_name = {
                "en-US": "en-US-Wavenet-D",
                "vi-VN": "vi-VN-Wavenet-B"
            }.get(locale, "en-US-Wavenet-D")
        else:
            ssml_gender = texttospeech.SsmlVoiceGender.NEUTRAL
            voice_name = "en-US-Neural2-D"  # General fallback

        print(f"Detected language: {locale}, gender: {ssml_gender.name}, using voice: {voice_name}")

        return {"name": voice_name, "gender": ssml_gender, "language_code": locale}

    def synthesize_speech(self, text, gender="female", output_file="output.mp3", audio_encoding=texttospeech.AudioEncoding.MP3):
        """Synthesizes speech from the given text with language detection."""
        language_code = self.detect_language(text)
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
                audio_encoding=audio_encoding
            )

            print(f"Using voice: {voice.name}, Language: {voice.language_code}, Gender: {voice.ssml_gender.name}")
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
        if converter.synthesize_speech(text, "male", output_file):
            print(f"Text-to-speech conversion for '{text}' successful.")
        else:
            print(f"Text-to-speech conversion for '{text}' failed.")
