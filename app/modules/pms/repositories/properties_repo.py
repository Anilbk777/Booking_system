from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete

from app.utils.exceptions import RepositoryException
from app.utils.logging import LoggerFactory

from app.modules.pms.models.properties_model import Property
import uuid

logger = LoggerFactory.get_logger(__name__)


class PropertyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_property(self, property_data: dict) -> Property:
        logger.info(
            f"[PropertyRepository] Creating property: {property_data['name']} of tenant {property_data['tenant_id']}"
        )
        try:
            new_property = Property(**property_data)
            self.db.add(new_property)
            await self.db.commit()
            await self.db.refresh(new_property)
            logger.info("[PropertyRepository] Property created successfully")
            return new_property
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(
                "[PropertyRepository] Error creating property: Integrity constraint violated"
            )
            raise RepositoryException(f"Integrity constraint violated: {str(e)}")
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error("[PropertyRepository] Error creating property: SQLA  ")
            raise RepositoryException(f"SQLAlchemy error: {str(e)}")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[PropertyRepository] Error creating property: {str(e)}")
            raise RepositoryException(str(e))

    async def get_property_by_id(
        self, property_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> Property | None:
        logger.info(f"[PropertyRepository] Getting property by id: {property_id}")
        try:
            result = await self.db.execute(
                select(Property).where(
                    Property.id == property_id,
                    Property.tenant_id == tenant_id,
                )
            )
            property = result.scalar_one_or_none()
            return property
        except Exception as e:
            logger.error(f"[PropertyRepository] Error getting property by id: {str(e)}")
            raise RepositoryException(str(e))

    async def get_property_by_name(
        self, property_name: str, tenant_id: uuid.UUID
    ) -> Property | None:
        logger.info(f"[PropertyRepository] Getting property by name: {property_name}")
        try:
            result = await self.db.execute(
                select(Property).where(
                    func.lower(Property.name) == property_name.lower(),
                    Property.tenant_id == tenant_id,
                )
            )
            property = result.scalar_one_or_none()
            return property
        except Exception as e:
            logger.error(
                f"[PropertyRepository] Error getting property by name: {str(e)}"
            )
            raise RepositoryException(str(e))

    async def update_property(
        self, property_id: uuid.UUID, tenant_id: uuid.UUID, property_data: dict
    ) -> Property | None:
        logger.info(f"[PropertyRepository] Updating property: {property_id}")
        try:
            query = (
                update(Property)
                .where(Property.id == property_id, Property.tenant_id == tenant_id)
                .values(**property_data)
                .returning(Property)
            )
            result = await self.db.execute(query)
            updated_property = result.scalars().first()
            await self.db.commit()
            return updated_property
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[PropertyRepository] Error updating property: {str(e)}")
            raise RepositoryException(str(e))

    async def delete_property(
        self, property_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> bool:
        logger.info(f"[PropertyRepository] Deleting property: {property_id}")
        try:
            query = delete(Property).where(
                Property.id == property_id, Property.tenant_id == tenant_id
            )
            result = await self.db.execute(query)
            await self.db.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[PropertyRepository] Error deleting property: {str(e)}")
            raise RepositoryException(str(e))
