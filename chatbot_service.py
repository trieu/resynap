from rs_model.chatbot_models import (
    get_selected_agent, menu_items, persona_agent_list, Message, is_gemini_model_ready, generate_report
)

import asyncio
import os
import time
from dotenv import load_dotenv
from redis import Redis
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import markdown
from rs_model.langgraph.langgraph_ai import submit_message_to_agent

# Load environment variables
load_dotenv(override=True)

RESOURCES_FOLDER = os.path.dirname(os.path.abspath(__file__)) + "/resources"
TEMPLATES_FOLDER = RESOURCES_FOLDER + "/templates"

class ChatbotService:
    def __init__(self):
        self.version = "1.0.0"
        self.service_name = f"RESYNAP CHATBOT VERSION: {self.version}"
        self.dev_mode = os.getenv("CHATBOT_DEV_MODE") == "true"
        self.hostname = os.getenv("CHATBOT_HOSTNAME")
        self.name = os.getenv("CHATBOT_NAME")
        self.redis_host = os.getenv("REDIS_HOST")
        self.redis_port = os.getenv("REDIS_PORT")
        
        # Initialize Redis client
        self.redis_client = Redis(host=self.redis_host, port=self.redis_port, decode_responses=True)
        
        # Set up directories
        self.resources_folder = RESOURCES_FOLDER
        self.templates_folder = TEMPLATES_FOLDER
        
        # Initialize FastAPI app
        self.app = FastAPI()
        self.setup_routes()
        
        # Mount static files
        self.app.mount("/resources", StaticFiles(directory=self.resources_folder), name="resources")
        
        # Initialize Jinja2 templates
        self.templates = Jinja2Templates(directory=self.templates_folder)
        
        print(f"CHATBOT_NAME: {self.name} HOSTNAME: {self.hostname} DEV_MODE: {self.dev_mode}")
    
    def is_visitor_ready(self, visitor_id: str):
        if self.redis_client.hget(visitor_id, 'chatbot') == "chatbot":
            return True
        if self.dev_mode:
            return True
        return False

    async def ping(self):
        return "PONG"
    
    async def root(self, request: Request):
        ts = int(time.time())
        data = {
            "request": request,
            "timestamp": ts,
            "selected_agent" : get_selected_agent(),
            "persona_agent_list": persona_agent_list,
            "menu_items": menu_items,
            "CHATBOT_HOSTNAME": self.hostname,
            "CHATBOT_DEV_MODE": self.dev_mode,
            "CHATBOT_NAME": self.name,
        }
        return self.templates.TemplateResponse(self.get_default_chatbot_template(), data)

    def get_default_chatbot_template(self):
        #return "chatbot.html"
        return 'ai-buddy.html'
    
    async def get_visitor_info(self, visitor_id: str):
        if not is_gemini_model_ready():
            return {"answer": "GEMINI_API_KEY is empty", "error_code": 501}
        
        if not visitor_id:
            return {"answer": "visitor_id is empty", "error": True, "error_code": 500}
        
        profile_id = self.redis_client.hget(visitor_id, 'profile_id')
        if not profile_id:
            if self.dev_mode:
                return {"answer": "local_dev", "error_code": 0}
            
            return {"answer": "Not found any profile in CDP", "error": True, "error_code": 404}
        
        name = str(self.redis_client.hget(visitor_id, 'name'))
        return {"answer": name, "error_code": 0}
    
    async def ask(self, msg: Message):
        visitor_id = msg.visitor_id
        if not visitor_id:
            return {"answer": "visitor_id is empty", "error": True, "error_code": 500}
        
        # mapping from visitor_id to profile_id
        if self.dev_mode:
            profile_id = "0"
        else:
            profile_id = self.redis_client.hget(visitor_id, 'profile_id')
            if not profile_id:
                return {"answer": "Not found any profile in CDP", "error": True, "error_code": 404}
        
        chatbot_ready = self.is_visitor_ready(visitor_id)
        
        question = msg.question
        if len(question) > 1000:
            return {"answer": "Your input must be less than 1000 characters!", "error": True, "error_code": 510}
        
        print("visitor_id: ", visitor_id)
        print("profile_id: ", profile_id)
        
        if chatbot_ready:   
            # set profile_id 
            msg.profile_id = profile_id         
            if "report" in question.lower():
                answer = generate_report(question)
            else:
                answer = ask_question(msg)
                
            # return the answer
            print(f"answer: {answer}")
            return {"question": question, "answer": answer, "visitor_id": visitor_id, "error_code": 0}
        
        return {"answer": "Your profile is banned due to Violation of Terms", "error": True, "error_code": 666}
    
    def setup_routes(self):
        self.app.get("/ping", response_class=PlainTextResponse)(self.ping)
        self.app.get("/", response_class=HTMLResponse)(self.root)
        self.app.get("/get-visitor-info", response_class=JSONResponse)(self.get_visitor_info)
        self.app.post("/ask", response_class=JSONResponse)(self.ask)

# the main function to ask chatbot
def ask_question(msg: Message) -> str:
    answer_text = ''
    try:
        # call to AI agent
        final_state =  submit_message_to_agent(msg)
        answer_text = final_state.response   
             
        if answer_text:
            # format markdown to HTML 
            answer_text = markdown.markdown(answer_text)
    except Exception as error:
        print("An exception occurred:", error)
        answer_text = ''

    # done
    return str(answer_text)   

# Initialize chatbot service as Fast API instance
chatbot_service = ChatbotService()
chatbot = chatbot_service.app