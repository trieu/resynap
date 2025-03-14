from moviepy import ImageClip, concatenate_videoclips, TextClip, VideoFileClip, AudioFileClip
from PIL import Image
from google.genai import types, Client
from io import BytesIO
import numpy as np
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def add_audio_to_video(video_path, audio_path, output_path):
    """Adds an audio file to a video file using MoviePy."""
    try:
        video_clip = VideoFileClip(video_path)
        audio_clip = AudioFileClip(audio_path)

        # Ensure the audio duration matches the video duration
        audio_clip = audio_clip.subclip(0, video_clip.duration)

        # Set the audio of the video clip
        video_clip = video_clip.set_audio(audio_clip)

        # Write the final video with audio
        video_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

        video_clip.close()
        audio_clip.close()

        print(f"Audio added to video successfully. Output: {output_path}")

    except Exception as e:
        print(f"Error adding audio to video: {e}")
