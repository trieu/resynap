from fastapi import FastAPI, HTTPException, Request, Depends
from personalization_models import ProfileRequest, ProductRequest, ContentRequest
from typing import List
import redis

from personalization import add_profile_to_qdrant, add_product_to_qdrant, add_content_to_qdrant, recommend_products_for_profile

import os
import traceback

# Fetch the host and port from environment variables
REDIS_HOST = os.getenv('REDIS_HOST', "")  # default is 'localhost'
REDIS_PORT = int(os.getenv('REDIS_PORT', 0))  # default is 6379
DEFAULT_AUTHORIZATION_KEY = os.getenv('DEFAULT_AUTHORIZATION_KEY', "")  # default is empty

# Initialize Redis connection
redis_db = False
if REDIS_HOST != "" and REDIS_PORT > 0:
    redis_db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

# FastAPI initialization
api_personalization = FastAPI()

# Middleware to check token in the request
async def verify_token(request: Request):
    token = request.headers.get('Authorization')
    if not token:
        raise HTTPException(status_code=401, detail="Authorization token is missing")
    
    # Validate token with Redis
    if redis_db != False:
        token_valid = redis_db.get(token)
    else:
        token_valid = DEFAULT_AUTHORIZATION_KEY == token
        
    if not token_valid:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# Endpoint to add profile
@api_personalization.post("/add-profile/", dependencies=[Depends(verify_token)])
async def add_profile(profile: ProfileRequest):
    try:
        add_profile_to_qdrant(
            profile.profile_id,
            profile.page_view_keywords,
            profile.purchase_keywords,
            profile.interest_keywords,
            profile.additional_info,
            profile.journey_maps
        )
        return {"status": "Profile added successfully"}
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint to check profile and get recommendation in real-time
@api_personalization.post("/check-profile-for-recommendation/", dependencies=[Depends(verify_token)])
async def add_profile(profile: ProfileRequest):
    try:
        profile_id = add_profile_to_qdrant(profile)       
        top_n = profile.max_recommendation_size
        except_product_ids = profile.except_product_ids
        in_journey_maps = profile.journey_maps
        rs = recommend_products_for_profile(profile_id, top_n, except_product_ids, in_journey_maps)
        if not rs:
            raise HTTPException(status_code=404, detail="Profile not found or no recommendations available")
        return rs
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint to add multiple profiles
@api_personalization.post("/add-profiles/", dependencies=[Depends(verify_token)])
async def add_profiles(profiles: List[ProfileRequest]):
    try:
        c = 0
        for profile in profiles:
            profile_id = add_profile_to_qdrant(profile)
            if profile_id:
                c = c + 1
                print(profile_id + " added successfully")
        return {"status": str(c) + " profiles added successfully"}
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint to add product
@api_personalization.post("/add-product/", dependencies=[Depends(verify_token)])
async def add_product(product: ProductRequest):
    try:
        add_product_to_qdrant(product)
        return {"status": "Product added successfully"}
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint to add multiple products
@api_personalization.post("/add-products/", dependencies=[Depends(verify_token)])
async def add_products(products: List[ProductRequest]):
    try:
        for product in products:
            add_product_to_qdrant(product)
        return {"status": "All products added successfully"}
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint to add content
@api_personalization.post("/add-content/", dependencies=[Depends(verify_token)])
async def add_content(content: ContentRequest):
    try:
        add_content_to_qdrant(content)
        return {"status": "Content added successfully"}
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
    
# Endpoint to add multiple contents
@api_personalization.post("/add-contents/", dependencies=[Depends(verify_token)])
async def add_contents(contents: List[ContentRequest]):
    try:
        for content in contents:
            add_content_to_qdrant(content)
        return {"status": "All contents added successfully"}
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint to recommend products based on profile
@api_personalization.get("/recommend/{profile_id}", dependencies=[Depends(verify_token)])
async def recommend(profile_id: str, top_n: int = 8, except_product_ids: str = "", journey_maps: str = ""):
    try:
        rs = recommend_products_for_profile(profile_id, top_n, get_input_array(except_product_ids), get_input_array(journey_maps))
        if not rs:
            raise HTTPException(
                status_code=404, detail="Profile not found or no recommendations available")
        return rs
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


def get_input_array(text, delimiter=","):
  """Splits a string by a delimiter and removes empty strings from the result.

  Args:
    text: The string to split.
    delimiter: The delimiter to split by (default is ",").

  Returns:
    A list of strings with empty strings removed.
  """

  return [item.strip() for item in text.split(delimiter) if item.strip()]