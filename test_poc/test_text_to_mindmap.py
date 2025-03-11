from google import genai
from google.genai import types

from PIL import Image
from io import BytesIO

import os
from dotenv import load_dotenv
import re
import unicodedata

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Usegemini-2.0-flash for fast mindmap generation
GEMINI_MODEL_ID = "gemini-2.0-flash"

# Configure your API key
genai_client = genai.Client(api_key=GEMINI_API_KEY)

def generate_mindmap_and_prompts(main_title):
    """
    Generates a Mermaid.js mindmap and a list of prompts based on the main title.
    Prompts are only generated from level 1 nodes.

    Args:
        main_title: The main title to base the mindmap and prompts on.

    Returns:
        A tuple containing the Mermaid.js mindmap string and a list of prompts.
    """

    mindmap_prompt = f"""
    Create a mindmap structure in mermaid.js format based on the following title: "{main_title}".
    Focus on breaking down the main title into related concepts and subtopics.
    Do not include any explanation, just the mermaid mindmap code in plain text.
    """

    mindmap_response = genai_client.models.generate_content(model=GEMINI_MODEL_ID, contents=mindmap_prompt)
    mindmap = mindmap_response.text

    lines = mindmap.split('\n')
    level_1_nodes = []

    for line in lines:
        if "-->" in line:  # Check for level 1 connections
            parts = line.split("-->")
            if len(parts) == 2:
                parent = parts[0].strip()
                child = parts[1].strip()

                if parent.startswith("root"):  # only get the childs of root.
                    if '(' in child and '))' in child:
                        node_text = child.split('((')[1].split('))')[0].strip()
                        level_1_nodes.append(node_text)
                        print(node_text)

    return mindmap


def build_prompts_from_mindmap(mindmap_text):
    lines = mindmap_text.strip().split("\n")
    nodes = []
    
    # Detect the indentation level of the root node
    base_indent = None

    for line in lines[3:]:  # Skip the first line "mindmap"
        if line == "```":
            continue

        match = re.match(r"^(\s*)(\S.*)", line)
        if match:
            indent_level = len(match.group(1)) // 2  # Assuming 2 spaces per level
            node = re.split(r"\[|\(|\{", match.group(2), 1)[0].strip()  # Extract node name
            
            if base_indent is None:  # First indented node sets the base level
                base_indent = indent_level
            
            if indent_level == base_indent:  # Ensure only direct children of root
                nodes.append(node)
    return nodes

def mindmap_to_image(prompts: list):
    # Create a folder to save images if it doesn't exist
    output_folder = "generated_images"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
     
    images = []   
    for prompt in prompts:
        print('prompt '+prompt)
        name = text_to_filename(prompt)
    
        response = genai_client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt='In creative way, visualize this concept: ' + prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type='image/jpeg'
            )
        )

        if response and response.generated_images:
            for i, generated_image in enumerate(response.generated_images):
                image = Image.open(BytesIO(generated_image.image.image_bytes))

                # Ensure a unique filename
                image_filename = f"generated_image_{name}_{i}.jpg" 
                image_path = os.path.join(output_folder, image_filename)
                image.save(image_path)
                print(f"Image saved to: {image_path}")
                images.append(image_path)
        else:
            print("No images generated.")

    return images


def text_to_filename(text: str, max_length: int = 255) -> str:
    # Normalize text to remove accents
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    # Replace spaces and special characters with underscores
    text = re.sub(r"[^\w\-]", "_", text)
    # Trim to max length
    return text[:max_length]

# Example usage
main_title = "Lazy orange cat in my kitchen with a cup of coffee"
mindmap = generate_mindmap_and_prompts(main_title)


prompts = build_prompts_from_mindmap(mindmap)

print("Mindmap:")
print(mindmap)

print("\nPrompts:")
print(prompts)


mindmap_to_image(prompts)



