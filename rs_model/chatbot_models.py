from dotenv import load_dotenv
import os

# Load the .env file and override any existing environment variables
load_dotenv(override=True)

import uuid
from typing import Optional
from pydantic import BaseModel, Field
from typing import Optional, Dict

# use Google AI
import markdown
import google.generativeai as genai

# need Google translate to convert input into English
from google.cloud import translate_v2 as translate
import pprint
from rs_model.language_utils import get_language_name


# default model names
GEMINI_TEXT_MODEL_ID = os.getenv("GEMINI_TEXT_MODEL_ID")
DEFAULT_TEMPERATURE_SCORE = 1.0

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TEMPERATURE_SCORE = 0.86

def is_gemini_model_ready():
    isReady = isinstance(GEMINI_API_KEY, str)
    # init Google AI 
    if isReady:
        genai.configure(api_key=GEMINI_API_KEY)
        return True
    else:
        return False




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

    def build_prompt(self, user_profile: Optional[Dict[str, str]] = None, ext_context: Optional[str] = None) -> str:
        """
        Constructs a well-formatted prompt for sending to an LLM foundation model.
        Allows inclusion of user profile details and external context.
        """
        profile_info = ""
        if user_profile:
            profile_info = "\n".join([f"- {key}: {value}" for key, value in user_profile.items()])
        
        additional_context = f"\nAdditional Context: {ext_context}" if ext_context else ""
        
        if len(self.answer_in_language) == 0 :
            self.answer_in_language = get_language_name(self.question) 
        
        prompt_text = f"""
        Context: {self.context}
        {additional_context}
        
        User Profile: \n{profile_info if profile_info else "an anonymous user"}
        
        Instruction:
        - Just return answer in {self.answer_in_language} in simple language
        - Format the answer as {self.answer_in_format}
        
        Answer the question:
        {self.question}
        """.strip()
        
        return prompt_text
    

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

# the main function to ask chatbot
def ask_question(prompt_text:str, answer_in_format: str, temperature_score = TEMPERATURE_SCORE ) -> str:
    
    answer_text = ''
    try:
        # call to Google Gemini APi
        gemini_text_model = genai.GenerativeModel(model_name=GEMINI_TEXT_MODEL_ID)
        model_config = genai.GenerationConfig(temperature=temperature_score)
        response = gemini_text_model.generate_content(prompt_text, generation_config=model_config)
        answer_text = response.text    
    except Exception as error:
        print("An exception occurred:", error)
        answer_text = ''

    # done
    return str(answer_text)