from dataclasses import dataclass, asdict, field
import time
from typing import List, Optional, Dict, Any
from rs_model.language_utils import get_language_name


@dataclass
class ConversationState:
    """
    A conversation state encapsulates all the information you need to understand and track the context of an ongoing conversation. 
    All fields:

    * Agent Role: Which type of agent is interacting (e.g., support, info, sales).
    * Journey Context: Where the user is in their overall interaction journey (journey_id).
    * Touchpoint Information: The specific interaction point (touchpoint_id).
    * Context:  is the background information that helps make the conversation relevant and personalized. It includes past messages, user preferences, session details (like time and device), and any extra data from other systems. It also tracks the user’s intent and sentiment to ensure clear and helpful responses.
    * Response: the agent's reply or action.
    * Keywords: A list of relevant keywords extracted from the conversation.

    This data class is used to store and pass around the conversation state in the AI workflow.
    """
    profile_id: str = ""
    user_message: str = ""

    agent_role: str = ""
    journey_id: str = ""
    touchpoint_id: str = ""
    context: str = ""
    keywords: List[str] = field(default_factory=list) 
    response: str = ""
    status: int = 1
    created_at: int = field(default_factory=lambda: int(time.time()))

    def to_dict(self):
        """Converts the state object to a dictionary for LangGraph."""
        return asdict(self)

    @staticmethod
    def from_dict(data):
        """Creates a ConversationState object from a dictionary, ensuring missing keys are handled."""
        if isinstance(data, ConversationState):  # ✅ Prevent passing a ConversationState instance
            return data
        return ConversationState(**data)  # ✅ Only pass dictionaries


@dataclass
class UserConversationState(ConversationState):
    """A conversation state encapsulates all the information from a specific user 
    All fields:

* User Identification: Who is talking (e.g., profile_id).
* User's Message: What the user said (user_message).
* Agent Role: Which type of agent is interacting (e.g., support, info, sales).
* Journey Context: Where the user is in their overall interaction journey (journey_id).
* Touchpoint Information: The specific interaction point (touchpoint_id).
* Context:  is the background information that helps make the conversation relevant and personalized. It includes past messages, user preferences, session details (like time and device), and any extra data from other systems. It also tracks the user’s intent and sentiment to ensure clear and helpful responses.
* Response: the agent's reply or action.

This data class is used to store and pass around the conversation state in the AI workflow when user send a message """

    private_mode: bool = False
    ext_context: str = ""
    answer_in_language: str = "Vietnamese"
    answer_in_format: str = "text"
    persona_name: str = "chatbot"
    session_id: str = ""
    previous_message: str = ""
    user_profile: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        """Converts the state object to a dictionary for LangGraph."""
        return asdict(self)

    @staticmethod
    def from_dict(data):
        """Creates a UserConversationState object from a dictionary, ensuring missing keys are handled."""
        if isinstance(data, UserConversationState):  # ✅ Prevent passing a UserConversationState instance
            return data
        return UserConversationState(**data)  # ✅ Only pass dictionaries

    def build_prompt(self) -> str:
        """
        Constructs a well-formatted prompt for sending to an LLM foundation model.
        Allows inclusion of user profile details and external context.
        """
        if len(self.persona_name) == 0:
            self.persona_name = " Alice, a smart AI buddy for user."
        
        # profile
        profile_info = ""
        if self.user_profile:
            profile_info = "\n".join(
                f"- {key}: {value}" for key, value in self.user_profile.items()
            )
        # additional context
        additional_context = f"\nAdditional Context: {self.ext_context}" if self.ext_context else ""

        if len(self.answer_in_language) == 0:
            self.answer_in_language = get_language_name(self.user_message)

        prompt_text = f"""
        Your persona is "{self.persona_name}". 
        
        Remember this user profile: \n{profile_info if profile_info else "an anonymous user"}
        
        
        Instruction to answer:
        - Previous message: "{self.previous_message}" of current conversation.
        - Just return answer in "{self.answer_in_language}" in simple language.
        - Format the answer as {self.answer_in_format}.
        - Build conversation's context from keywords: {self.context} . 
        - Additional context to help answer: {additional_context}.
        
        Your job is answering this message:
        {self.user_message}
        """.strip()

        return prompt_text

    def build_payload(self) -> dict:
        """ build payload for qdrant DB

        Returns:
            dict:  a dictionary for UserConversationState
        """
        return {
            "profile_id": self.profile_id,
            "user_message": self.user_message,
            "agent_role": self.agent_role,
            "journey_id": self.journey_id,
            "touchpoint_id": self.touchpoint_id,
            "context": self.context,
            "ext_context": self.ext_context,
            "session_id": self.session_id,
            "persona_name": self.persona_name,
            "answer_in_format": self.answer_in_format,
            "answer_in_language": self.answer_in_language,
            "response": self.response
        }
