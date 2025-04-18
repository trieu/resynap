from rs_model.langgraph.conversation_models import UserConversationState

from pydantic import BaseModel, Field
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
    temperature_score: float = Field(DEFAULT_TEMPERATURE_SCORE, description="The temperature score of LLM")

    visitor_id: str = Field("", description="The visitor id")
    profile_id: str = Field("", description="The user profile id")
    persona_name: str = Field("", description="The persona name")
    session_id: str = Field("", description="The session id")
    private_mode: bool = Field(False, description="The private mode")
    previous_message: str = Field("", description="previous message")

    def to_conversation_state(self, agent_role: str = "", journey_id: str = "", touchpoint_id: str = ""):
        """Converts the Message instance to a ConversationState object."""
        
        if self.private_mode:
            self.profile_id = ''
        
        state = UserConversationState(
            private_mode=self.private_mode,
            profile_id=self.profile_id,
            user_message=self.question,
            agent_role=agent_role,
            journey_id=journey_id,
            touchpoint_id=touchpoint_id,
            context=self.context,
            previous_message=self.previous_message,
            created_at=int(time.time())
        )

        state.answer_in_format = self.answer_in_format
        state.persona_name = self.persona_name
        state.session_id = self.session_id
        return state





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

def generate_report(question: str):
    """Generates an HTML report with a link and an embedded iframe, styled with Bootstrap 5."""

    # TODO
    superset_url = 'https://superset.datatest.ch/superset/dashboard/10/?standalone=true'

    html_report = f"""
    <div class="container">
      <a href="{superset_url}" target="_blank" class="btn btn-primary mb-3">Report URL</a>
      <div class="ratio ratio-16x9">
        <iframe src="{superset_url}" title="Superset Dashboard" frameborder="0" allowfullscreen></iframe>
      </div>
    </div>
    """

    return html_report, ['analytics']