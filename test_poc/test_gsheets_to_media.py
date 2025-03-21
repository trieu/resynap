from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import schedule
import time

# Import core functions
from test_text_to_speech import TextToSpeechConverter
from test_ideas_to_audio_script import generate_audio_script, generate_video_title
from test_text_to_video import generate_video
from test_upload_file_to_aws_s3 import upload_file_to_s3, normalize_to_url_friendly

load_dotenv(override=True)

GEN_BY_AI = "generated-by-ai"
PROCESSING = "PROCESSING DATA ..."

# Path to service account JSON file
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
GOOGLE_SHEET_URL_FOR_AI_AGENT = os.getenv("GOOGLE_SHEET_URL_FOR_AI_AGENT")

# Set up authentication
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(
    SERVICE_ACCOUNT_FILE, scope)

# Open the Google Sheet for the AI agent
google_sheet = gspread.authorize(creds).open_by_url(GOOGLE_SHEET_URL_FOR_AI_AGENT)

#  Generate audio URL
def generate_audio_URL(name, audio_script):
    file_name = normalize_to_url_friendly(name)
    output_file = f"output_{file_name}.mp3"
    
    # Generate audio file
    converter = TextToSpeechConverter()
    
    # Synthesize speech
    if converter.synthesize_speech(audio_script, output_file, 0.99, 0.8, 'female'):
        print(f"Text-to-speech conversion for '{output_file}' successful.")
    else:
        print(f"Text-to-speech conversion for '{output_file}' failed.")
        
    file_path = "./" + output_file  # Replace with your actual file path
    s3_key = f"audio/{output_file}"
    
    public_url = upload_file_to_s3(file_path, s3_key)
    print("Public URL:", public_url if public_url else "Upload failed.")
    
    return file_path, public_url


# Generate video URL
def generate_video_URL(name, description, localfile):
    file_name = normalize_to_url_friendly(name)
    
    # Generate video with audio
    video_url = generate_video(name, description, localfile)
    print(f"Video URL: {video_url}")
    
    file_path = "./" + video_url  
    s3_key = f"video/{file_name}.mp4"
    
    public_url = upload_file_to_s3(file_path, s3_key)
    print("Public URL:", public_url if public_url else "Upload failed.")
    
    return public_url


def process_for_group():
    print("=> process_for_group")

    worksheet = google_sheet.get_worksheet(1)
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
            worksheet.format(f"E{i}:F{i}", {'textFormat': {'bold': True,"fontSize": 16}})

            worksheet.update_acell(f"E{i}", PROCESSING)  # Update Audio URL
            worksheet.update_acell(f"F{i}", PROCESSING)  # Update Video URL
            
            # Update Audio Script
            if len(audio_script) == 0:
                audio_script = generate_audio_script(name, description)
                worksheet.update_acell(f"D{i}", audio_script)  

            # Generate audio URL
            localfile, audio_url = generate_audio_URL(name, audio_script)
            worksheet.update_acell(f"E{i}", audio_url)  # Update Audio URL
            
            # Generate video URL
            video_url = generate_video_URL(name, description, localfile)
            worksheet.update_acell(f"F{i}", video_url)  # Update Video URL

            # processing is done
            worksheet.update_acell(f"A{i}", GEN_BY_AI)  # Update Status
            worksheet.format(f"E{i}:F{i}", {'textFormat': {'bold': False,"fontSize": 10}})

            print(f"process_for_group row {i}")


def process_for_personal_profile():
    print("=> process_for_personal_profile")

    worksheet = google_sheet.get_worksheet(0)
    data = worksheet.get_all_values()
    headers = data[0]
    status_index = headers.index("Status")
    name_index = headers.index("Họ tên người nhận")
    description_index = headers.index("Mô tả sự kiện truyền thông")
    audio_script_index = headers.index("Audio Script")

    for i, row in enumerate(data[1:], start=2):  # Skip header row
        status = str(row[status_index]).strip().lower()
        name = row[name_index]
        description = row[description_index]
        if status == "need-to-process" and len(name) > 0 and len(description) > 0:
            
            audio_script = row[audio_script_index].strip()

            # processing is started
            worksheet.update_acell(f"E{i}", PROCESSING)  # Update Audio URL
            worksheet.update_acell(f"F{i}", PROCESSING)  # Update Video URL
            
             # Update Audio Script
            if len(audio_script) == 0:
                worksheet.update_acell(f"D{i}", PROCESSING)
                audio_script = generate_audio_script(name, description, "person")
                worksheet.update_acell(f"D{i}", audio_script)

            # Generate audio URL
            localfile, audio_url = generate_audio_URL(name, audio_script)
            worksheet.update_acell(f"E{i}", audio_url)  # Update Audio URL
            
            # Generate video URL
            video_url = generate_video_URL(name, description, localfile)
            worksheet.update_acell(f"F{i}", video_url)  # Update Video URL

            # processing is done
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
