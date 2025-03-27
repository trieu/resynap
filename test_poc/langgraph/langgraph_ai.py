import os
import uuid
import google.generativeai as genai
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, SearchParams

from langgraph.graph import StateGraph
from sentence_transformers import SentenceTransformer
from qdrant_client.http.models import Distance, VectorParams
from dataclasses import dataclass, asdict

# Configure Gemini AI
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# embedding model for text transformation
MODEL_NAME = 'BAAI/bge-m3'
embedding_model = SentenceTransformer(MODEL_NAME)
VECTOR_DIM_SIZE = embedding_model.get_sentence_embedding_dimension()

# Gemini AI model
GEMINI_MODEL_ID = 'gemini-2.0-flash'
gemini_model = genai.GenerativeModel(GEMINI_MODEL_ID)

# Fetch the host and port from environment variables
QDRANT_HOST = os.getenv('QDRANT_HOST', 'localhost')  # default is 'localhost'
QDRANT_PORT = int(os.getenv('QDRANT_PORT', 6333))  # default is 6333

COLLECTION_AGENT_ROLES = "om_agent_roles"
COLLECTION_CONVERSATION = "om_conversations"

@dataclass
class ConversationState:
    """A conversation state encapsulates all the information you need to understand and track the context of an ongoing conversation. It’s essentially a snapshot that contains key elements like:

* User Identification: Who is talking (e.g., user_id).
* User's Message: What the user said (user_message).
* Agent Role: Which type of agent is interacting (e.g., support, info, sales).
* Journey Context: Where the user is in their overall interaction journey (journey_id).
* Touchpoint Information: The specific interaction point (touchpoint_id).
* Context:  is the background information that helps make the conversation relevant and personalized. It includes past messages, user preferences, session details (like time and device), and any extra data from other systems. It also tracks the user’s intent and sentiment to ensure clear and helpful responses.
* Response: the agent's reply or action.

This data class is used to store and pass around the conversation state in the AI workflow."""
    user_id: str = ""
    user_message: str = ""
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


class DatabaseManager:
    """Handles interactions with Qdrant."""

    def __init__(self):

        # Qdrant (Vector Search)
        self.qdrant_client = QdrantClient(QDRANT_HOST, port=QDRANT_PORT)
        
        # Collection names
        self.conversations_collection_name = COLLECTION_CONVERSATION
        self.agent_roles_collection_name = COLLECTION_AGENT_ROLES
        
        # Create collections if they don't exist
        self._check_and_create_collection(self.conversations_collection_name)
        self._check_and_create_collection(self.agent_roles_collection_name) 


    def _check_and_create_collection(self, cl_name, vector_size=VECTOR_DIM_SIZE):
        """
        Checks if a Qdrant collection exists and creates it if it doesn't.
        """
        if vector_size is None:
            vector_size = VECTOR_DIM_SIZE

        # Get existing collections
        existing_collections = [col.name for col in self.qdrant_client.get_collections().collections]

        if cl_name not in existing_collections:
            self.qdrant_client.create_collection(
                collection_name=cl_name,
                vectors_config=VectorParams(
                    size=vector_size, distance=Distance.COSINE
                ),
            )
            print(f"✅ Created Qdrant collection: {cl_name} with vector size: {vector_size}")
        else:
            print(f"⚠️ Collection `{cl_name}` already exists. Skipping creation.")

    def get_qdrant_client(self):
        return self.qdrant_client
    
    def store_training_data(self, agent_role, journey_id, touchpoint_id, context, response):
        """Stores training data for AI learning."""
        embedding = embedding_model.encode(
            context, convert_to_tensor=True).tolist()
        training_id = str(uuid.uuid4())

        self.qdrant_client.upsert(
            collection_name=self.conversations_collection_name,
            points=[PointStruct(id=training_id, vector=embedding, payload={
                "agent_role": agent_role,
                "journey_id": journey_id,
                "touchpoint_id": touchpoint_id,
                "context": context,
                "response": response
            })]
        )

    def search_conversations(self, user_message, limit=2):
        """Searches for relevant context based on user query."""

        query_vector = embedding_model.encode(
            user_message, convert_to_tensor=True).tolist()
        search_results = self.qdrant_client.search(
            collection_name=self.conversations_collection_name,
            query_vector=query_vector,
            limit=limit,
            with_payload=True,
            search_params=SearchParams(hnsw_ef=128, exact=True)
        )
        return search_results
    
   


