from rs_model.chatbot_models import (
    menu_items, target_languages, Message, is_gemini_model_ready, ask_question, generate_report
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
            "target_languages": target_languages,
            "menu_items": menu_items,
            "CHATBOT_HOSTNAME": self.hostname,
            "CHATBOT_DEV_MODE": self.dev_mode,
            "CHATBOT_NAME": self.name,
        }
        return self.templates.TemplateResponse("chatbot.html", data)
    
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
        
        # FIXME load from arangoDB
        user_profile = {"Name": "John Doe", "Interests": "AI, Marketing"}
        ext_context = "Consider recent AI trends."
        
        prompt_text = msg.build_prompt(user_profile=user_profile, ext_context=ext_context)
        
        print("visitor_id: ", visitor_id)
        print("profile_id: ", profile_id)
        print(f"prompt_text: \n {prompt_text}")
        
        if chatbot_ready:
            
            answer_in_format = msg.answer_in_format
            temperature_score = msg.temperature_score
            
            if "report" in question.lower():
                answer = generate_report(question)
            else:
                answer = ask_question(prompt_text, answer_in_format, temperature_score)
            
            print(f"answer: {answer}")
            return {"question": question, "answer": answer, "visitor_id": visitor_id, "error_code": 0}
        
        return {"answer": "Your profile is banned due to Violation of Terms", "error": True, "error_code": 666}
    
    def setup_routes(self):
        self.app.get("/ping", response_class=PlainTextResponse)(self.ping)
        self.app.get("/", response_class=HTMLResponse)(self.root)
        self.app.get("/get-visitor-info", response_class=JSONResponse)(self.get_visitor_info)
        self.app.post("/ask", response_class=JSONResponse)(self.ask)

# Initialize chatbot service
chatbot_service = ChatbotService()
chatbot = chatbot_service.app
