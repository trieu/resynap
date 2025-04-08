from dotenv import load_dotenv
# Load the .env file and override any existing environment variables
load_dotenv(override=True)
import os

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, FileResponse

from rs_agent.agent_url_to_flowchart import GraphState

AGENT_API_HOSTNAME = os.getenv("AGENT_API_HOSTNAME","0.0.0.0")
AGENT_API_POST =  int(os.getenv('AGENT_API_POST', 8888))  # default is 8888

app_causal_graph = FastAPI()

# --- main API ---
@app_causal_graph.post("/generate_mermaid/")
async def generate_mermaid(url: str = Form(...), no_cache: bool = Form(False) ): 
    state = GraphState(url=url)
    return await state.process_url(no_cache=no_cache)
    

# --- Serve the Static HTML File ---
@app_causal_graph.get("/", response_class=HTMLResponse)
async def home():
    # Serve the index.html file from disk
    return FileResponse("./resources/templates/causal-graph.html")

# --- Run the FastAPI app_causal_graph ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app_causal_graph, host=AGENT_API_HOSTNAME, port=AGENT_API_POST)