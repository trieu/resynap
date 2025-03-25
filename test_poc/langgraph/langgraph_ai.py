import os
import uuid
import google.generativeai as genai
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, SearchParams

from langgraph.graph import StateGraph
from sentence_transformers import SentenceTransformer
from qdrant_client.http.models import Distance, VectorParams

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

class DatabaseManager:
    """Handles interactions with Qdrant."""
    def __init__(self):

        # Qdrant (Vector Search)
        self.qdrant_client = QdrantClient(QDRANT_HOST, port=QDRANT_PORT)
        self.collection_name = "conversations"

        if self.collection_name not in self.qdrant_client.get_collections().collections:
            self.qdrant_client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=VECTOR_DIM_SIZE, distance=Distance.COSINE),
            )

    def store_training_data(self, agent_role, journey_id, touchpoint_id, context, response):
        """Stores training data for AI learning."""
        embedding = embedding_model.encode(context, convert_to_tensor=True).tolist()
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

class State:
    """Stores conversation state."""
    def __init__(self, user_id, user_message, journey_id="", touchpoint_id=""):
        self.user_id = user_id
        self.user_message = user_message
        self.agent_role = ""
        self.journey_id = journey_id
        self.touchpoint_id = touchpoint_id
        self.context = ""
        self.response = ""

class LangGraphAI:
    """Main AI Workflow using LangGraph."""
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.workflow = StateGraph(State)  # ✅ Initialize LangGraph
        self._setup_workflow()  # ✅ Set up the workflow graph

    def _setup_workflow(self):
        """Defines the AI workflow graph."""
        self.workflow.add_node("determine_agent_role", self.determine_agent_role)
        self.workflow.add_node("retrieve_context", self.retrieve_context)
        self.workflow.add_node("generate_response", self.generate_response)

        # Define workflow transitions
        self.workflow.add_edge("determine_agent_role", "retrieve_context")
        self.workflow.add_edge("retrieve_context", "generate_response")

        # ✅ Corrected: Set entry point for the workflow
        self.workflow.set_entry_point("determine_agent_role")

        # ✅ Corrected: Compile the workflow properly
        self.workflow = self.workflow.compile()

    def determine_agent_role(self, state: State) -> State:
        """Assigns an agent role based on user_message."""
        embedding = embedding_model.encode(state.user_message, convert_to_tensor=True).tolist()
        state.agent_role = "psychologist"  # Hardcoded for now, replace with actual role detection
        return state

    def retrieve_context(self, state: State) -> State:
        """Retrieves past relevant context from Qdrant."""
        embedding = embedding_model.encode(state.user_message, convert_to_tensor=True).tolist()
        search_results = self.db_manager.qdrant_client.search(
            collection_name=self.db_manager.collection_name,
            query_vector=embedding,
            limit=3,
            with_payload=True,
            search_params=SearchParams(hnsw_ef=128, exact=True)
        )
        state.context = "\n".join([result.payload["context"] for result in search_results])
        return state

    def generate_response(self, state: State) -> State:
        """Generates an AI response using Gemini."""
        prompt = f"User: {state.user_message}\nContext: {state.context}\nResponse:"
        response = gemini_model.generate_content(prompt)
        state.response = response.text if response else "Xin lỗi, tôi không thể tạo câu trả lời."
        return state

# Initialize system
db_manager = DatabaseManager()
ai_system = LangGraphAI(db_manager)
