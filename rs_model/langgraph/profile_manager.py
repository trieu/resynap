from typing import List, Dict, Optional
from sqlalchemy import ForeignKey, JSON, Table, Column, String, Integer
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.dialects.postgresql import insert
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.WARNING)
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

load_dotenv()

# Database setup
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5433")
PG_DATABASE = os.getenv("PG_DATABASE", "customer360")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "")

DATABASE_URL = f"postgresql+asyncpg://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}"
engine = create_async_engine(DATABASE_URL)
async_session_maker = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

# Association Table for Many-to-Many relationship
profile_product_association = Table(
    'profile_product_association', Base.metadata,
    Column('profile_id', String, ForeignKey('profiles.profile_id'), primary_key=True),
    Column('product_id', String, ForeignKey('products.product_id'), primary_key=True),
    Column('relationship_type', String, nullable=False)
)

class Profile(Base):
    __tablename__ = 'profiles'

    profile_id = Column(String, primary_key=True)
    page_view_keywords = Column(JSON, nullable=True)
    purchase_keywords = Column(JSON, nullable=True)
    interest_keywords = Column(JSON, nullable=True)
    additional_info = Column(JSON, nullable=True)
    max_recommendation_size = Column(Integer, default=8)
    except_product_ids = Column(JSON, nullable=True)
    journey_maps = Column(JSON, nullable=True)

    linked_products = relationship("Product", secondary=profile_product_association, back_populates="linked_profiles")

class Product(Base):
    __tablename__ = 'products'

    product_id = Column(String, primary_key=True)
    product_name = Column(String, nullable=False)
    product_category = Column(String, nullable=False)
    product_keywords = Column(JSON, nullable=True)
    additional_info = Column(JSON, nullable=True)
    journey_maps = Column(JSON, nullable=True)

    linked_profiles = relationship("Profile", secondary=profile_product_association, back_populates="linked_products")

class ProfileRequest(BaseModel):
    profile_id: str
    page_view_keywords: List[str] = []
    purchase_keywords: List[str] = []
    interest_keywords: List[str] = []
    additional_info: dict = {}
    max_recommendation_size: int = Field(8, description="Default recommendation is 8")
    except_product_ids: List[str] = []
    journey_maps: List[str] = []

class ProductRequest(BaseModel):
    product_id: str
    product_name: str
    product_category: str
    product_keywords: List[str] = []
    additional_info: dict = {}
    journey_maps: List[str] = []

class Customer360:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_profile(self, profile: ProfileRequest):
        try:
            profile_data = profile.model_dump()
            existing_profile = await self.session.get(Profile, profile.profile_id)
            if existing_profile:
                for key, value in profile_data.items():
                    setattr(existing_profile, key, value)
            else:
                new_profile = Profile(**profile_data)
                self.session.add(new_profile)
            print(profile_data)
            await self.session.commit()
        except Exception as e:
            logging.error(f"Error adding profile: {e}")
            await self.session.rollback()
            raise

    async def add_product(self, product: ProductRequest):
        try:
            product_data = product.model_dump()
            existing_product = await self.session.get(Product, product.product_id)
            if existing_product:
                for key, value in product_data.items():
                    setattr(existing_product, key, value)
            else:
                new_product = Product(**product_data)
                self.session.add(new_product)
            print(product_data)
            await self.session.commit()
        except Exception as e:
            logging.error(f"Error adding product: {e}")
            await self.session.rollback()
            raise

    async def link_profile_to_product(self, profile_id: str, product_id: str, relationship_type: str):
        try:
            stmt = insert(profile_product_association).values(
                profile_id=profile_id, product_id=product_id, relationship_type=relationship_type
            ).on_conflict_do_update(
                index_elements=['profile_id', 'product_id'],
                set_={'relationship_type': relationship_type}
            )
            await self.session.execute(stmt)
            await self.session.commit()
        except Exception as e:
            logging.error(f"Error linking profile to product: {e}")
            await self.session.rollback()
            raise

    async def get_profile_360(self, profile_id: str) -> Optional[Dict]:
        try:
            profile = await self.session.get(Profile, profile_id)
            return profile.__dict__ if profile else None
        except Exception as e:
            logging.error(f"Error getting profile 360: {e}")
            raise

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)



async def save_profile(profile: ProfileRequest):
    async with async_session_maker() as session:
        async with session.begin():  # Ensures transaction management
            customer360 = Customer360(session=session)
            await customer360.add_profile(profile)  # Ensure this method commits changes
    
    print(f"Profile {profile.profile_id} saved successfully!")



async def main():
    await init_db()
    
    await save_profile(ProfileRequest(profile_id="P6", page_view_keywords=["electronics"], purchase_keywords=["iPhone"],
                interest_keywords=["technology"], additional_info={"age": 40, "location": "Saigon"}))
    

    await add_sample_data()

async def add_sample_data():
    async with async_session_maker() as session:
        customer360 = Customer360(session=session)
        
        profiles = [ProfileRequest(profile_id=f"P{i}", page_view_keywords=["electronics"] if i % 2 == 0 else ["fashion"],
                    purchase_keywords=["iPhone"] if i % 2 == 0 else ["Nike"],
                    interest_keywords=["technology"] if i % 2 == 0 else ["fitness"],
                    additional_info={"age": 25 + i, "location": "City" + str(i)}) for i in range(1, 6)]
        
        products = [ProductRequest(product_id=f"PR{i}", product_name=f"Product {i}",
                    product_category="Electronics" if i % 2 == 0 else "Fashion") for i in range(1, 6)]
        
        for profile in profiles:
            await customer360.add_profile(profile)
        
        for product in products:
            await customer360.add_product(product)
        
        for i in range(1, 6):
            await customer360.link_profile_to_product(f"P{i}", f"PR{i}", "bought" if i % 2 == 0 else "interested")

if __name__ == "__main__":
    asyncio.run(main())
    
