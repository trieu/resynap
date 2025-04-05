
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, FileResponse
import os
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from google import genai
from dotenv import load_dotenv

# --- Load Environment Variables ---
load_dotenv(override=True)

# --- Check for API Key ---
if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("GEMINI_API_KEY environment variable not set.")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_ID = 'gemini-2.0-flash'

BASE_PROMPT = '''
You are an expert text summarizer as flowchart.

Instructions:
1. Your task is to summarize the provided input text into a flowchart using Mermaid.js version 10 Markdown syntax.
2. The flowchart should represent the main steps, concepts, or flow described in the text.
3. The output **must** have the same language as the input text.
4. Use a simple top-down flowchart (`graph TD`). Example node format: id["Label"]. Example edge format: id1 --> id2["Label"].
5. Keep the flowchart concise and focused on the core information.
6. Ensure all nodes and all edges must be connected as flowchart
7. Ensure the output is ONLY the raw Mermaid code block. 
8. Do not include mermaid fences ```mermaid" at the beginning or "```" at the end, and no other explanatory text.

Input Text to summarize:
'''

app = FastAPI()

# --- Class to Handle Google Gemini API Calls ---


class GeminiAPI:
    def __init__(self, api_key: str, model_id: str):
        self.client = genai.Client(api_key=api_key)
        self.model_id = model_id

    def remove_mermaid_fences(self, text: str) -> str:
        """
        Removes the first line if it exactly matches '```mermaid' (after stripping whitespace)
        and the last line if it exactly matches '```' (after stripping whitespace).

        Args:
            text: The input string potentially containing Mermaid fences.

        Returns:
            The string with the specified fences removed, if they were present.
        """
        if not text:
            return ""  # Return empty string if input is empty

        lines = text.splitlines()

        # Check and remove the first line if it's the opening fence
        if lines and lines[0].strip() == '```mermaid':
            lines.pop(0)  # Remove the first element

        # Check and remove the last line if it's the closing fence
        # Need to check 'if lines' again in case the input was only '```mermaid'
        if lines and lines[-1].strip() == '```':
            lines.pop(-1)  # Remove the last element

        # Join the remaining lines back together
        return "\n".join(lines)

    def generate_mermaid_summary(self, text: str) -> str:
        """
        Generates a Mermaid.js flowchart summary from the provided text.
        Uses Google Gemini API for summarization.
        """
        # Optimized Prompt 1 (Minimal changes, grammar fix, slight rephrase)
        prompt = f"""
        {BASE_PROMPT}
        {text}
        """
        try:
            # Call Google Gemini API
            response = self.client.models.generate_content(
                model=self.model_id, contents=prompt, config=genai.types.GenerateContentConfig(temperature=0.6)
            )
            summary_markdown = (response.text.strip())

            return self.remove_mermaid_fences(summary_markdown)

        except Exception as e:
            return f"Error during summarization: {e}"

# --- Define the State for the Graph ---


class GraphState:
    def __init__(self, url: str):
        self.url = url
        self.extracted_text = ""
        self.summary_markdown = ""
        self.error = None


async def fetch_and_parse(url: str) -> str:
    """
    Fetches content from a URL, parses HTML, and extracts text.
    """
    extracted_text = ""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as response:
                response.raise_for_status()
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'lxml')

                # Remove script and style elements
                for script_or_style in soup(["script", "style"]):
                    script_or_style.decompose()

                text = soup.get_text()
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip()
                          for line in lines for phrase in line.split("  "))
                extracted_text = '\n'.join(chunk for chunk in chunks if chunk)

    except Exception as e:
        return f"Error fetching or parsing URL: {e}"

    return extracted_text

# --- Endpoint to process the URL and return the Mermaid markdown ---


@app.post("/generate_mermaid/")
async def generate_mermaid(url: str = Form(...)):
    state = GraphState(url=url)

    # Step 1: Fetch and parse URL
    extracted_text = await fetch_and_parse(state.url)
    state.extracted_text = extracted_text

    if not state.extracted_text:
        state.error = "Failed to extract text from the URL."
        return {"error": state.error}

    # Step 2: Summarize to Mermaid (using GeminiAPI class)
    gemini_api = GeminiAPI(api_key=GEMINI_API_KEY, model_id=GEMINI_MODEL_ID)
    summary_markdown = gemini_api.generate_mermaid_summary(
        state.extracted_text)
    state.summary_markdown = summary_markdown

    return {"summary_markdown": state.summary_markdown}

# --- Serve the Static HTML File (index.html) ---


@app.get("/", response_class=HTMLResponse)
async def home():
    # Serve the index.html file from disk
    return FileResponse("./resources/templates/text-to-flow.html")

# --- Run the FastAPI app ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
