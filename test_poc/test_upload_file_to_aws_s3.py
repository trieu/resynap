import boto3
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# AWS Configurations
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")  # Default to us-east-1 if not set
BUCKET_NAME = "media-personalization"

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
    aws_session_token=AWS_SESSION_TOKEN,
)

def upload_audio_to_s3(file_path, s3_key):
    """
    Uploads an audio file to S3 and makes it publicly accessible.

    :param file_path: Local path to the audio file
    :param s3_key: The key (path) where the file will be stored in S3
    :return: Public URL of the uploaded file
    """
    try:
        # Check if file exists before uploading
        if not os.path.exists(file_path):
            print(f"❌ Error: File '{file_path}' does not exist.")
            return None

        # Upload the file with public-read ACL
        s3.upload_file(
            file_path,
            BUCKET_NAME,
            s3_key,
            ExtraArgs={"ACL": "public-read", "ContentType": "audio/mpeg"},
        )

        # Construct the public URL
        public_url = f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        print(f"✅ File uploaded successfully: {public_url}")
        return public_url
    except Exception as e:
        print(f"❌ Error uploading file: {e}")
        return None

# Example Usage
file_path = "/home/trieu/projects/resynap/resources/generated_videos/video-with-sounds.mp4"  # Replace with your actual file path
s3_key = "test/video-with-sounds.mp4"  # Define the path inside the S3 bucket

public_url = upload_audio_to_s3(file_path, s3_key)
print("Public URL:", public_url if public_url else "Upload failed.")