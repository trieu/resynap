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
MODEL_NAME = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
embedding_model = SentenceTransformer(MODEL_NAME)
VECTOR_DIM_SIZE = embedding_model.get_sentence_embedding_dimension()

# Gemini AI model
GEMINI_MODEL_ID = 'gemini-2.0-flash'
gemini_model = genai.GenerativeModel(GEMINI_MODEL_ID)

# Fetch the host and port from environment variables
QDRANT_HOST = os.getenv('QDRANT_HOST', 'localhost')  # default is 'localhost'
QDRANT_PORT = int(os.getenv('QDRANT_PORT', 6333))  # default is 6333

COLLECTION_AGENT_ROLES = "agent_roles"

@dataclass
class State:
    """Stores conversation state."""
    user_id: str = ""
    user_message: str = ""
    agent_role: str = ""
    journey_id: str = ""
    touchpoint_id: str = ""
    context: str = ""
    response: str = ""

    def to_dict(self):
        """Converts the state object to a dictionary for LangGraph."""
        return asdict(self)

    @staticmethod
    def from_dict(data):
        """Creates a State object from a dictionary, ensuring missing keys are handled."""
        if isinstance(data, State):  # ✅ Prevent passing a State instance
            return data
        return State(**data)  # ✅ Only pass dictionaries


class DatabaseManager:
    """Handles interactions with Qdrant."""

    def __init__(self):

        # Qdrant (Vector Search)
        self.qdrant_client = QdrantClient(QDRANT_HOST, port=QDRANT_PORT)
        self.collection_name = "conversations"

        # Get existing collections
        existing_collections = [col.name for col in self.qdrant_client.get_collections().collections]

        if self.collection_name not in existing_collections:
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=VECTOR_DIM_SIZE, distance=Distance.COSINE
                ),
            )
            print(f"✅ Created Qdrant collection: {self.collection_name}")
        else:
            print(f"⚠️ Collection `{self.collection_name}` already exists. Skipping creation.")

    def get_qdrant_client(self):
        return self.qdrant_client
    
    def store_training_data(self, agent_role, journey_id, touchpoint_id, context, response):
        """Stores training data for AI learning."""
        embedding = embedding_model.encode(
            context, convert_to_tensor=True).tolist()
        training_id = str(uuid.uuid4())

        self.qdrant_client.upsert(
            collection_name=self.collection_name,
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
            collection_name=self.collection_name,
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
        self.workflow = StateGraph(State)  # ✅ Initialize LangGraph
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
        
        state = State.from_dict(state_dict) 
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
        if search_results:
            return search_results[0].to_dict()
        else:
            state.agent_role = "default_agent"
            return state.to_dict()

    def retrieve_context(self, state_dict) :
        """Retrieves past relevant context from Qdrant."""
        
        state = State.from_dict(state_dict) 
        embedding = embedding_model.encode(
            state.user_message, convert_to_tensor=True).tolist()
        search_results = self.db_manager.qdrant_client.search(
            collection_name=self.db_manager.collection_name,
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
        
        state = State.from_dict(state_dict) 
        prompt = f"User: {state.user_message}\nContext: {state.context}\nResponse:"
        response = gemini_model.generate_content(prompt)
        state.response = response.text if response else "Xin lỗi, tôi không thể tạo câu trả lời."
        return state.to_dict()


# Initialize system
db_manager = DatabaseManager()
ai_system = LangGraphAI(db_manager)

# Create an initial state
initial_state = State(user_id=str(uuid.uuid4()), user_message="Tôi luôn cảm thấy lo lắng.")

# Run LangGraph workflow
final_state_dict = ai_system.workflow.invoke(initial_state.to_dict()) 

# Convert back to State object
final_state = State.from_dict(final_state_dict)

# Output AI's response
print(f"User: {final_state.user_message}")
print(f"AI Response: {final_state.response}")

print(f"AI Agent Role: {final_state.agent_role}")
