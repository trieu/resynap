
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

# 
NODE_SIZE_LIMIT = 25 
BASE_PROMPT = f'''
You are an expert AI assistant specialized in analyzing text and constructing Causal Graphs.

Instructions:
1.  Your primary goal is to synthesize the provided input text into a concise Causal Graph using Mermaid.js (version 10+) Markdown syntax.
2.  Identify the key entities, events, states, concepts, and their **causal relationships** described in the text. The graph should clearly illustrate how one element leads to, influences, or causes another.
3.  **Infer causal links** based on the context, logical flow, and temporal sequence described in the text, even if words like "causes" or "because" are not explicitly used.
4.  Represent the causal flow using a **top-down directed graph (`graph TD`)**.
5.  **Nodes:** Use the format `id["Concise Label"]`. Nodes should represent the core causal elements (actions, events, states, key concepts). Keep labels brief and informative.
6.  **Edges:** Use the format `id1 --> id2` to signify that `id1` directly leads to, causes, or enables `id2`. Optionally, for added clarity on the relationship *only when necessary*, you can add a brief description to the link: `id1 -- "link description" --> id2`. Keep link descriptions extremely short if used at all. **Focus on the directed link (`-->`) representing causality.**
7.  **Connectivity:** The graph must be fully connected. Every node must have at least one incoming or outgoing edge, forming a single coherent causal structure. No isolated nodes or disconnected sub-graphs are allowed.
8.  **Conciseness and Focus:** Limit the graph complexity to a **maximum of {NODE_SIZE_LIMIT} nodes**. Concentrate on the most significant causal factors, outcomes, and the primary causal chain(s) presented in the text. Avoid minor details.
9.  **Language:** The output graph (node labels, edge descriptions if any) **must** be in the **same language** as the input text.
10. **Critical Output Formatting:** The final response MUST contain **ONLY the raw Mermaid code block** for the `graph TD`.
    * **Do NOT** include the markdown fences (```mermaid ... ```).
    * **Do NOT** include any introductory text, explanations, comments, titles, or closing remarks before or after the Mermaid code. Just the code itself.

Input text to summarize:
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
            summary_markdown = self.remove_mermaid_fences(response.text.strip())

            return summary_markdown

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
