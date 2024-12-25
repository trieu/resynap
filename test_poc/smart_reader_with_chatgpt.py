import os
import fitz  # PyMuPDF for extracting text from PDF
import openai
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from transformers import AutoTokenizer, AutoModel
import json

# Initialize Qdrant Client
qdrant_client = QdrantClient("http://localhost", port=6333)
COLLECTION_NAME = "book_vectors"

# Load GPT model and tokenizer (change model if needed)
tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file."""
    text = ""
    with fitz.open(pdf_path) as pdf:
        for page in pdf:
            text += page.get_text()
    return text

def store_text_as_json_and_qdrant(text, file_name):
    """Store extracted text in JSON and Qdrant."""
    # Save to JSON
    json_file_path = f"{file_name}.json"
    with open(json_file_path, "w") as f:
        json.dump({"content": text}, f)
    print(f"Text saved to {json_file_path}")

    # Save to Qdrant
    tokens = tokenizer(text, truncation=True, max_length=512, return_tensors="pt")
    vector = model(**tokens).last_hidden_state.mean(dim=1).squeeze().detach().numpy()

    point = PointStruct(id=1, vector=vector.tolist(), payload={"text": text})
    qdrant_client.upsert(COLLECTION_NAME, points=[point])
    print(f"Text vector stored in Qdrant collection '{COLLECTION_NAME}'")

def query_chatgpt(prompt):
    """Send a query to OpenAI GPT model."""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"]

def summarize_key_ideas(text):
    """Summarize key ideas using ChatGPT."""
    prompt = f"Summarize the key ideas of the following text:\n{text}"
    return query_chatgpt(prompt)

def create_slides_in_markdown(text):
    """Generate slide content in markdown using ChatGPT."""
    prompt = f"Generate slide content in markdown for the following text:\n{text}"
    return query_chatgpt(prompt)

if __name__ == "__main__":
    # Example usage
    pdf_path = "example_book.pdf"  # Replace with your PDF file
    file_name = "example_book"

    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)

    # Store text as JSON and in Qdrant
    store_text_as_json_and_qdrant(text, file_name)

    # Summarize key ideas
    summary = summarize_key_ideas(text)
    print("\nSummary:", summary)

    # Create slides in markdown
    slides = create_slides_in_markdown(text)
    print("\nSlides in Markdown:\n", slides)
