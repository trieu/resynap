
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, MatchExcept, Filter, MatchAny
from qdrant_client.http.models import VectorParams, Distance, FieldCondition
from sentence_transformers import SentenceTransformer
from rs_model.personalization_models import ContentRequest, ProfileRequest, ProductRequest
import hashlib
import os

# Fetch the host and port from environment variables
QDRANT_HOST = os.getenv('QDRANT_HOST', 'localhost')  # default is 'localhost'
QDRANT_PORT = int(os.getenv('QDRANT_PORT', 6333))  # default is 6333

# Fetch the host and port from environment variables
QDRANT_CLOUD_HOST = os.getenv('QDRANT_CLOUD_HOST', '')  # default is empty
QDRANT_CLOUD_API_KEY = os.getenv('QDRANT_CLOUD_API_KEY', '')  # default is empty

# Initialize QdrantClient with the loaded values
qdrant_client = False
if QDRANT_CLOUD_HOST != "" and QDRANT_CLOUD_API_KEY != "":
    qdrant_client = QdrantClient(host=QDRANT_CLOUD_HOST, api_key=QDRANT_CLOUD_API_KEY)
    print('USING QDRANT CLOUD DB ' + QDRANT_CLOUD_HOST)
else:
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    print('USING LOCAL QDRANT DB ' + QDRANT_HOST)

# Data collections in Qdrant
PROFILE_COLLECTION = "cdp_profile"
PRODUCT_COLLECTION = "cdp_product"
CONTENT_COLLECTION = "cdp_content"

# vector model
MODEL_NAME = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
VECTOR_MODEL = SentenceTransformer(MODEL_NAME)
VECTOR_DIM_SIZE = VECTOR_MODEL.get_sentence_embedding_dimension()
print('Load vector model:', MODEL_NAME, 'with dim:', VECTOR_DIM_SIZE)

# vector size
PROFILE_VECTOR_SIZE = VECTOR_DIM_SIZE
PRODUCT_VECTOR_SIZE = VECTOR_DIM_SIZE * 3
CONTENT_VECTOR_SIZE = VECTOR_DIM_SIZE

# Function to get the text embeddings
def get_text_embedding(text):
    if not text or not isinstance(text, str):
        print(f"Error: Invalid text input for embedding: {text}")
        # Return a zero vector if the text is invalid
        return np.zeros(VECTOR_DIM_SIZE)

    # Generate embeddings using the VECTOR_MODEL
    text_embedding = VECTOR_MODEL.encode(text, convert_to_tensor=True)

    # Ensure tensor is on CPU before converting to NumPy
    if text_embedding.is_cuda:
        numpy_embedding = text_embedding.cpu().numpy()
    else:
        numpy_embedding = text_embedding.numpy()

    return numpy_embedding

# get all collections in Qdrant
def get_all_collection_names_in_qdrant():
    existing_collections = qdrant_client.get_collections().collections
    return existing_collections

# Updated function to create collection in Qdrant
def create_qdrant_collection_if_not_exists(collection_name: str, vector_size: int):
    # Check if collection already exists
    existing_collections = qdrant_client.get_collections().collections
    if collection_name not in [col.name for col in existing_collections]:
        # Create collection with vectors_config
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size, distance=Distance.COSINE)
        )
        print(f"Collection '{collection_name}' created successfully.")
    else:
        print(f"Collection '{collection_name}' already exists.")


# Build profile vector based on attributes
def build_profile_vector(page_view_keywords, purchase_keywords, interest_keywords, journey_maps=[]):
    # Ensure none of the input lists are empty to avoid issues
    if not page_view_keywords or not purchase_keywords or not interest_keywords:
        print("Error: One or more keyword lists are empty.")
        return None

    # Get embeddings for page views, purchases, and interests
    page_view_vectors = np.array([get_text_embedding(k)
                                 for k in page_view_keywords])
    purchase_vectors = np.array([get_text_embedding(k)
                                for k in purchase_keywords])
    interest_vectors = np.array([get_text_embedding(k)
                                for k in interest_keywords])

    # Aggregate vectors by averaging or weighted sum
    page_view_vector = np.mean(page_view_vectors, axis=0)
    purchase_vector = np.mean(purchase_vectors, axis=0)
    interest_vector = np.mean(interest_vectors, axis=0)

    # Final profile vector by combining (weights can be adjusted)
    if len(journey_maps) > 0:
        journey_vectors = np.array([get_text_embedding(k) for k in journey_maps])
        journey_vector = np.mean(journey_vectors, axis=0)
        profile_vector = 0.2 * page_view_vector + 0.3 * \
            purchase_vector + 0.4 * interest_vector + 0.1 * journey_vector
    else:
        profile_vector = 0.3 * page_view_vector + 0.4 * \
            purchase_vector + 0.3 * interest_vector
    return profile_vector



