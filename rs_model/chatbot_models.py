import time
from dotenv import load_dotenv
import os

# Load the .env file and override any existing environment variables
load_dotenv(override=True)

import uuid
from typing import Optional
from pydantic import BaseModel, Field
from typing import Optional, Dict

# use Google AI
import google.generativeai as genai

# need Google translate to convert input into English
from google.cloud import translate_v2 as translate
import pprint

from rs_model.langgraph.conversation_models import UserConversationState


# default model names
GEMINI_TEXT_MODEL_ID = os.getenv("GEMINI_TEXT_MODEL_ID")
DEFAULT_TEMPERATURE_SCORE = 1.0

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TEMPERATURE_SCORE = 0.86



# Data models

class Message(BaseModel):
    """ Message as base class to get input from user with CDP as core database
        ### Example Usage
        msg = Message(question="What are the benefits of AI in marketing?")
        user_profile = {"Name": "John Doe", "Interests": "AI, Marketing"}
        print(msg.build_prompt(user_profile=user_profile, ext_context="Consider recent AI trends."))
    """
    
    answer_in_language: str = Field("English")  # Default is English
    answer_in_format: str = Field("html", description="The format of answer")
    context: str = Field("You are a creative chatbot.", description="The context of question")
    question: str = Field("", description="The question for Q&A")
    temperature_score: float = Field(DEFAULT_TEMPERATURE_SCORE, description="The temperature score of LLM")
    
    visitor_id: str = Field("", description="The visitor id")
    profile_id: str = Field("", description="The user id")
    persona_name: str = Field("", description="The persona name")
    session_id: str = Field("", description="The session id")
    
    def to_conversation_state(self, agent_role: str = "", journey_id: str = "", touchpoint_id: str = ""):
        """Converts the Message instance to a ConversationState object."""
        state = UserConversationState(
            profile_id=self.profile_id,
            user_message=self.question,
            agent_role=agent_role,
            journey_id=journey_id,
            touchpoint_id=touchpoint_id,
            context=self.context,
            created_at=int(time.time())
        )
        
        state.answer_in_format = self.answer_in_format
        state.persona_name = self.persona_name
        state.session_id = self.session_id
        return state

 
    
def is_gemini_model_ready():
    isReady = isinstance(GEMINI_API_KEY, str)
    # init Google AI 
    if isReady:
        genai.configure(api_key=GEMINI_API_KEY)
        return True
    else:
        return False
    
    
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



# TODO load from ArangoDB
persona_name_list = [
    {"code": "chatbot", "label": "Chatbot", "selected": True},
    {"code": "psychologist", "label": "Psychologist", "selected": False},
    {"code": "teacher", "label": "Teacher", "selected": False},
    {"code": "coach", "label": "Coach", "selected": False},
    {"code": "customer_support", "label": "Customer Support", "selected": False},
    {"code": "financial_advisor", "label": "Financial Advisor", "selected": False},
    {"code": "fitness_trainer", "label": "Fitness Trainer", "selected": False},
    {"code": "doctor", "label": "Doctor", "selected": False},
    {"code": "lawyer", "label": "Lawyer", "selected": False},
    {"code": "career_counselor", "label": "Career Counselor", "selected": False},
    {"code": "sales_assistant", "label": "Sales Assistant", "selected": False},
    {"code": "marketing_consultant", "label": "Marketing Consultant", "selected": False},
    {"code": "virtual_assistant", "label": "Virtual Assistant", "selected": False},
    {"code": "project_manager", "label": "Project Manager", "selected": False},
    {"code": "product_recommendation", "label": "Product Recommendation", "selected": False},
    {"code": "travel_agent", "label": "Travel Agent", "selected": False},
    {"code": "therapist", "label": "Therapist", "selected": False},
    {"code": "personal_stylist", "label": "Personal Stylist", "selected": False},
    {"code": "language_tutor", "label": "Language Tutor", "selected": False},
    {"code": "stock_market_analyst", "label": "Stock Market Analyst", "selected": False}
]


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

def generate_report(question: str) -> str:
    # TODO create report in iframe
    return '<iframe id="custom_report_iframe" src="https://superset.datatest.ch/superset/dashboard/10/?standalone=true" width="100%" style="" height="1280px" frameborder="0"></iframe>' 

