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




def get_selected_agent(persona_agent_list: list[dict]):
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
