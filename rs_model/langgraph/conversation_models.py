from dataclasses import dataclass, asdict


@dataclass
class ConversationState:
    """A conversation state encapsulates all the information you need to understand and track the context of an ongoing conversation. 
    All fields:

* Agent Role: Which type of agent is interacting (e.g., support, info, sales).
* Journey Context: Where the user is in their overall interaction journey (journey_id).
* Touchpoint Information: The specific interaction point (touchpoint_id).
* Context:  is the background information that helps make the conversation relevant and personalized. It includes past messages, user preferences, session details (like time and device), and any extra data from other systems. It also tracks the user’s intent and sentiment to ensure clear and helpful responses.
* Response: the agent's reply or action.

This data class is used to store and pass around the conversation state in the AI workflow."""
    agent_role: str = ""
    journey_id: str = ""
    touchpoint_id: str = ""
    context: str = ""
    response: str = ""
    status: int = 1

    def to_dict(self):
        """Converts the state object to a dictionary for LangGraph."""
        return asdict(self)

    @staticmethod
    def from_dict(data):
        """Creates a ConversationState object from a dictionary, ensuring missing keys are handled."""
        if isinstance(data, ConversationState):  # ✅ Prevent passing a ConversationState instance
            return data
        return ConversationState(**data)  # ✅ Only pass dictionaries




class UserConversationState(ConversationState):
    """A conversation state encapsulates all the information from a specific user 
    All fields:

* User Identification: Who is talking (e.g., user_id).
* User's Message: What the user said (user_message).
* Agent Role: Which type of agent is interacting (e.g., support, info, sales).
* Journey Context: Where the user is in their overall interaction journey (journey_id).
* Touchpoint Information: The specific interaction point (touchpoint_id).
* Context:  is the background information that helps make the conversation relevant and personalized. It includes past messages, user preferences, session details (like time and device), and any extra data from other systems. It also tracks the user’s intent and sentiment to ensure clear and helpful responses.
* Response: the agent's reply or action.

This data class is used to store and pass around the conversation state in the AI workflow when user send a message """
    user_id: str = ""
    user_message: str = ""
   
    def to_dict(self):
        """Converts the state object to a dictionary for LangGraph."""
        return asdict(self)

    @staticmethod
    def from_dict(data):
        """Creates a UserConversationState object from a dictionary, ensuring missing keys are handled."""
        if isinstance(data, UserConversationState):  # ✅ Prevent passing a UserConversationState instance
            return data
        return UserConversationState(**data)  # ✅ Only pass dictionaries