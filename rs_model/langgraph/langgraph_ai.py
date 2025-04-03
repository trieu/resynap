import os
import uuid
import google.generativeai as genai
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, SearchParams, Filter, FieldCondition, MatchValue

from qdrant_client.http.models import Distance

from langgraph.graph import StateGraph
from sentence_transformers import SentenceTransformer

from rs_domain.user_management import get_user_profile, get_user_profile_for_ai_agent
from rs_model.langgraph.conversation_models import ConversationState, UserConversationState
from rs_model.chatbot_models import Message
from rs_model.language_utils import remove_similar_keywords
from rs_model.system_utils import read_json_from_file


# Configure Gemini AI
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Embedding model for text transformation
MODEL_NAME = 'BAAI/bge-m3'
embedding_model = SentenceTransformer(MODEL_NAME)
VECTOR_DIM_SIZE = embedding_model.get_sentence_embedding_dimension()

# Gemini AI model
GEMINI_MODEL_ID = 'gemini-2.0-flash'
gemini_model = genai.GenerativeModel(GEMINI_MODEL_ID)

# Fetch the host and port from environment variables
QDRANT_HOST = os.getenv('QDRANT_HOST', 'localhost')  # default is 'localhost'
QDRANT_PORT = int(os.getenv('QDRANT_PORT', 6333))  # default is 6333

# Collection names
COLLECTION_AGENT_ROLES = "om_agent_roles"
COLLECTION_AGENT_CONVERSATION = "om_agent_conversations"
COLLECTION_USER_CONVERSATION = "om_user_conversations"

# 
MIN_CONTEXT_TO_SAVE = 2

def to_embedding_vector(s: str):
    """Converts a string into an embedding vector using the SentenceTransformer model.

    Args:
        s (str): The input string to vectorize.

    Returns:
        list: A list representing the embedding vector of the input string.
    """
    return embedding_model.encode(s, convert_to_tensor=True).tolist()

