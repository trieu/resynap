from moviepy import ImageClip, concatenate_videoclips, TextClip, afx, AudioFileClip, CompositeAudioClip
from PIL import Image
from google.genai import types, Client
from io import BytesIO
import numpy as np
from datetime import datetime
import os
from dotenv import load_dotenv

from test_ideas_to_audio_script import generate_video_title

# Load environment variables
load_dotenv(override=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Use gemini-2.0-flash for fast mindmap generation
GEMINI_MODEL_ID = "gemini-2.0-flash"

genai_client = Client(api_key=GEMINI_API_KEY)

# Configuration
OUTPUT_IMAGE_FOLDER = "resources/generated_images"
OUTPUT_VIDEO_FOLDER = "resources/generated_videos"
IMAGE_DURATION = 4  # Seconds per image in the video
FONT_SIZE = 50
FONT_COLOR = "white"
FONT_PATH = "Arial"  # Ensure this font exists on the system

def setup_directories():
    os.makedirs(OUTPUT_IMAGE_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_VIDEO_FOLDER, exist_ok=True)

def generate_prompts(description, num_prompts=1):
    """Generates multiple prompts based on a main title using Google GenAI."""

    prompt = f"""
    Given the main title: "{description}", generate {num_prompts} variations of creative prompts. 
    Focus on varying the style, details, and perspective.
    Return each prompt on a new line.
    """
    response = genai_client.models.generate_content(model=GEMINI_MODEL_ID, contents=prompt)

    return response.text.strip().split('\n')

def create_text_clip(text, duration):
    """Creates a text clip with the given text and duration."""
    return TextClip(
        text=text,
        font_size=FONT_SIZE,
        color=FONT_COLOR,
        font=FONT_PATH,
        size=(1280, None),
        method="caption"
    ).with_duration(duration)

def generate_image_videos(prompts, num_images_per_prompt=1, duration=IMAGE_DURATION):
    """Generates images using Google GenAI and saves them to disk."""
    image_clips = []
    image_counter = 1
    
    for prompt in prompts:

        final_prompt = f"Generate an image to visualize the concept: '{prompt}'. Ensure the image is free of any text and represents the concept clearly."
        
        response = genai_client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=final_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=num_images_per_prompt,
                output_mime_type='image/jpeg'
            )
        )

        if response and response.generated_images:
            for generated_image in response.generated_images:
                image = Image.open(BytesIO(generated_image.image.image_bytes))
                image_path = os.path.join(OUTPUT_IMAGE_FOLDER, f"image_{image_counter}.png")
                image.save(image_path)
                image_counter += 1

                # Create image clip
                image_clip = ImageClip(np.array(image)).with_duration(duration)
                # description_clip = create_text_clip(prompt, IMAGE_DURATION)
                # combined_clip = concatenate_videoclips([image_clip, description_clip])
                image_clips.append(image_clip)
    
    return image_clips



def generate_video(name, description, audio_path) -> str:
    """Generates a video using AI-generated images and text."""
    setup_directories()
    # Generate a timestamped filename for the video
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Define the output video filename
    video_filename = os.path.join(OUTPUT_VIDEO_FOLDER, f"generated_video_{timestamp}.mp4")
    
    # Generate a title for the video
    title = generate_video_title(name, description)
    
    # Load the audio file from the path provided
    audio_voice = AudioFileClip(audio_path)
    
    # Load the audio file for background music
    background_music_path = "/home/trieu/Music/joe-hisaishi-summer.mp3"
    audio_music = AudioFileClip(background_music_path)
    audio_music = audio_music.with_effects([afx.MultiplyStereoVolume(left=0.2, right=0.2)])  # Reduce music volume to 30%

    # Merge by overlaying both audios
    final_audio = CompositeAudioClip([audio_voice, audio_music])
    print(f"Audio {audio_path} duration: {audio_voice.duration} seconds")
    
    # Generate images based on the prompts
    image_clips = generate_image_videos( [title] , num_images_per_prompt=1, duration=audio_voice.duration)
    
    # Add a title clip at the beginning    
    title_clip = create_text_clip(title + ' ' + name, 5)
    
    # Add a summary clip at the end
    summary_clip = create_text_clip("Thank you!", 5)
    
    video_clips = [title_clip] + image_clips + [summary_clip]
    draft_video = concatenate_videoclips(video_clips, method="compose")
    
    # Set the audio of the video clip
    final_video = draft_video.with_audio(final_audio)
    
    final_video.write_videofile(video_filename, fps=24, audio_codec='aac')
    
    print(f"Video saved to: {video_filename}")
    return video_filename



# Example usage
if __name__ == "__main__":
    
    name = 'Triều'
    description = '''
    Chào mừng nhân viên mới phòng CNTT với checklist:
        1) Giới thiệu Team 
        2) Môi trường làm việc
        3)  Giới thiệu các sản phẩm của phòng CNTT
    '''
    audio_path = "/home/trieu/sounds/audio_trieu.mp3"
    
    video_url = generate_video(name, description, audio_path)
    print(f"Video URL: {video_url}")
