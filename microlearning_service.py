from redis import Redis
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from typing import Optional
import time
import os
from dotenv import load_dotenv
# Load the .env file and override any existing environment variables
load_dotenv(override=True)


VERSION = "1.0.0"
SERVICE_NAME = "RESYNAP MICRO LEARNING VERSION:" + VERSION

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TEMPERATURE_SCORE = 0.86

MICROLEARNING_DEV_MODE = os.getenv("MICROLEARNING_DEV_MODE") == "true"
MICROLEARNING_HOSTNAME = os.getenv("MICROLEARNING_HOSTNAME")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")


# Redis Client to get User Session
REDIS_CLIENT = Redis(host=REDIS_HOST,  port=REDIS_PORT, decode_responses=True)
FOLDER_RESOURCES = os.path.dirname(os.path.abspath(__file__)) + "/resources/"
FOLDER_TEMPLATES = FOLDER_RESOURCES + "templates"

# init FAST API microlearning_api
microlearning_api = FastAPI()
microlearning_api.mount(
    "/resources", StaticFiles(directory=FOLDER_RESOURCES), name="resources")
templates = Jinja2Templates(directory=FOLDER_TEMPLATES)

# Data models


class Message(BaseModel):
    context: str = Field(default="", description="the context of question")
    question: str = Field(default="", description="the question for Q&A ")
    visitor_id: str = Field(default="", description="the visitor id ")


def is_visitor_ready(visitor_id: str):
    return REDIS_CLIENT.hget(visitor_id, 'microlearning_api') == "microlearning_api" or MICROLEARNING_DEV_MODE


@microlearning_api.get("/ping", response_class=PlainTextResponse)
async def ping():
    return "PONG"


@microlearning_api.get("/", response_class=HTMLResponse)
async def root(request: Request):
    ts = int(time.time())
    data = {"request": request, "MICROLEARNING_HOSTNAME": MICROLEARNING_HOSTNAME,
            "MICROLEARNING_DEV_MODE": MICROLEARNING_DEV_MODE, 'timestamp': ts}
    return templates.TemplateResponse("index.html", data)


# API get-visitor-info
@microlearning_api.get("/get-visitor-info", response_class=JSONResponse)
async def get_visitor_info(visitor_id: str):
    isGeminiReady = isinstance(GEMINI_API_KEY, str)
    if not isGeminiReady:
        return {"answer": "GEMINI_API_KEY is empty", "error_code": 501}
    
    if len(visitor_id) == 0:
        return {"answer": "visitor_id is empty ", "error": True, "error_code": 500}
    
    profile_id = REDIS_CLIENT.hget(visitor_id, 'profile_id')
    if profile_id is None or len(profile_id) == 0:
        if MICROLEARNING_DEV_MODE:
            return {"answer": "local_dev", "error_code": 0}
        else:
            return {"answer": "Not found any profile in CDP", "error": True, "error_code": 404}
        
    name = str(REDIS_CLIENT.hget(visitor_id, 'name'))
    return {"answer": name, "error_code": 0}


# the main function to ask a question and get an recommendation
def ask_question(context: str = '', question: str = 'Hi', temperature_score=TEMPERATURE_SCORE) -> str:

    response = ""
    prompt_data = {"question": question, "context": context}

    prompt_text = question
    answer_text = 'No answer!'
    try:
        # call to Google Gemini APi
        print("Call to Google Gemini API")
    except Exception as error:
        print("An exception occurred:", error)
        answer_text = "That's an interesting question."
        answer_text += "I have no answer by you can click here to check <a target='_blank' href='https://www.google.com/search?q=" + question + "'> "
        answer_text += "Google</a> ?"

    # done
    return str(answer_text)
