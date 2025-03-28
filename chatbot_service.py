from dotenv import load_dotenv
import os

# Load the .env file and override any existing environment variables
load_dotenv(override=True)

import uuid
import time
from typing import Optional
from pydantic import BaseModel, Field

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from redis import Redis

# use Google AI
import markdown
import google.generativeai as genai

# need Google translate to convert input into English
from google.cloud import translate_v2 as translate
import pprint



VERSION = "1.0.0"
SERVICE_NAME = "RESYNAP CHATBOT VERSION:" + VERSION

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TEMPERATURE_SCORE = 0.86

# init Google AI 
genai.configure(api_key=GEMINI_API_KEY)

# default model names
GEMINI_TEXT_MODEL_ID = os.getenv("GEMINI_TEXT_MODEL_ID")
DEFAULT_TEMPERATURE_SCORE = 1.0

CHATBOT_DEV_MODE = os.getenv("CHATBOT_DEV_MODE") == "true"
CHATBOT_HOSTNAME = os.getenv("CHATBOT_HOSTNAME")
CHATBOT_NAME = os.getenv("CHATBOT_NAME")

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")

# print out the configuration
print(f"CHATBOT_NAME: {CHATBOT_NAME} CHATBOT_HOSTNAME {CHATBOT_HOSTNAME} CHATBOT_DEV_MODE {CHATBOT_DEV_MODE}")

# Redis Client to get User Session
REDIS_CLIENT = Redis(host=REDIS_HOST,  port=REDIS_PORT, decode_responses=True)
FOLDER_RESOURCES = os.path.dirname(os.path.abspath(__file__)) + "/resources/"
FOLDER_TEMPLATES = FOLDER_RESOURCES + "templates"

# init FAST API chatbot
chatbot = FastAPI()
chatbot.mount("/resources", StaticFiles(directory=FOLDER_RESOURCES), name="resources")
templates = Jinja2Templates(directory=FOLDER_TEMPLATES)

# Data models

# Sample menu items, TODO load from ArangoDB


menu_items = [
    {
        "id": str(uuid.uuid4()),  # Generate a unique UUID string
        **item
    }
    for item in [
        {"name": "HR Support", "active": False, "private": True, "decode_key": "a1b2c3"},
        {"name": "Stress Management", "active": False, "private": True, "decode_key": "x9y8z7"},
        {"name": "Sales Report 2025", "active": True, "private": False, "decode_key": ""},
        {"name": "Customer Feedback Analysis 2025", "active": False, "private": False, "decode_key": ""},
        {"name": "AI Research Discussion", "active": False, "private": True, "decode_key": "d4e5f6"},
        {"name": "Marketing Trends 2024", "active": False, "private": False, "decode_key": ""},
        {"name": "Employee Well-being", "active": False, "private": True, "decode_key": "g7h8i9"},
        {"name": "Tech Innovations", "active": False, "private": False, "decode_key": ""},
        {"name": "Customer Support AI", "active": False, "private": True, "decode_key": "j1k2l3"},
        {"name": "Competitive Analysis", "active": False, "private": False, "decode_key": ""}
    ]
]


# Language options, BCP-47 language code https://en.wikipedia.org/wiki/IETF_language_tag 
# TODO load from ArangoDB
target_languages = [
    {"code": "", "label": "Automatically detect the language according to question", "selected": True},
    {"code": "en", "label": "Answer the question in English", "selected": False},
    {"code": "vi", "label": "Trả lời câu hỏi bằng tiếng Việt", "selected": False},
    {"code": "de", "label": "Beantworten Sie Fragen auf Deutsch", "selected": False},
    {"code": "fr", "label": "Répondez à la question en français", "selected": False},
    {"code": "es", "label": "Responde la pregunta en español", "selected": False},
    {"code": "ja", "label": "質問には日本語で答える", "selected": False},
    {"code": "zh", "label": "用中文回答问题", "selected": False},
    {"code": "ko", "label": "질문에 한국어로 답변하기", "selected": False}
]

class Message(BaseModel):
    answer_in_language: Optional[str] = Field("en") # default is English
    answer_in_format: str = Field("html", description="the format of answer")
    context: str = Field("You are a creative chatbot.", description="the context of question")
    question: str = Field("", description="the question for Q&A ")
    temperature_score: float = Field(DEFAULT_TEMPERATURE_SCORE, description="the temperature score of LLM ")
    prompt: str
    visitor_id: str = Field("", description="the visitor id ")

def is_visitor_ready(visitor_id:str):
    return REDIS_CLIENT.hget(visitor_id, 'chatbot') == "chatbot" or CHATBOT_DEV_MODE

@chatbot.get("/ping", response_class=PlainTextResponse)
async def ping():
    return "PONG"

@chatbot.get("/", response_class=HTMLResponse)
async def root(request: Request):
    ts = int(time.time())
    data = {
            "request": request, 'timestamp': ts, "target_languages": target_languages, "menu_items": menu_items, 
            "CHATBOT_HOSTNAME": CHATBOT_HOSTNAME, 
            "CHATBOT_DEV_MODE": CHATBOT_DEV_MODE, 
            'CHATBOT_NAME': CHATBOT_NAME            
            }
    return templates.TemplateResponse("chatbot.html", data)


