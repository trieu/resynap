import warnings
warnings.filterwarnings("ignore")

import fitz  # PyMuPDF
import re
import google.generativeai as genai
import os

from dotenv import load_dotenv
load_dotenv()

GEMINI_MODEL = 'models/gemini-1.5-flash-latest'
GOOGLE_GENAI_API_KEY = os.getenv("GOOGLE_GENAI_API_KEY")

if GOOGLE_GENAI_API_KEY is None or len(GOOGLE_GENAI_API_KEY) == 0:
    print('GOOGLE_GENAI_API_KEY is empty')
    exit

genai.configure(api_key=GOOGLE_GENAI_API_KEY)


def insert_separator_before_headings(text):
    """Inserts a separator before level 2 headings (##) in a text string.

    Args:
        text: The input text string.

    Returns:
        The modified text string with separators inserted.
    """

    return re.sub(r'(?m)^##', r'\n---\n##', text)


def text_to_slides(extracted_text: str):
    """using Google Gemini to convert long text into summary slides

    Args:
        extracted_text (str): a long text

    Returns:
        slides_in_markdown (str): slides in markdown code
    """
    gemini_model = genai.GenerativeModel(model_name=GEMINI_MODEL)
    model_config = genai.GenerationConfig(temperature=0.5)
    
    context = "You are book reader. You can do book summary into slides in markdown."
    context = context + " Each slide must begins with '##'. Write summary slides for this content: \n "
    prompt = context + extracted_text

    response = gemini_model.generate_content(prompt, generation_config=model_config)
    return insert_separator_before_headings(response.text)


def extract_text_from_pdf(pdf_path, start_page, end_page):
    """
    Extract text from a PDF file between specified page numbers.

    :param pdf_path: Path to the PDF file.
    :param start_page: Starting page number (1-indexed).
    :param end_page: Ending page number (1-indexed).
    :return: Extracted text as a string.
    """
    extracted_text = ""

    try:
        # Open the PDF file
        with fitz.open(pdf_path) as pdf_document:
            # Ensure page range is within document bounds
            total_pages = pdf_document.page_count
            start_page = max(1, start_page)  # Minimum page is 1
            # Maximum page is total pages
            end_page = min(end_page, total_pages)

            # Loop through specified pages and extract text
            for page_num in range(start_page - 1, end_page):  # Convert to 0-indexed
                page = pdf_document[page_num]
                extracted_text += page.get_text()

    except Exception as e:
        print(f"An error occurred: {e}")

    return extracted_text

def write_text_to_file(text: str, filename="summary-slides.md"):
    """Writes text to a file.

    Args:
        text: The text to write.
        filename: The name of the file (default: "summary-slides.md").
    """
    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(text)
        print(f"Text written to {filename} successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")


# ---------------------------
# Replace with your PDF file path
pdf_path = "/home/thomas/Documents/CDP/aws-in-action.pdf"
start_page = 200
end_page = 232

# extract text form PDF file
extracted_text = extract_text_from_pdf(pdf_path, start_page, end_page)

# summary slides
slides_in_md = text_to_slides(extracted_text)

# write to file or save into database
write_text_to_file(slides_in_md, filename="chapter8.md")

print("\n -------------------------- ")
print(slides_in_md)