# Build content vector based on attributes
def build_content_vector(content_title, content_category, content_keywords):
    # Ensure none of the input lists are empty to avoid issues
    if not content_title or not content_category or not content_keywords:
        print("Error: One or more keyword lists are empty.")
        return None

    # Get embeddings for title, category and keywords
    title_embedding = np.array([get_text_embedding(content_title)])
    category_embedding = np.array([get_text_embedding(content_category)])
    keyword_embeddings = np.array([get_text_embedding(k)
                                for k in content_keywords])

    # Aggregate vectors by averaging or weighted sum
    title_vector = np.mean(title_embedding, axis=0)
    category_vector = np.mean(category_embedding, axis=0)
    keyword_vector = np.mean(keyword_embeddings, axis=0)

    # Final profile vector by combining (weights can be adjusted)
    content_vector = 0.3 * title_vector + 0.4 * category_vector + 0.3 * keyword_vector
        
    return content_vector

# Build product vector based on attributes
def build_product_vector(product_name, product_category, product_keywords, journey_maps=[]):
    # Can use advanced models like BERT for better embeddings
    name_vector = get_text_embedding(product_name)
    category_vector = get_text_embedding(product_category)
    keyword_vectors = np.array([get_text_embedding(k)
                               for k in product_keywords])

    # Final product vector by concatenating all (can use other combination strategies)
    if len(journey_maps) > 0:
        journey_vectors = np.array([get_text_embedding(k)
                                   for k in journey_maps])

        weight_keywords = 0.4
        weight_journeys = 0.6

        # Calculate the weighted mean along the desired axis (usually axis=0 for combining vectors)
        mean_of_keywords_journeys = (weight_keywords * np.mean(keyword_vectors, axis=0) +
                                     weight_journeys * np.mean(journey_vectors, axis=0))

        product_vector = np.concatenate(
            [name_vector, category_vector, mean_of_keywords_journeys])
    else:
        # Aggregate keyword vectors by averaging
        keyword_vector = np.mean(keyword_vectors, axis=0)
        product_vector = np.concatenate(
            [name_vector, category_vector, keyword_vector])
    return product_vector

# Convert string to point_id using hashlib for large dataset
def string_to_point_id(input_string):
    # Use SHA-256 hash and convert it to an integer with 16 digits
    # the resulting integer to a range between 0 and 99,999,999,999,999,999 (16 digits).
    return int(hashlib.sha256(input_string.encode('utf-8')).hexdigest(), 16) % (10 ** 16)

# Helper function to add vectors to Qdrant collection
def add_vector_to_qdrant(collection_name: str, object_id, vector, payload):
    point_id = string_to_point_id(str(object_id))
    point = PointStruct(
        id=point_id,  # Use profile_id as the point ID
        vector=vector.tolist(),  # Store the vector
        payload=payload
    )
    qdrant_client.upsert(
        collection_name=collection_name,
        points=[point]
    )

# Function to add profile to Qdrant
def add_profile_to_qdrant(p: ProfileRequest):
    try: 
        profile_id = p.profile_id
        profile_vector = build_profile_vector(p.page_view_keywords, p.purchase_keywords, p.interest_keywords, p.journey_maps)

        if profile_vector is None:
            print(
                f"Error: Could not generate a valid vector for profile {profile_id}.")
            return

        # Save profile vector to Qdrant
        payload = {"profile_id": profile_id, "additional_info": p.additional_info}
        payload['page_view_keywords'] = p.page_view_keywords
        payload['purchase_keywords'] = p.purchase_keywords
        payload['interest_keywords'] = p.interest_keywords
        payload['journey_maps'] = p.journey_maps
        add_vector_to_qdrant(PROFILE_COLLECTION, profile_id, profile_vector, payload)
        print(f"Profile {profile_id} added to Qdrant")
        return profile_id
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        
    return ''



