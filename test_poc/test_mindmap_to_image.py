from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

# Create a folder to save images if it doesn't exist
output_folder = "generated_images"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
    
    
mindmap = """ ```mermaid
mindmap
  root((Lazy orange cat in my kitchen with a cup of coffee))
    Cat
      Lazy
        Sleeping
        Stretching
      Orange
        Fur color
        Breed (Optional)
      Behavior
        Purring
        Meowing
    Kitchen
      Location
        Home
      Furniture
        Counter
        Table
        Chair
      Smells
        Coffee
        Food
    Coffee
      Cup
        Ceramic
        Glass
      Type
        Hot
        Iced (less likely)
      Aroma
        Strong
        Mild
    Atmosphere
      Relaxed
      Morning
      Quiet
``` """

response = client.models.generate_images(
    model='imagen-3.0-generate-002',
    prompt='Visualize relationship graph with clear text from the following mindmap:\n ' + mindmap,
    config=types.GenerateImagesConfig(
        number_of_images=1,
    )
)

for i, generated_image in enumerate(response.generated_images):
    image = Image.open(BytesIO(generated_image.image.image_bytes))

    # Save the image to the folder with a unique filename
    image_filename = f"generated_image_{i + 1}.png"  # or .jpg, etc.
    image_path = os.path.join(output_folder, image_filename)
    image.save(image_path)
    print(f"Image saved to: {image_path}")

    # Optionally, you can still show the image
    # image.show()