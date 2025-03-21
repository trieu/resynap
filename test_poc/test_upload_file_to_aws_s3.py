from datetime import datetime

import logging
import mimetypes
import boto3
import os
import sys
import unidecode
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)

# AWS Configurations
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")  # Default to us-east-1 if not set
AWS_S3_BUCKET_PUBLIC = os.getenv("AWS_S3_BUCKET_PUBLIC")

# Function to check if AWS credentials are set
def check_aws_credentials():
    if not AWS_ACCESS_KEY or not AWS_SECRET_KEY:
        print("❌ AWS credentials are missing. Please check your .env file or environment variables.")
        sys.exit(1)
    print("✅ AWS credentials are set.")

# Validate credentials before initializing S3 client
check_aws_credentials()

# Initialize S3 Client
s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    #aws_session_token=AWS_SESSION_TOKEN,
)

def upload_file_to_s3(file_path, s3_key):
    """
    Uploads an audio or video file to S3 and makes it publicly accessible.

    :param file_path: Local path to the file
    :param s3_key: The key (path) where the file will be stored in S3
    :return: Public URL of the uploaded file or None if failed
    """
    try:
        # Check if the file exists
        if not os.path.exists(file_path):
            logging.error(f"❌ File not found: {file_path}")
            return None

        # Detect MIME type based on file extension
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            logging.warning("⚠️ Unknown file type, defaulting to binary/octet-stream")
            content_type = "application/octet-stream"

        # Upload file with correct MIME type
        s3.upload_file(
            file_path,
            AWS_S3_BUCKET_PUBLIC,
            s3_key,
            ExtraArgs={"ACL": "public-read", "ContentType": content_type},
        )

        # Construct the public URL with a cache buster
        cache_buster = int(datetime.now().timestamp())
        public_url = f"https://{AWS_S3_BUCKET_PUBLIC}.s3.{AWS_REGION}.amazonaws.com/{s3_key}?t={cache_buster}"

        logging.info(f"✅ File uploaded successfully: {public_url}")
        return public_url

    except Exception as e:
        logging.error(f"❌ Error uploading file: {e}")
        return None

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

# Example Usage
if __name__ == "__main__":
    file_path = "/home/trieu/projects/resynap/resources/generated_videos/video-with-sounds.mp4"  # Replace with your actual file path
    s3_key = "test/video-with-sounds.mp4"  # Define the path inside the S3 bucket

    public_url = upload_file_to_s3(file_path, s3_key)
    print("Public URL:", public_url if public_url else "Upload failed.")