# Function to add product to Qdrant
def add_product_to_qdrant(p: ProductRequest):
    product_id = p.product_id
    # Generate product vector
    product_vector = build_product_vector(p.product_name, p.product_category, p.product_keywords, p.journey_maps)
    if product_vector is None:
        print(
            f"Error: Could not generate a valid vector for product {product_name} with ID {product_id}.")
        return

    # Save product vector to Qdrant
    payload = {"product_id": product_id, "name": p.product_name,  
               "keywords": p.product_keywords, "url": p.url,
               "category": p.product_category, "additional_info": p.additional_info,
               "journey_maps": p.journey_maps}
    add_vector_to_qdrant(PRODUCT_COLLECTION, product_id, product_vector, payload)
    print(f"Product {product_id} added to Qdrant")
    return product_id

# Function to add content to Qdrant
def add_content_to_qdrant(c: ContentRequest):
    content_id = c.content_id
    # Generate content vector
    content_vector = build_content_vector(c.title, c.content_category, c.content_keywords)
    if content_vector is None:
        print(
            f"Error: Could not generate a valid vector for content title {c.title} with ID {content_id}.")
        return

    # Save product vector to Qdrant
    payload = {"content_id": content_id, "title": c.title, "url": c.url, 
               "description": c.description, "content": c.content,
               "content_type": c.content_type, "keywords": c.content_keywords,
               "category": c.content_category, "additional_info": c.additional_info,
               "journey_maps": c.journey_maps}
    add_vector_to_qdrant(CONTENT_COLLECTION, content_id, content_vector, payload)
    print(f"Content {content_id} added to Qdrant")
    return content_id

# Recommend products based on profile vector
def recommend_products_for_profile(profile_id, top_n=8, except_product_ids=[], in_journey_maps=[]):
    try:
        point_id = string_to_point_id(profile_id)
        profile_data = qdrant_client.retrieve(
            collection_name=PROFILE_COLLECTION,
            ids=[point_id]  # Fetch the point with the given profile_id
        )
        print(profile_data)

        # Check if profile exists and has a vector
        if not profile_data or len(profile_data) == 0:
            print(f"Profile {profile_id} not found in Qdrant.")
            return []

        profile = profile_data[0]
        if len(profile.payload) == 0:
            print(f"Profile {profile_id} does not have a vector in Qdrant.")
            return []

        profile_vector = build_profile_vector(
            profile.payload['page_view_keywords'],
            profile.payload['purchase_keywords'],
            profile.payload['interest_keywords'],
            profile.payload['journey_maps']
        )

        # the vector to query
        search_vector = np.concatenate(
            [profile_vector, profile_vector, profile_vector])

        # filters
        must_filter = []
        if len(in_journey_maps) > 0:
            must_filter.append(FieldCondition(key="journey_maps", match=MatchAny(any=in_journey_maps)))
        if len(except_product_ids) > 0:
            must_filter.append(FieldCondition(key="product_id", match=MatchExcept(**{"except": except_product_ids})))
        
        print(len(in_journey_maps))
        print(len(except_product_ids))
        print(must_filter)
            
        # Use profile vector to search for closest products in the product collection
        search_results = qdrant_client.search(
            collection_name=PRODUCT_COLLECTION,
            query_vector=search_vector,
            query_filter=Filter( must=must_filter),
            limit=top_n
        )

        # Extract product information from the search results
        recommended_products = [
            {
                "product_id": result.payload.get('product_id'),
                "product_name": result.payload.get('name'),
                "product_category": result.payload.get('category'),
                "brand": result.payload.get('additional_info')['brand'],
                "price": result.payload.get('additional_info')['price'],
                "journey_maps": result.payload.get('journey_maps'),
                "score": result.score
            }
            for result in search_results
        ]

        return {"profile": profile.payload, "recommended_products": recommended_products}

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return []


def init_db_personalization():
    if qdrant_client == False:
        raise Exception("qdrant_client is NULL")
    ### Create collections if not exist ###
    create_qdrant_collection_if_not_exists(
        PROFILE_COLLECTION, PROFILE_VECTOR_SIZE)
    create_qdrant_collection_if_not_exists(
        PRODUCT_COLLECTION, PRODUCT_VECTOR_SIZE)
    create_qdrant_collection_if_not_exists(
        CONTENT_COLLECTION, CONTENT_VECTOR_SIZE)
