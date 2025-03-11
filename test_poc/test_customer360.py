from typing import List, Dict, Optional, Tuple
from sqlalchemy import create_engine, ForeignKey, JSON, Table, Column, String, select, update
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.dialects.postgresql import insert  # Import for upsert
from pydantic import BaseModel, Field

import os
from dotenv import load_dotenv
import asyncio
import logging

# Configure logging (best practice: do this once, globally)
logging.basicConfig(level=logging.WARNING)  # Set root logger level
# Reduce SQLAlchemy logging to WARNING to avoid the ROLLBACK messages in normal operation.
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)


load_dotenv()

# Database setup
from sqlalchemy.engine.url import URL

# ... (rest of your database setup code - PG_HOST, DATABASE_URL, etc.) ...
# Load environment variables
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5433")
PG_DATABASE = os.getenv("PG_DATABASE", "customer360")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "")

# Build SQLAlchemy connection URL
DATABASE_URL = URL.create(
    drivername="postgresql+asyncpg",
    username=PG_USER,
    password=PG_PASSWORD,
    host=PG_HOST,
    port=PG_PORT,
    database=PG_DATABASE,
)

# Use async engine for SQLAlchemy 2.0
engine = create_async_engine(DATABASE_URL)  # Logging controlled by logging module
async_session_maker = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


# Define Base class for SQLAlchemy 2.0
class Base(DeclarativeBase):
    pass


# Association table for many-to-many relationships
profile_product_association = Table(
    'profile_product_association', Base.metadata,
    Column('profile_id', String, ForeignKey('profiles.profile_id'), primary_key=True),
    Column('product_id', String, ForeignKey('products.product_id'), primary_key=True),
    Column('relationship_type', String, nullable=False)
)



class Profile(Base):
    __tablename__ = 'profiles'

    profile_id: Mapped[str] = mapped_column(primary_key=True)
    page_view_keywords: Mapped[Optional[List[str]]] = mapped_column(JSON)
    purchase_keywords: Mapped[Optional[List[str]]] = mapped_column(JSON)
    interest_keywords: Mapped[Optional[List[str]]] = mapped_column(JSON)
    additional_info: Mapped[Optional[Dict]] = mapped_column(JSON)
    max_recommendation_size: Mapped[int] = mapped_column(default=8)
    except_product_ids: Mapped[Optional[List[str]]] = mapped_column(JSON)
    journey_maps: Mapped[Optional[List[str]]] = mapped_column(JSON)

    linked_products: Mapped[List["Product"]] = relationship(
        secondary=profile_product_association, back_populates="linked_profiles", viewonly=False
    )


class Product(Base):
    __tablename__ = 'products'

    product_id: Mapped[str] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column(nullable=False)
    product_category: Mapped[str] = mapped_column(nullable=False)
    product_keywords: Mapped[Optional[List[str]]] = mapped_column(JSON)
    additional_info: Mapped[Optional[Dict]] = mapped_column(JSON)
    journey_maps: Mapped[Optional[List[str]]] = mapped_column(JSON)

    linked_profiles: Mapped[List["Profile"]] = relationship(
        secondary=profile_product_association, back_populates="linked_products", viewonly=False
    )



