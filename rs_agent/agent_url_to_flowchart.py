

import os
import aiohttp
from bs4 import BeautifulSoup
from google import genai
from dotenv import load_dotenv
from typing import Dict
import hashlib

# --- Load Environment Variables ---
load_dotenv(override=True)

# --- Check for API Key ---
if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("GEMINI_API_KEY environment variable not set.")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_ID = 'gemini-2.0-flash'

# 
NODE_SIZE_LIMIT = 50 
BASE_PROMPT = f'''
You are an expert AI assistant specialized in analyzing text and constructing Causal Graphs.

Instructions:
 - Your primary goal is to synthesize the provided input text into a concise Causal Graph using Mermaid.js (version 10+) Markdown syntax.
 - Identify the key entities, events, states, concepts, and their **causal relationships** described in the text. The graph should clearly illustrate how one element leads to, influences, or causes another.
 - **Infer causal links** based on the context, logical flow, and temporal sequence described in the text, even if words like "causes" or "because" are not explicitly used.
 - **Critical Output Formatting:** The final response MUST contain **ONLY the raw Mermaid code block** for the `graph TD`.
    * **Do NOT** include the markdown fences (```mermaid ... ```).
    * **Do NOT** include any introductory text, explanations, comments, titles, or closing remarks before or after the Mermaid code. Just the code itself.

Constraints: 
- Limit the graph complexity to a **maximum of {NODE_SIZE_LIMIT} nodes**. Concentrate on the most significant causal factors, outcomes, and the primary causal chain(s) presented in the text. Avoid minor details.
- Max 10 nodes per level
-  Represent the causal flow using a top-down directed graph (`graph TD`), the top is the cause and the bottom is the effect.
- **Nodes:** Use the format `id["Concise Label"]`. Each id must start with the prefix n followed by an ordered number (e.g., n1, n2, n3, …). Nodes should represent the core causal elements (actions, events, states, key concepts). Keep labels brief and informative.
-  **Edges:** Use the format `id1 --> id2` to signify that `id1` directly leads to, causes, or enables `id2`. Optionally, for added clarity on the relationship *only when necessary*, you can add a brief description to the link: `id1 -- "link description" --> id2`. Keep link descriptions extremely short if used at all. **Focus on the directed link (`-->`) representing causality.**
- The graph must be complete and fully connected. Every node must have at least one incoming or outgoing edge, forming a single complete causal structure.
-  The output graph (node labels, edge descriptions if any) **must** be in the **same language** as the input text.

Input text to summarize:
'''


# Utility: hash the URL to use as a cache key
def hash_url(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()

class AgentCausalGraph:
   
    
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
                model=self.model_id, contents=prompt, config=genai.types.GenerateContentConfig(temperature=0.7)
            )
            summary_markdown = self.remove_mermaid_fences(response.text.strip())

            return summary_markdown

        except Exception as e:
            return f"Error during summarization: {e}"

# --- Define the State for the Graph ---


class GraphState:
     # Local in-memory cache (URL hash -> Mermaid summary)
    markdown_cache: Dict[str, str] = {}
    text_cache: Dict[str, str] = {}
    
    def __init__(self, url: str):
        self.url = url
        self.extracted_text = ""
        self.summary_markdown = ""
        self.error = None
        
        
    async def process_url(self, no_cache: bool = False):
        cache_key = hash_url(self.url)
       
        # Return from cache if available
        extracted_text = ''
        if cache_key in self.text_cache and not no_cache:
            extracted_text = self.text_cache[cache_key]
        
        # Step 1: Fetch and parse URL
        if len(extracted_text) == 0:
            # Fetch and parse URL
            extracted_text = await fetch_and_parse(self.url)
            self.text_cache[cache_key] = extracted_text
        
        # Return from cache if available
        if cache_key in self.markdown_cache and not no_cache:
            return {"summary_markdown": self.markdown_cache[cache_key], "cached": True, "extracted_text" : extracted_text}

        # double check to make sure not pass empty text for AI agent
        self.extracted_text = extracted_text
        if len(self.extracted_text) == 0:
            self.error = "Failed to extract text from the URL."
            return {"error": self.error}

        # Step 2: Summarize to Mermaid (using AgentCausalGraph class)
        agent = AgentCausalGraph(api_key=GEMINI_API_KEY, model_id=GEMINI_MODEL_ID)
        summary_markdown = agent.generate_mermaid_summary(self.extracted_text)
        self.summary_markdown = summary_markdown

        # Store in cache
        if len(summary_markdown) > 0:
            self.markdown_cache[cache_key] = summary_markdown
            return {"summary_markdown": summary_markdown, "cached": False, "extracted_text" : extracted_text}
        else:
            self.error = "Failed to generate_mermaid_summary from extracted_text."
            return {"error": self.error}
        

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