@chatbot.get("/get-visitor-info", response_class=JSONResponse)
async def get_visitor_info(visitor_id: str):
    isReady = isinstance(GEMINI_API_KEY, str)
    if not isReady:        
        return {"answer": "GEMINI_API_KEY is empty", "error_code": 501}
    if len(visitor_id) == 0: 
        return {"answer": "visitor_id is empty ", "error": True, "error_code": 500}
    profile_id = REDIS_CLIENT.hget(visitor_id, 'profile_id')
    if profile_id is None or len(profile_id) == 0: 
        if CHATBOT_DEV_MODE : 
            return {"answer": "local_dev", "error_code": 0}
        else:
            return {"answer": "Not found any profile in CDP", "error": True, "error_code": 404}
    name = str(REDIS_CLIENT.hget(visitor_id, 'name'))
    return {"answer": name, "error_code": 0}


# the main API of chatbot
@chatbot.post("/ask", response_class=JSONResponse)
async def ask(msg: Message):
    visitor_id = msg.visitor_id
    if len(visitor_id) == 0: 
        return {"answer": "visitor_id is empty ", "error": True, "error_code": 500}
    
    if CHATBOT_DEV_MODE:
        profile_id = "0"
    else:
        profile_id = REDIS_CLIENT.hget(visitor_id, 'profile_id')
        if profile_id is None or len(profile_id) == 0: 
            return {"answer": "Not found any profile in CDP", "error": True, "error_code": 404}
    
    chatbot_ready = is_visitor_ready(visitor_id)
    question = msg.question
    prompt = msg.prompt
    lang_of_question = msg.answer_in_language
    context = msg.context
       
    if len(question) > 1000 or len(prompt) > 1000 :
        return {"answer": "Question must be less than 1000 characters!", "error": True, "error_code": 510}

    print("context: "+context)
    print("question: "+question)
    print("prompt: "+prompt)
    print("visitor_id: " + visitor_id)
    print("profile_id: "+profile_id)

    if chatbot_ready:        
        if lang_of_question == "" :
            lang_of_question = detect_language(question)        
             
        format = msg.answer_in_format
        temperature_score = msg.temperature_score
        question_in_english = prompt

        if lang_of_question != "en":
            # our model can only understand English        
            question_in_english = translate_text(prompt, 'en')
            
        # translate if need
        if "report" in question_in_english.lower():
            # TODO create report in iframe
            answer = '<iframe id="custom_report_iframe" src="https://superset.datatest.ch/superset/dashboard/10/?standalone=true" width="100%" style="" height="1280px" frameborder="0"></iframe>' 
        else:
            answer = ask_question(context, format, lang_of_question, question_in_english, temperature_score)
        print("answer " + answer)
        data = {"question": question,
                "answer": answer, "visitor_id": visitor_id, "error_code": 0}
    else:
        data = {"answer": "Your profile is banned due to Violation of Terms", "error": True, "error_code": 666}
    return data



# detect language
def detect_language(text: str) -> str:
    if text == "" or text is None:
        return "en"
    if isinstance(text, bytes):
        text = text.decode("utf-8")
    result = translate.Client().detect_language(text)
    print(result)
    if result['confidence'] > 0.9 :
        return result['language']
    else : 
        return "en"
    
# Translates text into the target language.
def translate_text(text: str, target: str) -> dict:
    if text == "" or text is None:
        return ""
    if isinstance(text, bytes):
        text = text.decode("utf-8")
    result = translate.Client().translate(text, target_language=target)
    return result['translatedText']

def format_string_for_md_slides(rs):
    rs = rs.replace('<br/>','\n')
    rs = rs.replace('##','## ')
    return rs

# the main function to ask chatbot
def ask_question(context: str = '', answer_in_format: str = '', target_language: str = '', question: str = 'Hi', temperature_score = TEMPERATURE_SCORE ) -> str:
    
    response = ""
    prompt_data = {"question":question,"context":context}
   
    prompt_text = question
    answer_text = 'No answer!'
    try:
        # call to Google Gemini APi
        gemini_text_model = genai.GenerativeModel(model_name=GEMINI_TEXT_MODEL_ID)
        model_config = genai.GenerationConfig(temperature=temperature_score)
        response = gemini_text_model.generate_content(prompt_text, generation_config=model_config)
        answer_text = response.text    
    except Exception as error:
        print("An exception occurred:", error)
        answer_text = "That's an interesting question."
        answer_text += "I have no answer by you can click here to check <a target='_blank' href='https://www.google.com/search?q=" + question + "'> "
        answer_text +=   "Google</a> ?"

    # translate into target_language 
    if isinstance(target_language, str) and isinstance(answer_text, str):
        if len(answer_text) > 1:
            rs = ''
            if answer_in_format == 'html':
                # convert the answer in markdown into html 
                # See https://www.devdungeon.com/content/convert-markdown-html-python
                rs_html = markdown.markdown(answer_text, extensions=['fenced_code'])
                # translate into target language
                rs = translate_text(rs_html, target_language)
            else :
                answer_text = answer_text.replace('\n','<br/>')
                answer_text = answer_text.replace("```", "")                
                rs = translate_text(answer_text, target_language)
                rs = format_string_for_md_slides(rs)
            return rs
        else:
            return answer_text    
    elif answer_text is None:
        return translate_text("Sorry, I can not answer your question !", target_language) 
    # done
    return str(answer_text)