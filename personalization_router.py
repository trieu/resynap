from fastapi import FastAPI, HTTPException, Request, Depends
from personalization_models import ProfileRequest, ProductRequest
from typing import List
import redis

from personalization import add_profile_to_qdrant, add_product_to_qdrant, recommend_products_for_profile

from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv(override=True)

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
            profile.additional_info
        )
        return {"status": "Profile added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint to check profile and get recommendation in real-time
@api_personalization.post("/check-profile-for-recommendation/", dependencies=[Depends(verify_token)])
async def add_profile(profile: ProfileRequest):
    try:
        profile_id = add_profile_to_qdrant(
            profile.profile_id,
            profile.page_view_keywords,
            profile.purchase_keywords,
            profile.interest_keywords,
            profile.additional_info
        )        
        top_n = profile.max_recommendation_size
        except_product_ids = profile.except_product_ids
        rs = recommend_products_for_profile(profile_id, top_n, except_product_ids)
        if not rs:
            raise HTTPException(
                status_code=404, detail="Profile not found or no recommendations available")
        return rs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint to add multiple profiles
@api_personalization.post("/add-profiles/", dependencies=[Depends(verify_token)])
async def add_profiles(profiles: List[ProfileRequest]):
    try:
        for profile in profiles:
            add_profile_to_qdrant(
                profile.profile_id,
                profile.page_view_keywords,
                profile.purchase_keywords,
                profile.interest_keywords,
                profile.additional_info
            )
        return {"status": "All profiles added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint to add product
@api_personalization.post("/add-product/", dependencies=[Depends(verify_token)])
async def add_product(product: ProductRequest):
    try:
        add_product_to_qdrant(
            product.product_id,
            product.product_name,
            product.product_category,
            product.product_keywords,
            product.additional_info
        )
        return {"status": "Product added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint to add multiple products
@api_personalization.post("/add-products/", dependencies=[Depends(verify_token)])
async def add_products(products: List[ProductRequest]):
    try:
        for product in products:
            add_product_to_qdrant(
                product.product_id,
                product.product_name,
                product.product_category,
                product.product_keywords,
                product.additional_info
            )
        return {"status": "All products added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint to recommend products based on profile
@api_personalization.get("/recommend/{profile_id}", dependencies=[Depends(verify_token)])
async def recommend(profile_id: str, top_n: int = 8, except_product_ids: str = ""):
    try:
        rs = recommend_products_for_profile(profile_id, top_n, except_product_ids.split(","))
        if not rs:
            raise HTTPException(
                status_code=404, detail="Profile not found or no recommendations available")
        return rs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