# Pydantic request models
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
            if existing_profile:
                for key, value in profile.model_dump().items():
                    setattr(existing_profile, key, value)
                await self.session.merge(existing_profile)
            else:
                new_profile = Profile(**profile.model_dump())
                self.session.add(new_profile)
            await self.session.commit()
            # Wrap refresh in a try-except block.  It's OK if refresh fails.
            try:
                await self.session.refresh(existing_profile if existing_profile else new_profile)
            except Exception as e:
                logging.warning(f"Refresh failed after adding/updating profile: {e}")

            return existing_profile if existing_profile else new_profile
        except Exception as e:
            logging.error(f"Error adding profile: {e}")
            await self.session.rollback()  # Rollback on ANY error
            raise  # Re-raise the exception to propagate it upwards


    async def add_product(self, product: ProductRequest):
        try:
            existing_product = await self.session.get(Product, product.product_id)
            if existing_product:
                for key, value in product.model_dump().items():
                    setattr(existing_product, key, value)
                await self.session.merge(existing_product)
            else:
                new_product = Product(**product.model_dump())
                self.session.add(new_product)
            await self.session.commit()
            # Wrap refresh in a try-except
            try:
                await self.session.refresh(existing_product if existing_product else new_product)
            except Exception as e:
                logging.warning(f"Refresh failed after adding/updating product: {e}")
            return existing_product if existing_product else new_product

        except Exception as e:
            logging.error(f"Error adding product: {e}")
            await self.session.rollback()
            raise

    async def link_profile_to_product(self, profile_id: str, product_id: str, relationship_type: str):
        try:
            stmt = insert(profile_product_association).values(
                profile_id=profile_id, product_id=product_id, relationship_type=relationship_type
            )
            update_stmt = stmt.on_conflict_do_update(
                index_elements=['profile_id', 'product_id'],
                set_={'relationship_type': relationship_type}
            )
            await self.session.execute(update_stmt)
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

            linked_products_result = await self.session.execute(
                select(Product, profile_product_association.c.relationship_type)
                .join(profile_product_association, profile_product_association.c.product_id == Product.product_id)
                .where(profile_product_association.c.profile_id == profile_id)
            )

            linked_products = []
            for product, relationship_type in linked_products_result:
                linked_products.append({
                    "product_id": product.product_id,
                    "product_name": product.product_name,
                    "relationship": relationship_type
                })
            profile_dict = profile.__dict__.copy()
            profile_dict.pop('_sa_instance_state', None)
            return {
                **profile_dict,
                "linked_products": linked_products
            }
        except Exception as e:
            logging.error(f"Error getting profile 360: {e}")
            #  Don't rollback here; this is a read-only operation.
            raise

    async def query_relationship(self, profile_id: str, relationship_type: str) -> List[Dict]:
        try:
            result = await self.session.execute(
                select(Product)
                .join(profile_product_association, profile_product_association.c.product_id == Product.product_id)
                .where(
                    profile_product_association.c.profile_id == profile_id,
                    profile_product_association.c.relationship_type == relationship_type
                )
            )
            return [{"product_id": row.product_id, "product_name": row.product_name} for row in result.scalars()]
        except Exception as e:
            logging.error(f"Error querying relationship: {e}")
            # Don't rollback; read-only operation
            raise

# Example Usage (Async)
async def main():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # Remove drop_all after initial run
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        customer360 = Customer360(session=session)

        try:
            profile = ProfileRequest(
                profile_id="P123",
                page_view_keywords=["electronics", "smartphones"],
                purchase_keywords=["iPhone", "Samsung"],
                interest_keywords=["technology", "gadgets"],
                additional_info={"age": 30, "location": "NYC"},
                except_product_ids=["X123", "Y456"],
                journey_maps=["map1", "map2"]
            )
            await customer360.add_profile(profile)

            profile2 = ProfileRequest(
                profile_id="P456",
                page_view_keywords=["books", "novels"],
                purchase_keywords=["fiction", "thriller"],
                interest_keywords=["reading", "literature"],
                additional_info={"age": 25, "location": "London"},
            )
            await customer360.add_profile(profile2)

            profile3 = ProfileRequest(
                profile_id="P789",
                page_view_keywords=["books", "magazines"],
                purchase_keywords=["non-fiction", "biography"],
                interest_keywords=["reading", "science"],
                additional_info={"age": 35, "location": "Vietnam"},
            )
            await customer360.add_profile(profile3)

            product = ProductRequest(
                product_id="PR001",
                product_name="iPhone 13",
                product_category="Smartphones",
                product_keywords=["Apple", "iPhone", "Mobile"],
                additional_info={"color": "black", "storage": "128GB"},
                journey_maps=["map1"]
            )
            await customer360.add_product(product)

            product2 = ProductRequest(
                product_id="PR002",
                product_name="The Lord of the Rings",
                product_category="Books",
                product_keywords=["Tolkien", "Fantasy", "Fiction"],
                additional_info={"author": "J.R.R. Tolkien"},
            )
            await customer360.add_product(product2)



            await customer360.link_profile_to_product("P123", "PR001", "purchased")
            await customer360.link_profile_to_product("P456", "PR002", "purchased")
            await customer360.link_profile_to_product("P123", "PR002", "viewed")  # link P123 to PR002

            profile_360 = await customer360.get_profile_360("P123")

            print(profile_360)
            print(await customer360.query_relationship("P123", "purchased"))
            print(await customer360.query_relationship("P123", "viewed"))
            print(await customer360.get_profile_360("P456"))
            # Test upsert (update relationship_type if it exists)
            await customer360.link_profile_to_product("P123", "PR001", "viewed")  # Change to "viewed"
            print(await customer360.get_profile_360("P123")) # Now shows "viewed" relationship
            await customer360.link_profile_to_product("P123", "PR001", "test")
            print(await customer360.get_profile_360("P123"))

        except Exception as e:
            print(f"An error occurred in main: {e}")
        finally:
            await session.close() # Close the session in a finally block
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())