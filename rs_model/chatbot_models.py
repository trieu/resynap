from rs_model.langgraph.conversation_models import UserConversationState
import google.generativeai as genai
from typing import Optional, Dict
from pydantic import BaseModel, Field
from typing import Optional
import uuid
import time
from dotenv import load_dotenv
import os

from rs_model.language_utils import VIETNAMESE

# Load the .env file and override any existing environment variables
load_dotenv(override=True)


# use Google AI


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
    context: str = Field("You are a creative chatbot.",
                         description="The context of question")
    question: str = Field("", description="The question for Q&A")
    temperature_score: float = Field(
        DEFAULT_TEMPERATURE_SCORE, description="The temperature score of LLM")

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
        {"name": "HR Support", "active": False,
            "private": True, "decode_key": "a1b2c3"},
        {"name": "Stress Management", "active": False,
            "private": True, "decode_key": "x9y8z7"},
        {"name": "Sales Report 2025", "active": True,
            "private": False, "decode_key": ""},
        {"name": "Customer Feedback Analysis 2025",
            "active": False, "private": False, "decode_key": ""},
        {"name": "AI Research Discussion", "active": False,
            "private": True, "decode_key": "d4e5f6"},
        {"name": "Marketing Trends 2024", "active": False,
            "private": False, "decode_key": ""},
        {"name": "Employee Well-being", "active": False,
            "private": True, "decode_key": "g7h8i9"},
        {"name": "Tech Innovations", "active": False,
            "private": False, "decode_key": ""},
        {"name": "Customer Support AI", "active": False,
            "private": True, "decode_key": "j1k2l3"},
        {"name": "Competitive Analysis", "active": False,
            "private": False, "decode_key": ""}
    ]
]


