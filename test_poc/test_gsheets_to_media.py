from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import unidecode
import re
import time


# Load environment variables
load_dotenv(override=True)

GEN_BY_AI = "generated-by-ai"
PROCESSING = "PROCESSING"

# Path to service account JSON file
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

# Set up authentication
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
gc = gspread.authorize(creds)

# Open the Google Sheet for the AI agent
GOOGLE_SHEET_URL_FOR_AI_AGENT = os.getenv("GOOGLE_SHEET_URL_FOR_AI_AGENT")
sh = gc.open_by_url(GOOGLE_SHEET_URL_FOR_AI_AGENT)


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


def generate_audio_URL(name, description):
    file_name = normalize_to_url_friendly(name)
    time.sleep(3)  # Simulate processing time
    return f"https://audio.example.com/{file_name}.mp3"


def generate_video_URL(name, description):
    file_name = normalize_to_url_friendly(name)
    time.sleep(3)  # Simulate processing time
    return f"https://video.example.com/{file_name}.mp4"


def process_for_group():
    print("Processing for group...")
    
    worksheet = sh.get_worksheet(1)
    data = worksheet.get_all_values()
    headers = data[0]
    status_index = headers.index("Status")
    name_index = headers.index("Tên nhóm")
    description_index = headers.index("Mô tả sự kiện truyền thông")

    for i, row in enumerate(data[1:], start=2):  # Skip header row
        status = str(row[status_index]).strip().lower()
        if  status == "need-to-process":
            name = row[name_index]
            description = row[description_index]
            
            # processing is started
            worksheet.update_acell(f"E{i}", PROCESSING)  # Update Audio URL
            worksheet.update_acell(f"F{i}", PROCESSING)  # Update Video URL
            
            audio_url = generate_audio_URL(name, description)
            video_url = generate_video_URL(name, description)

             # processing is done
            worksheet.update_acell(f"E{i}", audio_url)  # Update Audio URL
            worksheet.update_acell(f"F{i}", video_url)  # Update Video URL
            
            worksheet.update_acell(f"A{i}", GEN_BY_AI)  # Update Status
            
            print(f"process_for_group row {i}")


def process_for_personal_profile():
    print("Processing for personal profile...")
    
    worksheet = sh.get_worksheet(0)
    data = worksheet.get_all_values()
    headers = data[0]
    status_index = headers.index("Status")
    name_index = headers.index("Họ tên người nhận")
    description_index = headers.index("Mô tả sự kiện truyền thông")

    for i, row in enumerate(data[1:], start=2):  # Skip header row
        status = str(row[status_index]).strip().lower()
        if  status == "need-to-process":
            name = row[name_index]
            description = row[description_index]
            
            # processing is started
            worksheet.update_acell(f"E{i}", PROCESSING)  # Update Audio URL
            worksheet.update_acell(f"F{i}", PROCESSING)  # Update Video URL
            
            audio_url = generate_audio_URL(name, description)
            video_url = generate_video_URL(name, description)

             # processing is done
            worksheet.update_acell(f"E{i}", audio_url)  # Update Audio URL
            worksheet.update_acell(f"F{i}", video_url)  # Update Video URL
            
            worksheet.update_acell(f"A{i}", GEN_BY_AI)  # Update Status
            
            print(f"process_for_personal_profile row {i}")

if __name__ == "__main__":
    # Run functions in a loop every 5 seconds
    while True:
        process_for_group()
        process_for_personal_profile()
        time.sleep(5) 
