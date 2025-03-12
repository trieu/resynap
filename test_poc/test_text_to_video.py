from moviepy import ImageClip, concatenate_videoclips, TextClip
from PIL import Image
from google.genai import types, Client
from io import BytesIO
import numpy as np
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Usegemini-2.0-flash for fast mindmap generation
GEMINI_MODEL_ID = "gemini-2.0-flash"

genai_client = Client(api_key=GEMINI_API_KEY)

# Configuration
OUTPUT_IMAGE_FOLDER = "resources/generated_images"
OUTPUT_VIDEO_FOLDER = "resources/generated_videos"
IMAGE_DURATION = 4  # Seconds per image in the video
FONT_SIZE = 40
FONT_COLOR = "white"
FONT_PATH = "Arial"  # Ensure this font exists on the system

def setup_directories():
    os.makedirs(OUTPUT_IMAGE_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_VIDEO_FOLDER, exist_ok=True)

def generate_prompts(main_title, num_prompts=3):
    """Generates multiple prompts based on a main title using Google GenAI."""

    prompt = f"""
    Given the main title: "{main_title}", generate {num_prompts} variations of creative prompts. 
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

def generate_images(prompts, num_images_per_prompt=1):
    """Generates images using Google GenAI and saves them to disk."""
    image_clips = []
    image_counter = 1
    
    for prompt in prompts:

        response = genai_client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt='In creative way, visualize this concept: ' + prompt,
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
                image_clip = ImageClip(np.array(image)).with_duration(IMAGE_DURATION)
                description_clip = create_text_clip(prompt, IMAGE_DURATION)
                combined_clip = concatenate_videoclips([image_clip, description_clip])
                image_clips.append(combined_clip)
    
    return image_clips

def generate_video(main_title):
    """Generates a video using AI-generated images and text."""
    setup_directories()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_filename = os.path.join(OUTPUT_VIDEO_FOLDER, f"generated_video_{timestamp}.mp4")
    
    prompts = generate_prompts(main_title)
    image_clips = generate_images(prompts)
    
    title_clip = create_text_clip(main_title, 5)
    summary_clip = create_text_clip("Thank you for watching!", 5)
    
    video_clips = [title_clip] + image_clips + [summary_clip]
    final_video = concatenate_videoclips(video_clips, method="compose")
    final_video.write_videofile(video_filename, fps=24)
    
    print(f"Video saved to: {video_filename}")
    return video_filename

# Example usage
if __name__ == "__main__":
    
    ideas = "Tạo một video minh họa về Microlearning với mindmap trực quan, trình bày các khái niệm chính như bài học ngắn, lợi ích, định dạng (short video, flashcard), và ứng dụng trong đào tạo nhân viên, phát triển kỹ năng, phát triển bản thân."

    generate_video(ideas)
