from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import os
from dotenv import load_dotenv

load_dotenv()

IMAGE_MODEL_ID = os.getenv("IMAGE_MODEL_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Create a genai client
client = genai.Client(api_key=GEMINI_API_KEY)

# Create a folder to save images if it doesn't exist
output_folder = "resources/generated_images"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

profiles = [{"name": "Linh", "gender": "male", "age_range": " 30 to 35"}]
profiles2 = [{"name": "Hong", "gender": "female", "age_range": " 25 to 30"},
             {"name": "Trieu", "gender": "male", "age_range": " 35 to 40"}]

for profile in profiles:

    name = profile["name"]
    gender = profile["gender"]
    age_range = profile["age_range"]

    if gender == "male":
        gender_term = "man"
    elif gender == "female":
        gender_term = "woman"
    else:
        gender_term = "person"  # Default if gender is not specified

    the_prompt = f"In creative way, create a happy {gender_term} avatar with text '{name}' as description, a {gender} in the age range from {age_range}."
    print(the_prompt)

    response = client.models.generate_images(
        model=IMAGE_MODEL_ID,
        prompt=the_prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            output_mime_type='image/jpeg'
        )
    )

    if response.generated_images:
        for i, generated_image in enumerate(response.generated_images):
            image = Image.open(BytesIO(generated_image.image.image_bytes))

            # Save the image to the folder with a unique filename
            image_filename = f"generated_image_{name}.jpg"
            image_path = os.path.join(output_folder, image_filename)
            image.save(image_path)
            print(f"Image saved to: {image_path}")

            # Optionally, you can still show the image
            # image.show()
    else:
        print("No images generated.")