class DatabaseManager:
    """Handles interactions with Qdrant vector database for storing and retrieving conversation data."""

    def __init__(self):
        """Initializes the DatabaseManager, connects to Qdrant, and ensures the necessary collections exist."""

        # Qdrant (Vector Search)
        self.qdrant_client = QdrantClient(QDRANT_HOST, port=QDRANT_PORT)
        
        # Create collections if they don't exist
        self.check_and_create_collection(COLLECTION_AGENT_CONVERSATION)
        self.check_and_create_collection(COLLECTION_USER_CONVERSATION) 
        self.check_and_create_collection(COLLECTION_AGENT_ROLES) 


    def check_and_create_collection(self, cl_name, vector_size=VECTOR_DIM_SIZE):
        """
        Checks if a Qdrant collection exists and creates it if it doesn't.

        Args:
            cl_name (str): The name of the collection to check/create.
            vector_size (int, optional): The size of the vectors in the collection. Defaults to VECTOR_DIM_SIZE.
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
        """Returns the Qdrant client instance."""
        return self.qdrant_client
    
    
    def save_conversation_state(self, state: ConversationState):
        """Saves the conversation state to the Qdrant vector database.

        This function embeds the conversation context and stores it along with other relevant information
        in the specified collection.

        Args:
            state (ConversationState): The ConversationState object containing the data to be saved.
        """
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
        """Saves the user conversation state to the Qdrant vector database.

        Args:
            state (UserConversationState): The UserConversationState object containing the data to be saved.
        """
        if  len(state.user_message) > MIN_CONTEXT_TO_SAVE:
            try:       
                prompt_text = f"""
                    Extract context keywords from the following text. 
                    Must focus on the keywords that to enrich user profile and personal traits
                    Must provide a comma-separated list of keywords () without explanations.
                    The list has maximum 10 keywords.
                    
                Text: "{state.user_message}"
                Keywords:
                """
                response = gemini_model.generate_content(prompt_text)
                state.context = response.text if response and response.text else ""
            except Exception as e:  # Catch Gemini API errors
                print(f"Error generating response from Gemini: {e}")
                
        if  len(state.context) > MIN_CONTEXT_TO_SAVE:
            print(f"=> Context to vectorize from AI model: {state.context}")        
            embedding = to_embedding_vector(state.context)
            conversation_id = str(uuid.uuid4())

            self.qdrant_client.upsert(
                collection_name=COLLECTION_USER_CONVERSATION,
                points=[PointStruct(id=conversation_id, vector=embedding, payload=state.build_payload())]
            )


    def load_conversation_state(self, context: str, limit=2):
        """Searches for relevant conversation context in the Qdrant vector database.

        Args:
            context (str): The context to search for.  This will be vectorized and used as the query.
            limit (int, optional): The maximum number of results to return. Defaults to 2.

        Returns:
            list: A list of search results from Qdrant. Each result contains the point ID, vector, and payload.
                  Returns an empty list if the context is empty.
        """

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
    
    
    def load_user_conversation_state(self, profile_id: str, user_message: str, limit=10):
        """Searches for relevant user conversation context in the Qdrant vector database.

        Args:
            profile_id (str): The ID of the user to filter results.
            user_message (str): The user_message to search for. This will be vectorized and used as the query.
            limit (int, optional): The maximum number of results to return. Defaults to 2.

        Returns:
            list: A list of search results from Qdrant. Each result contains the point ID, vector, and payload.
                Returns an empty list if the context and profile_id are empty.
        """
        
        print(f'profile_id: {profile_id}, user_message:{user_message}')
        if len(profile_id) > 0 and len(user_message) > 0 :
            query_vector = to_embedding_vector(user_message)
            search_results = self.qdrant_client.search(
                collection_name=COLLECTION_USER_CONVERSATION,
                query_vector=query_vector,
                limit=limit,
                with_payload=True,
                search_params=SearchParams(hnsw_ef=128, exact=True),
                query_filter=Filter(
                    must=[
                        FieldCondition(key="profile_id", match=MatchValue(value=profile_id))
                    ]
                )
            )
            
            # Sort results by created_at in descending order at application level
            sorted_results = sorted(search_results, key=lambda x: x.payload.get("created_at", 0), reverse=True)
            return sorted_results
        else:
            print(f'profile_id and context is empty ')

        return []

   

class LangGraphAI:
    """Main AI Workflow using LangGraph."""

    def __init__(self, db_manager):
        """Initializes the LangGraphAI with a database manager and sets up the workflow."""
        self.db_manager = db_manager
        self.workflow = StateGraph(UserConversationState)  # ✅ Initialize LangGraph
        self._setup_workflow()  # ✅ Set up the workflow graph

    def _setup_workflow(self):
        """Defines the AI workflow graph."""
        
        # define agent nodes 
        self.workflow.add_node("detect_ai_persona", self.detect_ai_persona)
        self.workflow.add_node("retrieve_context", self.retrieve_context)
        self.workflow.add_node("generate_response", self.generate_response)

        # Define workflow transitions
        self.workflow.add_edge("detect_ai_persona", "retrieve_context")
        self.workflow.add_edge("retrieve_context", "generate_response")

        #  Set entry point for the workflow
        self.workflow.set_entry_point("detect_ai_persona")

        #  Compile the workflow properly
        self.workflow = self.workflow.compile()

    # 🔹 Hàm xác định vai trò của agent từ ngữ cảnh của người dùng

    def detect_ai_persona(self, state_dict) :
        """Determines the appropriate agent role based on the user's message using Qdrant.

        Args:
            state_dict (dict): A dictionary representing the current conversation state.

        Returns:
            dict: The updated conversation state dictionary, including the determined agent role.
        """
        
        state = UserConversationState.from_dict(state_dict) 
        embedding = to_embedding_vector(state.user_message)
        
        # Search for the most relevant agent role
        search_results = self.db_manager.get_qdrant_client().search(
            collection_name=COLLECTION_AGENT_ROLES,
            query_vector=embedding,
            limit=1,
            with_payload=True,
            search_params=SearchParams(hnsw_ef=128, exact=True),
        )
        
        if search_results:
            # Assuming the payload contains the agent role information
            # Adjust this based on how you store the agent role in the payload
            
            #Added error handling for cases with no 'agent_role' key in the payload
            default_agent_role = "default_agent"
            state.agent_role = search_results[0].payload.get("agent_role", default_agent_role)  
            return state.to_dict()
        else:
            state.agent_role = "default_agent"
            return state.to_dict()

    def retrieve_context(self, state_dict) :
        """Retrieves past relevant context from Qdrant based on the user message.

        Args:
            state_dict (dict): A dictionary representing the current conversation state.

        Returns:
            dict: The updated conversation state dictionary, including the retrieved context.
        """
        
        state = UserConversationState.from_dict(state_dict) 
        
        # TODO Use load user profile from db_manager
        
        if state.private_mode:
            state.user_profile = None
        else:
            state.user_profile = get_user_profile_for_ai_agent(state.profile_id)
        
        # Use load user conversation state from db_manager
        search_results = self.db_manager.load_user_conversation_state(state.profile_id, state.user_message)
        
        print(f"=> retrieve_context len(search_results) = {len(search_results)} ")
        
        contexts = []
        for result in search_results:
            context = result.payload["context"]
            if len(context) > 0: 
                context = context.replace("\n", "").replace("\r", "")           
                print(f"context {context}")
                contexts.append(context)
        
        # Extract keywords from the text
        #
        unique_keywords = remove_similar_keywords(contexts)
        
        state.context = ", ".join(unique_keywords)
        return state.to_dict()

    def generate_response(self, state_dict) :
        """Generates an AI response using Gemini, incorporating user message and retrieved context.

        Args:
            state_dict (dict): A dictionary representing the current conversation state.

        Returns:
            dict: The updated conversation state dictionary, including the generated AI response.
        """
        #prompt = f"User: {state.user_message}\nContext: {state.context}\nAgent Role: {state.agent_role}\nResponse:"
        print("state_dict \n ",state_dict)
        state = UserConversationState.from_dict(state_dict) 
        print("state \n ",state)
        try:            
            prompt_text = state.build_prompt()
            print(prompt_text)
            response = gemini_model.generate_content(prompt_text)
            state.response = response.text if response and response.text else "I'm sorry, I am unable to generate a response at this time."
        except Exception as e:  # Catch Gemini API errors
            print(f"Error generating response from Gemini: {e}")
            state.response = "I'm sorry, an error occurred while generating a response."
        return state.to_dict()

# Agent System 
agent_system_loaded = False
agent_system = None  # Declare as global to ensure accessibility

def init_ai_system():
    """Initializes the AI system (DatabaseManager and LangGraphAI) if it hasn't been initialized yet.
       Uses a global flag to ensure initialization only happens once.

       Returns:
           LangGraphAI: The initialized LangGraphAI instance.
    """
    global agent_system, agent_system_loaded  # Use global to persist changes
    if not agent_system_loaded:
        # Initialize system
        db_manager = DatabaseManager()
        agent_system = LangGraphAI(db_manager)
        agent_system_loaded = True  # Update flag
    return agent_system
        

def submit_message_to_agent(user_msg: Message):
    """Submits a user message to the AI agent, runs the LangGraph workflow, and returns the final state.

    Args:
        msg (Message): The user's message.

    Returns:
        UserConversationState: The final conversation state after processing the user message.
    """

    # Create an initial state
    initial_state = user_msg.to_conversation_state()

    # Run LangGraph workflow
    agent_system = init_ai_system()
    final_state_dict = agent_system.workflow.invoke(initial_state.to_dict()) 

    # Convert back to UserConversationState object
    final_state = UserConversationState.from_dict(final_state_dict)

    #Save conversation state to database for future context
    agent_system.db_manager.save_user_conversation_state(final_state)

    return final_state
   
def main():
    profile_id = str(uuid.uuid4())
    msg = "Tôi không thể ngủ vào ban đêm"
    final_state =  submit_message_to_agent(profile_id, msg)
   
    # Output AI's response
    print(f"User: {final_state.user_message}")
    print(f"AI Response: {final_state.response}")
    print(f"AI Agent Role: {final_state.agent_role}")
    print(f"AI context used: {final_state.context}")
