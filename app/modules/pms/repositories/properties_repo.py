from app.modules.pms.models.properties_model import Property, PropertyAmenity
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.utils.exceptions import RepositoryException
from app.utils.logging import LoggerFactory
import uuid

logger = LoggerFactory.get_logger(__name__)


class PropertyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_property(self, property: dict) -> Property:
        logger.info(f"[PropertyRepository] Creating property: {property}")
        try:
            new_property = Property(**property)
            self.db.add(new_property)
            await self.db.commit()
            await self.db.refresh(new_property)
            logger.info("[PropertyRepository] Property created successfully")
            return new_property
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
            if property:
                logger.info("[PropertyRepository] Property found")
            else:
                logger.error("[PropertyRepository] Property not found")
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
            if property:
                logger.info("[PropertyRepository] Property found")
            else:
                logger.error("[PropertyRepository] Property not found")
            return property
        except Exception as e:
            logger.error(f"[PropertyRepository] Error getting property by name: {str(e)}")
            raise RepositoryException(str(e))

    async def create_amenity(self, amenity: dict) -> PropertyAmenity:
        logger.info(f"[PropertyRepository] Creating amenity: {amenity}")
        try:
            new_amenity = PropertyAmenity(**amenity)
            self.db.add(new_amenity)
            await self.db.commit()
            await self.db.refresh(new_amenity)
            logger.info("[PropertyRepository] Amenity created successfully")
            return new_amenity
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[PropertyRepository] Error creating amenity: {str(e)}")
            raise RepositoryException(str(e))

    async def get_amenity_by_id(
        self, property_id: uuid.UUID
    ) -> PropertyAmenity | None:
        logger.info(f"[PropertyRepository] Getting amenity by id: {property_id}")
        try:
            result = await self.db.execute(
                select(PropertyAmenity).where(PropertyAmenity.property_id == property_id)
            )
            amenity = result.scalar_one_or_none()
            if amenity:
                logger.info("[PropertyRepository] Amenity found")
            else:
                logger.error("[PropertyRepository] Amenity not found")
            return amenity
        except Exception as e:
            logger.error(f"[PropertyRepository] Error getting amenity by id: {str(e)}")
            raise RepositoryException(str(e))