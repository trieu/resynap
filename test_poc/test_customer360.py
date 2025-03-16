from typing import List, Dict, Optional
from sqlalchemy import ForeignKey, JSON, Table, Column, String
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
from sqlalchemy.engine.url import URL

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5433")
PG_DATABASE = os.getenv("PG_DATABASE", "customer360")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "")

DATABASE_URL = URL.create(
    drivername="postgresql+asyncpg",
    username=PG_USER,
    password=PG_PASSWORD,
    host=PG_HOST,
    port=PG_PORT,
    database=PG_DATABASE,
)

engine = create_async_engine(DATABASE_URL)
async_session_maker = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


profile_product_association = Table(
    'profile_product_association', Base.metadata,
    Column('profile_id', String, ForeignKey('profiles.profile_id'), primary_key=True),
    Column('product_id', String, ForeignKey('products.product_id'), primary_key=True),
    Column('relationship_type', String, nullable=False)
)

class Profile(Base):
    __tablename__ = 'profiles'

    profile_id: Column[str] = Column(String, primary_key=True)
    page_view_keywords: Column[Optional[List[str]]] = Column(JSON)
    purchase_keywords: Column[Optional[List[str]]] = Column(JSON)
    interest_keywords: Column[Optional[List[str]]] = Column(JSON)
    additional_info: Column[Optional[Dict]] = Column(JSON)
    max_recommendation_size: Column[int] = Column(default=8)
    except_product_ids: Column[Optional[List[str]]] = Column(JSON)
    journey_maps: Column[Optional[List[str]]] = Column(JSON)

    linked_products: Column[List["Product"]] = relationship(
       "Product", secondary=profile_product_association, back_populates="linked_profiles"
    )

class Product(Base):
    __tablename__ = 'products'

    product_id: Column[str] = Column(String, primary_key=True)
    product_name: Column[str] = Column(String, nullable=False)
    product_category: Column[str] = Column(String, nullable=False)
    product_keywords: Column[Optional[List[str]]] = Column(JSON)
    additional_info: Column[Optional[Dict]] = Column(JSON)
    journey_maps: Column[Optional[List[str]]] = Column(JSON)

    linked_profiles: Column[List["Profile"]] = relationship(
       "Profile", secondary=profile_product_association, back_populates="linked_products"
    )

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
            existing_profile = await self.session.get(Profile, profile.profile_id)
            profile_data = profile.model_dump()  # Pydantic v2 fix
            if existing_profile:
                for key, value in profile_data.items():
                    setattr(existing_profile, key, value)
            else:
                new_profile = Profile(**profile_data)
                self.session.add(new_profile)
            await self.session.commit()
        except Exception as e:
            logging.error(f"Error adding profile: {e}")
            await self.session.rollback()
            raise

    async def add_product(self, product: ProductRequest):
        try:
            existing_product = await self.session.get(Product, product.product_id)
            product_data = product.model_dump()  # Pydantic v2 fix
            if existing_product:
                for key, value in product_data.items():
                    setattr(existing_product, key, value)
            else:
                new_product = Product(**product_data)
                self.session.add(new_product)
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
            if not profile:
                return None
            return profile.__dict__
        except Exception as e:
            logging.error(f"Error getting profile 360: {e}")
            raise

### sample data testing

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        customer360 = Customer360(session=session)

        # Sample profiles
        profiles = [
            ProfileRequest(
                profile_id=f"P{i}",
                page_view_keywords=["electronics", "smartphones", "gadgets"] if i % 2 == 0 else ["fashion", "clothing"],
                purchase_keywords=["iPhone", "Samsung"] if i % 2 == 0 else ["Nike", "Adidas"],
                interest_keywords=["technology", "gadgets"] if i % 2 == 0 else ["fitness", "outdoors"],
                additional_info={"age": 25 + i, "location": "City" + str(i)},
                except_product_ids=[f"X{i}", f"Y{i+1}"],
                journey_maps=[f"map{i}", f"map{i+1}"]
            ) for i in range(1, 6)
        ]

        # Sample products
        products = [
            ProductRequest(
                product_id=f"PR{i}",
                product_name=f"Product {i}",
                product_category="Electronics" if i % 2 == 0 else "Fashion",
                product_keywords=["tech", "AI"] if i % 2 == 0 else ["style", "comfort"],
                additional_info={"brand": "BrandX" if i % 2 == 0 else "BrandY"},
                journey_maps=[f"journey{i}"]
            ) for i in range(1, 6)
        ]

        # Add profiles and products
        for profile in profiles:
            await customer360.add_profile(profile)
            print("profile " + profile.profile_id + " added")
        

        for product in products:
            await customer360.add_product(product)
            print("product " + product.product_id + " added")

        # Link profiles to products
        for i in range(1, 6):
            profile_id = f"P{i}"
            product_id = f"PR{i}"
            relationship_type = "bought" if i % 2 == 0 else "interested"
            await customer360.link_profile_to_product(profile_id, product_id, relationship_type)
            print(f"linked profile {profile_id} to product {product_id}")

if __name__ == "__main__":
    asyncio.run(main())
