import uuid

from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool

from app.modules.pms.models.properties_model import (
    Amenity,
    Property,
    PropertyAmenity,
    PropertyHotelDetail,
    PropertyPhoto,
)
from app.modules.pms.repositories.properties_repo import PropertyRepository
from app.modules.pms.schemas.properties_schemas import PropertyCreate
from app.utils.exceptions import (
    InvalidImageException,
    PropertyAlreadyExistsException,
    PropertyNotFoundException,
    RepositoryException,
    ServiceException,
    UnauthorizedException,
    DefaultAmenityNotExistsException,
)
from app.utils.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class PropertyService:
    def __init__(self, property_repository: PropertyRepository):
        self.property_repository = property_repository

    async def create_property(self, payload: PropertyCreate, tenant_id: uuid.UUID):
        logger.info(f"[PropertyService] Creating property: {payload}")
        # 1. Convert Pydantic payload to clean dictionary mappings
        payload_dict = payload.model_dump()

        # 2. Extract nested relational segments to keep the base dictionary clean
        hotel_detail_data = payload_dict.pop("hotel_detail")
        amenities_input = payload_dict.pop("amenities")
        photo_urls_data = payload_dict.pop("photo_urls")

        # Check if property already exists
        existing_property = await self.property_repository.get_property_by_name(
            payload_dict["name"], tenant_id
        )
        if existing_property:
            logger.error(
                f"[PropertyService] Property with name {payload_dict['name']} already exists"
            )
            raise PropertyAlreadyExistsException(
                f"Property with name {payload_dict['name']} already exists"
            )

        try:
            return await self.property_repository.create_property_transactional(
                tenant_id=tenant_id,
                property_data=payload_dict,
                hotel_detail_data=hotel_detail_data,
                amenities_input=amenities_input,
                photo_urls=photo_urls_data,
            )

        except (RepositoryException, DefaultAmenityNotExistsException):
            raise

        except Exception as e:
            logger.error(f"[PropertyService] Error creating property: {str(e)}")
            raise ServiceException(str(e))

    async def get_all_properties(self, tenant_id: uuid.UUID):
        logger.info(f"[PropertyService] Getting all properties for tenant: {tenant_id}")
        try:
            return await self.property_repository.get_all_properties(tenant_id)
        except RepositoryException:
            raise
        except Exception as e:
            logger.error(f"[PropertyService] Error getting all properties: {str(e)}")
            raise ServiceException(str(e))

    async def get_property_details_by_id(
        self, property_id: uuid.UUID, tenant_id: uuid.UUID
    ):
        logger.info(f"[PropertyService] Getting property details by id: {property_id}")

        existing_property = await self.property_repository.get_property_by_id(
            property_id, tenant_id
        )
        if not existing_property:
            logger.error(f"[PropertyService] Property with id {property_id} not found")
            raise PropertyNotFoundException(f"Property with id {property_id} not found")

        try:
            return await self.property_repository.get_property_details_by_id(
                property_id, tenant_id
            )
        except (PropertyNotFoundException, UnauthorizedException, RepositoryException):
            raise
        except Exception as e:
            logger.error(
                f"[PropertyService] Error getting property details by id: {str(e)}"
            )
            raise ServiceException(str(e))

    async def update_property(self, property_id: uuid.UUID, tenant_id: uuid.UUID, payload: PropertyCreate):
        logger.info(f"[PropertyService] Updating property: {property_id}")

        # 1. Convert Pydantic payload to clean dictionary mappings
        payload_dict = payload.model_dump()

        # 2. Extract nested relational segments to keep the base dictionary clean
        hotel_detail_data = payload_dict.pop("hotel_detail")
        amenities_input = payload_dict.pop("amenities")
        photo_urls_data = payload_dict.pop("photo_urls")

        # Check if property already exists
        existing_property = await self.property_repository.get_property_by_name(
            payload_dict["name"], tenant_id
        )
        if existing_property and existing_property.id != property_id:
            logger.error(
                f"[PropertyService] Property with name {payload_dict['name']} already exists"
            )
            raise PropertyAlreadyExistsException(
                f"Property with name {payload_dict['name']} already exists"
            )
        

        try:
            return await self.property_repository.update_property(
                property_id, tenant_id, payload_dict, hotel_detail_data, amenities_input, photo_urls_data
            )
        except (PropertyNotFoundException,PropertyAlreadyExistsException, UnauthorizedException, RepositoryException):
            raise
        except Exception as e:
            logger.error(f"[PropertyService] Error updating property: {str(e)}")
            raise ServiceException(str(e))
