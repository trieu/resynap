import os
import asyncio
from typing import TypedDict, Annotated, List
from dotenv import load_dotenv

import aiohttp
from bs4 import BeautifulSoup
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

# --- Load Environment Variables ---
load_dotenv(override=True)


# --- Check for API Key ---
if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("GEMINI_API_KEY environment variable not set.")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Define the State for the Graph ---
# This dictionary holds the data passed between nodes.


class GraphState(TypedDict):
    url: str                # Input URL
    extracted_text: str     # Text extracted from the URL
    summary_markdown: str   # Final Mermaid Markdown summary
    error: str | None       # To capture any errors during the process

# --- Define Graph Nodes ---


async def fetch_and_parse(state: GraphState) -> dict:
    """
    Fetches content from a URL, parses HTML, and extracts text.
    Updates the state with the extracted text or an error message.
    """
    print("--- Node: Fetching and Parsing URL ---")
    url = state['url']
    extracted_text = ""
    error = None

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as response:  # Added timeout
                response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'lxml')  # Using lxml parser

                # Basic text extraction (can be improved)
                # Remove script and style elements
                for script_or_style in soup(["script", "style"]):
                    script_or_style.decompose()

                # Get text, strip leading/trailing whitespace, join lines
                text = soup.get_text()
                lines = (line.strip() for line in text.splitlines())
                # Handle multiple spaces
                chunks = (phrase.strip()
                          for line in lines for phrase in line.split("  "))
                extracted_text = '\n'.join(chunk for chunk in chunks if chunk)

                if not extracted_text:
                    print(f"Warning: No text extracted from {url}")
                    error = f"No text could be extracted from the URL: {url}"
                else:
                    print(
                        f"   Successfully extracted ~{len(extracted_text)} characters.")

    except aiohttp.ClientError as e:
        print(f"   Error fetching URL {url}: {e}")
        error = f"Network error fetching URL: {e}"
    except Exception as e:
        print(f"   Error parsing URL {url}: {e}")
        error = f"Error parsing HTML content: {e}"

    return {"extracted_text": extracted_text, "error": error}


async def summarize_to_mermaid(state: GraphState) -> dict:
    """
    Summarizes the extracted text into Mermaid.js flowchart Markdown
    using Google Gemini Flash.
    """
    print("--- Node: Summarizing to Mermaid ---")
    if state.get("error"):  # If an error occurred previously, skip this step
        print("   Skipping due to previous error.")
        return {}
    if not state.get("extracted_text"):
        print("   Skipping as there is no text to summarize.")
        return {"error": "Cannot summarize, no text was extracted."}

    text_to_summarize = state['extracted_text']
    summary_markdown = ""
    error = None

    try:
        # Use gemini-1.5-flash-latest as requested
        GEMINI_MODEL_ID = "gemini-2.0-flash"
        llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL_ID, temperature=0.3)

        # Define the prompt - explicitly ask for Mermaid flowchart syntax
        system_prompt = """You are an expert text summarizer. Your task is to summarize the provided text into a flowchart using Mermaid.js Markdown syntax.
The flowchart should represent the main steps, concepts, or flow described in the text.
Ensure the output is ONLY the Mermaid code block, starting with ```mermaid and ending with ```.
Use a simple flowchart (graph TD). Example node format: id["Label"]. Example edge format: id1 --> id2["Label"].
Keep the flowchart concise and focused on the core information."""

        human_prompt = f"Please summarize the following text into a Mermaid.js flowchart:\n\n---\n\n{text_to_summarize}\n\n---"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]

        # Use stream for potentially large outputs if needed, invoke for simpler cases
        # response = llm.stream(messages)
        # for chunk in response:
        #     summary_markdown += chunk.content

        response = await llm.ainvoke(messages)  # Use async invoke
        summary_markdown = response.content.strip()  # Get content and strip whitespace

        # Basic validation if it looks like a mermaid block
        if not (summary_markdown.startswith("```mermaid") and summary_markdown.endswith("```")):
            print(" Warning: LLM output doesn't look like a Mermaid block. Wrapping it.")
            summary_markdown = f"```mermaid\ngraph TD\n    A[Summary Start]\n    B[LLM Output:\n{summary_markdown}\n    ]\n    A --> B\n```"
            error = "LLM output was not in expected Mermaid format."
        else:
            print(" Successfully generated Mermaid summary.")

    except Exception as e:
        print(f"   Error calling Google GenAI: {e}")
        error = f"Error during summarization: {e}"

    return {"summary_markdown": summary_markdown, "error": error}

# --- Build the Graph ---

# Initialize the graph state
workflow = StateGraph(GraphState)

# Add the nodes
workflow.add_node("fetch_parse", fetch_and_parse)
workflow.add_node("summarize", summarize_to_mermaid)

# Define the edges (the flow of execution)
workflow.set_entry_point("fetch_parse")  # Start with fetching
workflow.add_edge("fetch_parse", "summarize")  # After fetching, summarize
workflow.add_edge("summarize", END)  # After summarizing, end the graph

# Compile the graph into a runnable application
app = workflow.compile()

# --- Run the Agent ---


async def run_agent(url: str):
    """Helper function to run the graph asynchronously."""
    inputs = {"url": url}
    print(f"\n🚀 Starting RAG Agent for URL: {url}")
    final_state = await app.ainvoke(inputs)
    print("\n🏁 Agent finished.")

    if final_state.get("error"):
        print(f"\n⚠️ Error occurred: {final_state['error']}")

    if final_state.get("summary_markdown"):
        print("\n📄 Generated Mermaid Markdown Summary:")
        print("-" * 40)
        print(final_state["summary_markdown"])
        print("-" * 40)
    else:
        print("\n❌ No summary was generated.")

    # You can inspect the full final state if needed
    # print("\nFull Final State:")
    # print(final_state)

# --- Example Usage ---
if __name__ == "__main__":
    # Replace with the URL you want to process
    target_url = "https://vnexpress.net/tong-bi-thu-to-lam-dien-dam-voi-tong-thong-my-trump-4870250.html"  # Example URL

    # Run the asynchronous function
    asyncio.run(run_agent(target_url))
