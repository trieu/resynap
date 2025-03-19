from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import schedule
import unidecode
import re
import time

from test_text_to_speech import TextToSpeechConverter
from test_ideas_to_audio_script import generate_audio_script
from test_upload_file_to_aws_s3 import upload_audio_to_s3

load_dotenv(override=True)

GEN_BY_AI = "generated-by-ai"
PROCESSING = "PROCESSING DATA ..."

# Path to service account JSON file
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

# Set up authentication
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(
    SERVICE_ACCOUNT_FILE, scope)
gc = gspread.authorize(creds)

# Open the Google Sheet for the AI agent
GOOGLE_SHEET_URL_FOR_AI_AGENT = os.getenv("GOOGLE_SHEET_URL_FOR_AI_AGENT")
sh = gc.open_by_url(GOOGLE_SHEET_URL_FOR_AI_AGENT)


def generate_audio_URL(name, audio_script):
    file_name = normalize_to_url_friendly(name)
    converter = TextToSpeechConverter()
    output_file = f"output_{file_name}.mp3"
    if converter.synthesize_speech(audio_script, output_file, 0.9, 0.7, 'female'):
        print(f"Text-to-speech conversion for '{output_file}' successful.")
    else:
        print(f"Text-to-speech conversion for '{output_file}' failed.")
        
    file_path = "./" + output_file  # Replace with your actual file path
    s3_key = f"audio/{output_file}"
    
    public_url = upload_audio_to_s3(file_path, s3_key)
    print("Public URL:", public_url if public_url else "Upload failed.")
    
    return public_url


def generate_video_URL(name, description):
    file_name = normalize_to_url_friendly(name)
    # TODO - Implement video generation logic
    return ""


def normalize_to_url_friendly(text):
    # Convert Unicode characters to ASCII (e.g., "Nhân viên" -> "Nhan vien")
    text = unidecode.unidecode(text)
    # Convert to lowercase
    text = text.lower()
    # Replace spaces and special characters with hyphens
    text = re.sub(r'[^a-z0-9]+', '-', text)
    # Remove leading and trailing hyphens
    text = text.strip('-')
    return text


def process_for_group():
    print("=> process_for_group")

    worksheet = sh.get_worksheet(1)
    data = worksheet.get_all_values()
    headers = data[0]
    status_index = headers.index("Status")
    name_index = headers.index("Tên nhóm")
    description_index = headers.index("Mô tả sự kiện truyền thông")
    audio_script_index = headers.index("Audio Script")

    for i, row in enumerate(data[1:], start=2):  # Skip header row
        status = str(row[status_index]).strip().lower()
        if status == "need-to-process":
            name = row[name_index]
            description = row[description_index]
            audio_script = row[audio_script_index].strip()
            

            # processing is started
            worksheet.update_acell(f"E{i}", PROCESSING)  # Update Audio URL
            worksheet.update_acell(f"F{i}", PROCESSING)  # Update Video URL
            
            # Update Audio Script
            if len(audio_script) == 0:
                audio_script = generate_audio_script(name, description)
                worksheet.update_acell(f"D{i}", audio_script)  

            audio_url = generate_audio_URL(name, audio_script)
            video_url = generate_video_URL(name, description)

            # processing is done
            worksheet.update_acell(f"E{i}", audio_url)  # Update Audio URL
            worksheet.update_acell(f"F{i}", video_url)  # Update Video URL

            worksheet.update_acell(f"A{i}", GEN_BY_AI)  # Update Status

            print(f"process_for_group row {i}")


def process_for_personal_profile():
    print("=> process_for_personal_profile")

    worksheet = sh.get_worksheet(0)
    data = worksheet.get_all_values()
    headers = data[0]
    status_index = headers.index("Status")
    name_index = headers.index("Họ tên người nhận")
    description_index = headers.index("Mô tả sự kiện truyền thông")
    audio_script_index = headers.index("Audio Script")

    for i, row in enumerate(data[1:], start=2):  # Skip header row
        status = str(row[status_index]).strip().lower()
        if status == "need-to-process":
            name = row[name_index]
            description = row[description_index]
            audio_script = row[audio_script_index].strip()

            # processing is started
            worksheet.update_acell(f"E{i}", PROCESSING)  # Update Audio URL
            worksheet.update_acell(f"F{i}", PROCESSING)  # Update Video URL
            
             # Update Audio Script
            if len(audio_script) == 0:
                audio_script = generate_audio_script(name, description, "person")
                worksheet.update_acell(f"D{i}", audio_script)

            audio_url = generate_audio_URL(name, audio_script)
            video_url = generate_video_URL(name, description)

            # processing is done
            worksheet.update_acell(f"E{i}", audio_url)  # Update Audio URL
            worksheet.update_acell(f"F{i}", video_url)  # Update Video URL

            worksheet.update_acell(f"A{i}", GEN_BY_AI)  # Update Status

            print(f"process_for_personal_profile row {i}")


if __name__ == "__main__":
    # Schedule jobs to run every 5 seconds
    schedule.every(5).seconds.do(process_for_group)
    schedule.every(5).seconds.do(process_for_personal_profile)

    print("Scheduled jobs. Running scheduler...")
    while True:
        schedule.run_pending()
        time.sleep(1)  # Sleep for a short interval to avoid busy-waiting
