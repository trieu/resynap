import os
import uuid
import google.generativeai as genai
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, SearchParams

from langgraph.graph import StateGraph
from sentence_transformers import SentenceTransformer
from qdrant_client.http.models import Distance, VectorParams
from rs_model.langgraph.conversation_models import ConversationState, UserConversationState

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

# collection names
COLLECTION_AGENT_ROLES = "om_agent_roles"
COLLECTION_AGENT_CONVERSATION = "om_agent_conversations"
COLLECTION_USER_CONVERSATION = "om_user_conversations"


def to_embedding_vector(s: str):
    """_summary_

    Args:
        s (str): string to vectorize

    Returns:
        a vector of s
    """
    return embedding_model.encode(s, convert_to_tensor=True).tolist()

class DatabaseManager:
    """Handles interactions with Qdrant."""

    def __init__(self):

        # Qdrant (Vector Search)
        self.qdrant_client = QdrantClient(QDRANT_HOST, port=QDRANT_PORT)
        
        # Create collections if they don't exist
        self.check_and_create_collection(COLLECTION_AGENT_CONVERSATION)
        self.check_and_create_collection(COLLECTION_USER_CONVERSATION) 
        self.check_and_create_collection(COLLECTION_AGENT_ROLES) 


    def check_and_create_collection(self, cl_name, vector_size=VECTOR_DIM_SIZE):
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
    
    def save_conversation_state(self, state: ConversationState):
        """Stores training data for AI learning."""
        embedding = to_embedding_vector(state.context)
        training_id = str(uuid.uuid4())

        self.qdrant_client.upsert(
            collection_name=COLLECTION_AGENT_CONVERSATION,
            points=[PointStruct(id=training_id, vector=embedding, payload={
                "agent_role": state.agent_role,
                "journey_id": state.journey_id,
                "touchpoint_id": state.touchpoint_id,
                "context": state.context,
                "response": state.response
            })]
        )
        
    def save_user_conversation_state(self, state: UserConversationState):
        """Stores training data for AI learning."""
        embedding = to_embedding_vector(state.context)
        training_id = str(uuid.uuid4())

        self.qdrant_client.upsert(
            collection_name=COLLECTION_USER_CONVERSATION,
            points=[PointStruct(id=training_id, vector=embedding, payload={
                "user_id":state.user_id,
                "user_message":state.user_message,
                "agent_role": state.agent_role,
                "journey_id": state.journey_id,
                "touchpoint_id": state.touchpoint_id,
                "context": state.context,
                "response": state.response
            })]
        )

    def load_conversation_state(self, context: str, limit=2):
        """Searches for relevant context based on user query."""

        if len(context) > 0:
            query_vector = to_embedding_vector(context)
            search_results = self.qdrant_client.search(
                collection_name=COLLECTION_AGENT_CONVERSATION,
                query_vector=query_vector,
                limit=limit,
                with_payload=True,
                search_params=SearchParams(hnsw_ef=128, exact=True)
            )
            return search_results
        return []
    
    def load_user_conversation_state(self, context: str, limit=2):
        """Searches for relevant context based on user query."""

        if len(context) > 0:
            query_vector = to_embedding_vector(context)
            search_results = self.qdrant_client.search(
                collection_name=COLLECTION_AGENT_CONVERSATION,
                query_vector=query_vector,
                limit=limit,
                with_payload=True,
                search_params=SearchParams(hnsw_ef=128, exact=True)
            )
            return search_results
        return []
   

class LangGraphAI:
    """Main AI Workflow using LangGraph."""

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.workflow = StateGraph(ConversationState)  # ✅ Initialize LangGraph
        self._setup_workflow()  # ✅ Set up the workflow graph

    def _setup_workflow(self):
        """Defines the AI workflow graph."""
        self.workflow.add_node("determine_agent_role", self.determine_agent_role)
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
        embedding = to_embedding_vector(state.user_message)
        
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
        embedding = to_embedding_vector(state.user_message)
        # Search for relevant context
        search_results = self.db_manager.qdrant_client.search(
            collection_name=self.db_manager.COLLECTION_AGENT_CONVERSATION,
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

# Agent System 
agent_system_loaded = False
agent_system = None  # Declare as global to ensure accessibility

def init_ai_system():
    global agent_system, agent_system_loaded  # Use global to persist changes
    if not agent_system_loaded:
        # Initialize system
        db_manager = DatabaseManager()
        agent_system = LangGraphAI(db_manager)
        agent_system_loaded = True  # Update flag
    return agent_system
        

def submit_message_to_agent(user_id: str, msg:str):

    # Create an initial state
    initial_state = ConversationState(user_id=user_id, user_message=msg)

    # Run LangGraph workflow
    agent_system = init_ai_system()
    final_state_dict = agent_system.workflow.invoke(initial_state.to_dict()) 

    # Convert back to ConversationState object
    final_state = ConversationState.from_dict(final_state_dict)

    return final_state
   

if __name__ == "__main__":
    
    user_id = str(uuid.uuid4())
    msg = "Tôi không thể ngủ vào ban đêm"
    final_state =  submit_message_to_agent(user_id, msg)
   
    # Output AI's response
    print(f"User: {final_state.user_message}")
    print(f"AI Response: {final_state.response}")

    print(f"AI Agent Role: {final_state.agent_role}")