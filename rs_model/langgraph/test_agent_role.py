import os
import uuid
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, SearchParams
from qdrant_client.http.models import Distance, VectorParams
from langgraph_ai import ConversationState, embedding_model

# Fetch the host and port from environment variables
QDRANT_HOST = os.getenv('QDRANT_HOST', 'localhost')  # Default to localhost
QDRANT_PORT = int(os.getenv('QDRANT_PORT', 6333))  # Default to 6333

class AgentRoleManager:
    """Handles agent role assignment using Qdrant vector search."""
    
    def __init__(self):
        self.qdrant_client = QdrantClient(QDRANT_HOST, port=QDRANT_PORT)
        self.collection_name = "om_agent_roles"

        # Ensure collection exists in Qdrant
        if self.collection_name not in self.qdrant_client.get_collections().collections:
            self.qdrant_client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=embedding_model.get_sentence_embedding_dimension(), 
                                            distance=Distance.COSINE),
            )
        
        self.setup_roles_in_qdrant()

    def setup_roles_in_qdrant(self):
        """Stores predefined agent roles in Qdrant with their embeddings."""
        predefined_roles = {
            "psychologist": "I need emotional support and guidance.",
            "technical_support": "I have an issue with my software or device.",
            "sales_representative": "I am looking for information about a product.",
            "customer_service": "I need help with my order or account.",
        }

        # Generate embeddings and store in Qdrant
        points = []
        for role, description in predefined_roles.items():
            embedding = embedding_model.encode(description, convert_to_tensor=True).tolist()
            points.append(PointStruct(id=str(uuid.uuid4()), vector=embedding, payload={"role": role}))

        self.qdrant_client.upsert(collection_name=self.collection_name, points=points)

    def determine_agent_role(self, state: ConversationState) -> ConversationState:
        """Uses Qdrant to determine the best-matching agent role based on user_message."""
        user_embedding = embedding_model.encode(state.user_message, convert_to_tensor=True).tolist()

        # Perform nearest neighbor search in Qdrant
        search_results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=user_embedding,
            limit=1,  # Get top match
            with_payload=True,
            search_params=SearchParams(hnsw_ef=128, exact=True)
        )

        if search_results:
            state.agent_role = search_results[0].payload["role"]
        else:
            state.agent_role = "default_agent"  # Fallback role if no match is found

        return state


# ✅ **Test function for agent role detection using Qdrant**
def test_agent_role_detection():
    agent_role_manager = AgentRoleManager()

    test_cases = [
        ("I feel very stressed and need someone to talk to.", "psychologist"),
        ("My internet is not working, can you help?", "technical_support"),
        ("What are the latest discounts on your products?", "sales_representative"),
        ("I want to track my order, can you assist?", "customer_service"),
    ]
    
    for user_message, expected_role in test_cases:
        state = ConversationState(profile_id="test", user_message=user_message)
        state = agent_role_manager.determine_agent_role(state)
        assert state.agent_role == expected_role, f"Expected {expected_role}, got {state.agent_role}"

    print("✅ All agent role detection tests passed!")

# Run the test
test_agent_role_detection()