# TODO load from ArangoDB
persona_agent_list = [
    {"code": "chatbot", "name": "Trợ lý chuyện trò thân thiện", "description": "Một AI trò chuyện đa năng.", "gender": "neutral", "selected": True, "avatar_url": "https://cdn-icons-png.flaticon.com/128/2728/2728212.png", "domain_knowledge": "Phát triển bản thân"},

    {"code": "psychologist", "name": "Anh tư vấn tâm lý đáng tin", "description": "Hỗ trợ và tư vấn sức khỏe tinh thần.", "gender": "male", "selected": False, "avatar_url": "https://cdn-icons-png.flaticon.com/128/4576/4576683.png", "domain_knowledge": "Sức khỏe"},

    {"code": "teacher", "name": "Cô giáo tận tâm", "description": "Cung cấp hướng dẫn và kiến thức giáo dục.", "gender": "female", "selected": False, "avatar_url": "https://cdn-icons-png.flaticon.com/128/8065/8065183.png", "domain_knowledge": "Giáo dục"},

    {"code": "coach", "name": "Huấn luyện viên nhiệt huyết", "description": "Tạo động lực và hướng dẫn người dùng đạt mục tiêu.", "gender": "male", "selected": False, "avatar_url": "https://cdn-icons-png.flaticon.com/128/857/857682.png", "domain_knowledge": "Phát triển bản thân"},

    {"code": "customer_support", "name": "Chuyên viên hỗ trợ siêu nhanh", "description": "Hỗ trợ khách hàng với sản phẩm hoặc dịch vụ.", "gender": "neutral", "selected": False, "avatar_url": "https://cdn-icons-png.flaticon.com/128/1256/1256650.png", "domain_knowledge": "Công việc"},

    {"code": "financial_advisor", "name": "Cố vấn tài chính uy tín", "description": "Tư vấn về kế hoạch tài chính và đầu tư.", "gender": "male", "selected": False, "avatar_url": "https://cdn-icons-png.flaticon.com/128/2333/2333145.png", "domain_knowledge": "Công việc"},

    {"code": "fitness_trainer", "name": "PT thể hình nghiêm khắc mà vui tính", "description": "Cung cấp kế hoạch tập luyện và lời khuyên về thể hình.", "gender": "male", "selected": False, "avatar_url": "https://cdn-icons-png.flaticon.com/128/2910/2910796.png", "domain_knowledge": "Sức khỏe"},

    {"code": "doctor", "name": "Bác sĩ online đáng tin cậy", "description": "Cung cấp thông tin và tư vấn y tế tổng quát.", "gender": "neutral", "selected": False, "avatar_url": "https://cdn-icons-png.flaticon.com/128/3209/3209265.png", "domain_knowledge": "Sức khỏe"},

    {"code": "lawyer", "name": "Luật sư cố vấn chắc chắn", "description": "Cung cấp thông tin và hướng dẫn pháp lý.", "gender": "male", "selected": False, "avatar_url": "https://cdn-icons-png.flaticon.com/128/2750/2750250.png", "domain_knowledge": "Công việc"},

    {"code": "career_counselor", "name": "Chuyên viên hướng nghiệp sáng suốt", "description": "Hỗ trợ lập kế hoạch và phát triển sự nghiệp.", "gender": "female", "selected": False, "avatar_url": "https://cdn-icons-png.flaticon.com/128/1903/1903162.png", "domain_knowledge": "Công việc"},

    {"code": "software_engineer", "name": "Kỹ sư phần mềm dày dạn", "description": "Hỗ trợ lập trình, thiết kế hệ thống và giải quyết vấn đề kỹ thuật.", "gender": "male", "selected": False, "avatar_url": "https://cdn-icons-png.flaticon.com/128/1087/1087815.png", "domain_knowledge": "Công việc"},

    {"code": "business_consultant", "name": "Chuyên gia tư vấn kinh doanh", "description": "Cung cấp chiến lược phát triển doanh nghiệp và tối ưu quy trình.", "gender": "male", "selected": False, "avatar_url": "https://cdn-icons-png.flaticon.com/128/2345/2345354.png", "domain_knowledge": "Công việc"},

    {"code": "parenting_coach", "name": "Chuyên gia nuôi dạy con", "description": "Hỗ trợ cha mẹ trong giáo dục và nuôi dạy con cái.", "gender": "female", "selected": False, "avatar_url": "https://cdn-icons-png.flaticon.com/128/2933/2933249.png", "domain_knowledge": "Cuộc sống cá nhân"},

    {"code": "public_speaker", "name": "Diễn giả truyền cảm hứng", "description": "Hướng dẫn kỹ năng thuyết trình và giao tiếp tự tin.", "gender": "neutral", "selected": False, "avatar_url": "https://cdn-icons-png.flaticon.com/128/3989/3989540.png", "domain_knowledge": "Phát triển bản thân"},

    {"code": "travel_expert", "name": "Hướng dẫn viên du lịch", "description": "Tư vấn về điểm đến, hành trình và trải nghiệm du lịch.", "gender": "neutral", "selected": False, "avatar_url": "https://cdn-icons-png.flaticon.com/128/2018/2018673.png", "domain_knowledge": "Du lịch"},

    {"code": "language_tutor", "name": "Gia sư ngoại ngữ", "description": "Dạy các ngôn ngữ phổ biến như Anh, Nhật, Hàn, Pháp.", "gender": "female", "selected": False, "avatar_url": "https://cdn-icons-png.flaticon.com/128/8065/8065351.png", "domain_knowledge": "Giáo dục"},

    {"code": "nutritionist", "name": "Chuyên gia dinh dưỡng", "description": "Tư vấn chế độ ăn uống và lối sống lành mạnh.", "gender": "neutral", "selected": False, "avatar_url": "https://cdn-icons-png.flaticon.com/128/1995/1995575.png", "domain_knowledge": "Sức khỏe"},

    {"code": "mental_health_coach", "name": "Huấn luyện viên sức khỏe tinh thần", "description": "Giúp cải thiện tâm lý, giảm căng thẳng và phát triển tinh thần.", "gender": "neutral", "selected": False, "avatar_url": "https://cdn-icons-png.flaticon.com/128/1811/1811962.png", "domain_knowledge": "Sức khỏe"},

    {"code": "career_coach", "name": "Cố vấn sự nghiệp", "description": "Hỗ trợ định hướng nghề nghiệp và phát triển chuyên môn.", "gender": "male", "selected": False, "avatar_url": "https://cdn-icons-png.flaticon.com/128/2098/2098307.png", "domain_knowledge": "Công việc"},

    {"code": "relationship_counselor", "name": "Chuyên gia tư vấn tình cảm", "description": "Hỗ trợ xây dựng và duy trì mối quan hệ lành mạnh.", "gender": "female", "selected": False, "avatar_url": "https://cdn-icons-png.flaticon.com/128/3135/3135768.png", "domain_knowledge": "Cuộc sống cá nhân"},
]



def get_selected_agent():
    """
    Lọc danh sách persona_agent_list và trả về agent được chọn (selected=True).

    Returns:
      Dictionary của agent được chọn, hoặc None nếu không có agent nào được chọn.
    """
    for agent in persona_agent_list:
        if agent.get("selected"):
            return agent
    return None


def generate_report(question: str) -> str:
    # TODO create report in iframe
    return '<iframe id="custom_report_iframe" src="https://superset.datatest.ch/superset/dashboard/10/?standalone=true" width="100%" style="" height="1280px" frameborder="0"></iframe>'
