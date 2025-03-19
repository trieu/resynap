# Description: This script demonstrates how to use the Narakeet Text-to-Speech API to convert text to speech.
import requests
import os

class TextToSpeechAPI:
    def __init__(self, api_key):
        """Initialize the API client with the provided API key."""
        self.api_key = api_key
        self.base_url = "https://api.narakeet.com/text-to-speech/mp3?voice=minh"
        self.headers = {
            "Content-Type": "text/plain",
            "x-api-key": self.api_key,
            "accept": "application/octet-stream",
        }

    def generate_speech(self, text, output_file="result.mp3"):
        """
        Converts text to speech and saves it as an audio file.

        :param text: The input text to be converted.
        :param output_file: The filename to save the generated audio.
        :return: Path to the saved audio file.
        """
        try:
            response = requests.post(self.base_url, data=text, headers=self.headers)

            if response.status_code == 200:
                with open(output_file, "wb") as file:
                    file.write(response.content)
                print(f"✅ Audio file saved successfully: {output_file}")
                return output_file
            else:
                print(f"❌ Error: {response.status_code}, {response.text}")
                return None
        except Exception as e:
            print(f"❌ Exception occurred: {e}")
            return None

# Example Usage
if __name__ == "__main__":
    API_KEY = os.getenv("NARAKEET_API_KEY")
    tts = TextToSpeechAPI(API_KEY)
    vn_text = '''
        KHÔNG KHÍ TẠI NHÀ VĂN HÓA THANH NIÊN NGAY LÚC NÀY ĐANG DẦN TRỞ NÊN SÔI ĐỘNG HƠN VỚI NGÀY HỘI GIẤC MƠ LỌ LEM! 
        '''
    tts.generate_speech(vn_text, "output.mp3")