class LangGraphAI:
    """Main AI Workflow using LangGraph."""

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.workflow = StateGraph(ConversationState)  # ✅ Initialize LangGraph
        self._setup_workflow()  # ✅ Set up the workflow graph

    def _setup_workflow(self):
        """Defines the AI workflow graph."""
        self.workflow.add_node("determine_agent_role",
                               self.determine_agent_role)
        self.workflow.add_node("retrieve_context", self.retrieve_context)
        self.workflow.add_node("generate_response", self.generate_response)

        # Define workflow transitions
        self.workflow.add_edge("determine_agent_role", "retrieve_context")
        self.workflow.add_edge("retrieve_context", "generate_response")

        #  Set entry point for the workflow
        self.workflow.set_entry_point("determine_agent_role")

        #  Compile the workflow properly
        self.workflow = self.workflow.compile()

    # 🔹 Hàm xác định vai trò của agent từ ngữ cảnh của người dùng

    def determine_agent_role(self, state_dict) :
        """Sử dụng Qdrant để tìm vai trò của agent phù hợp với nội dung tin nhắn."""
        
        state = ConversationState.from_dict(state_dict) 
        embedding = embedding_model.encode(
            state.user_message, convert_to_tensor=True).tolist()
        
        # Search for the most relevant agent role
        search_results = self.db_manager.get_qdrant_client().search(
            collection_name=COLLECTION_AGENT_ROLES,
            query_vector=embedding,
            limit=1,
            with_payload=True,
            search_params=SearchParams(hnsw_ef=128, exact=True),
        )
        if len(search_results) > 0:
            return search_results[0].to_dict()
        else:
            state.agent_role = "default_agent"
            return state.to_dict()

    def retrieve_context(self, state_dict) :
        """Retrieves past relevant context from Qdrant."""
        
        state = ConversationState.from_dict(state_dict) 
        embedding = embedding_model.encode(
            state.user_message, convert_to_tensor=True).tolist()
        # Search for relevant context
        search_results = self.db_manager.qdrant_client.search(
            collection_name=self.db_manager.conversations_collection_name,
            query_vector=embedding,
            limit=3,
            with_payload=True,
            search_params=SearchParams(hnsw_ef=128, exact=True)
        )
        state.context = "\n".join([result.payload["context"]
                                  for result in search_results])
        return state.to_dict()

    def generate_response(self, state_dict) :
        """Generates an AI response using Gemini."""
        
        state = ConversationState.from_dict(state_dict) 
        prompt = f"User: {state.user_message}\nContext: {state.context}\nResponse:"
        response = gemini_model.generate_content(prompt)
        state.response = response.text if response else "Xin lỗi, tôi không thể tạo câu trả lời."
        return state.to_dict()

def main():

    # Initialize system
    db_manager = DatabaseManager()
    ai_system = LangGraphAI(db_manager)

    # Create an initial state
    initial_state = ConversationState(user_id=str(uuid.uuid4()), user_message="Tôi không thể ngủ vào ban đêm")

    # Run LangGraph workflow
    final_state_dict = ai_system.workflow.invoke(initial_state.to_dict()) 

    # Convert back to ConversationState object
    final_state = ConversationState.from_dict(final_state_dict)

    # Output AI's response
    print(f"User: {final_state.user_message}")
    print(f"AI Response: {final_state.response}")

    print(f"AI Agent Role: {final_state.agent_role}")

if __name__ == "__main__":
   main()