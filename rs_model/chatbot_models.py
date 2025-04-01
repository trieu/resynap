import time
from dotenv import load_dotenv
import os

from rs_model.language_utils import VIETNAMESE

# Load the .env file and override any existing environment variables
load_dotenv(override=True)

import uuid
from typing import Optional
from pydantic import BaseModel, Field
from typing import Optional, Dict

# use Google AI
import google.generativeai as genai



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
    
    answer_in_language: str = Field(VIETNAMESE)  # Default is VIETNAMESE
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
persona_agent_list = [
    {"code": "chatbot", "label": "Trợ lý chuyện trò thân thiện", "description": "Một AI trò chuyện đa năng.", "gender": "neutral", "selected": True},
    {"code": "psychologist", "label": "Anh tư vấn tâm lý đáng tin", "description": "Hỗ trợ và tư vấn sức khỏe tinh thần.", "gender": "male", "selected": False},
    {"code": "teacher", "label": "Cô giáo tận tâm", "description": "Cung cấp hướng dẫn và kiến thức giáo dục.", "gender": "female", "selected": False},
    {"code": "coach", "label": "Huấn luyện viên nhiệt huyết", "description": "Tạo động lực và hướng dẫn người dùng đạt mục tiêu.", "gender": "male", "selected": False},
    {"code": "customer_support", "label": "Chuyên viên hỗ trợ siêu nhanh", "description": "Hỗ trợ khách hàng với sản phẩm hoặc dịch vụ.", "gender": "neutral", "selected": False},
    {"code": "financial_advisor", "label": "Cố vấn tài chính uy tín", "description": "Tư vấn về kế hoạch tài chính và đầu tư.", "gender": "male", "selected": False},
    {"code": "fitness_trainer", "label": "PT thể hình nghiêm khắc mà vui tính", "description": "Cung cấp kế hoạch tập luyện và lời khuyên về thể hình.", "gender": "male", "selected": False},
    {"code": "doctor", "label": "Bác sĩ online đáng tin cậy", "description": "Cung cấp thông tin và tư vấn y tế tổng quát.", "gender": "neutral", "selected": False},
    {"code": "lawyer", "label": "Luật sư cố vấn chắc chắn", "description": "Cung cấp thông tin và hướng dẫn pháp lý.", "gender": "male", "selected": False},
    {"code": "career_counselor", "label": "Chuyên viên hướng nghiệp sáng suốt", "description": "Hỗ trợ lập kế hoạch và phát triển sự nghiệp.", "gender": "female", "selected": False},
]



def generate_report(question: str) -> str:
    # TODO create report in iframe
    return '<iframe id="custom_report_iframe" src="https://superset.datatest.ch/superset/dashboard/10/?standalone=true" width="100%" style="" height="1280px" frameborder="0"></iframe>' 

