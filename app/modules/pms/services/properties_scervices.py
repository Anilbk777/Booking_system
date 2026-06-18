from app.modules.pms.repositories.properties_repo import PropertyRepository
from app.modules.pms.models.properties_model import Property, PropertyAmenity
from app.utils.exceptions import (
    ServiceException,
    PropertyAlreadyExistsException,
    PropertyNotFoundException,
    UnauthorizedException,
)
from app.utils.logging import LoggerFactory
import uuid

logger = LoggerFactory.get_logger(__name__)


class PropertyService:
    def __init__(self, property_repository: PropertyRepository):
        self.property_repository = property_repository

    async def create_property(self, property: dict, tenant_id: uuid.UUID) -> Property:

        logger.info(f"[PropertyService] Creating property: {property}")
        try:
            # Check if property already exists
            existing_property = await self.property_repository.get_property_by_name(
                property["name"], tenant_id
            )
            if existing_property:
                raise PropertyAlreadyExistsException(
                    f"Property with name {property['name']} already exists"
                )

            property["tenant_id"] = tenant_id
            new_property = await self.property_repository.create_property(property)
            logger.info("[PropertyService] Property created successfully")
            return new_property

        except PropertyAlreadyExistsException:
            raise
        except Exception as e:
            logger.error(f"[PropertyService] Error creating property: {str(e)}")
            raise ServiceException(str(e))

    async def get_property_by_id(
        self, property_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> Property:
        logger.info(f"[PropertyService] Getting property by id: {property_id}")
        try:
            property = await self.property_repository.get_property_by_id(
                property_id, tenant_id
            )
            if not property:
                raise PropertyNotFoundException(
                    f"Property with id {property_id} not found"
                )
            if property.tenant_id != tenant_id:
                raise UnauthorizedException(
                    f"Property does not belong to the tenant {tenant_id}"
                )
            logger.info("[PropertyService] Property found successfully")
            return property
        except (PropertyNotFoundException, UnauthorizedException) as e:
            logger.error(f"[PropertyService] Error getting property by id: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"[PropertyService] Error getting property by id: {str(e)}")
            raise ServiceException(str(e))

    async def create_amenity(
        self, amenity: dict, tenant_id: uuid.UUID, property_id: uuid.UUID
    ) -> PropertyAmenity:
        logger.info(f"[PropertyService] Creating amenity: {amenity}")

        property = await self.property_repository.get_property_by_id(property_id)
        if not property:
            raise PropertyNotFoundException(f"Property with id {property_id} not found")
        if property.tenant_id != tenant_id:
            raise PropertyNotFoundException(
                f"Property does not belong to the tenant {tenant_id}"
            )

        try:
            amenity["property_id"] = property.id
            new_amenity = await self.property_repository.create_amenity(amenity)
            logger.info("[PropertyService] Amenity created successfully")
            return new_amenity
        except Exception as e:
            logger.error(f"[PropertyService] Error creating amenity: {str(e)}")
            raise ServiceException(str(e))

    async def get_amenity_by_id(self, property_id: uuid.UUID) -> PropertyAmenity:
        logger.info(f"[PropertyService] Getting amenity by id: {property_id}")
        try:
            amenity = await self.property_repository.get_amenity_by_id(property_id)
            return amenity
        except Exception as e:
            logger.error(f"[PropertyService] Error getting amenity by id: {str(e)}")
            raise ServiceException(str(e))
