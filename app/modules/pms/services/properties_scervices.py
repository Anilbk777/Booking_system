from fastapi import UploadFile
from app.modules.pms.repositories.properties_repo import PropertyRepository
from app.modules.pms.models.properties_model import Property, PropertyPhoto
from app.utils.exceptions import (
    RepositoryException,
    ServiceException,
    PropertyAlreadyExistsException,
    PropertyNotFoundException,
    UnauthorizedException,
    InvalidImageException,
)
from app.utils.logging import LoggerFactory
from starlette.concurrency import run_in_threadpool
from app.utils.imgae_utils import process_property_image
import uuid

logger = LoggerFactory.get_logger(__name__)


class PropertyService:
    def __init__(self, property_repository: PropertyRepository):
        self.property_repository = property_repository

    async def create_property(
        self, property_data: dict, tenant_id: uuid.UUID
    ) -> Property:

        logger.info(f"[PropertyService] Creating property: {property_data}")
        try:
            # Check if property already exists
            existing_property = await self.property_repository.get_property_by_name(
                property_data["name"], tenant_id
            )
            if existing_property:
                logger.error(
                    f"[PropertyService] Property with name {property_data['name']} already exists"
                )
                raise PropertyAlreadyExistsException(
                    f"Property with name {property_data['name']} already exists"
                )

            property_data["tenant_id"] = tenant_id
            new_property = await self.property_repository.create_property(property_data)
            logger.info("[PropertyService] Property created successfully")
            return new_property

        except (PropertyAlreadyExistsException, RepositoryException):
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
                logger.error(
                    f"[PropertyService] Property with id {property_id} not found"
                )
                raise PropertyNotFoundException(
                    f"Property with id {property_id} not found"
                )
            if property.tenant_id != tenant_id:
                logger.error(
                    f"[PropertyService] Property does not belong to the tenant {tenant_id}"
                )
                raise UnauthorizedException(
                    f"Property does not belong to the tenant {tenant_id}"
                )
            logger.info("[PropertyService] Property found successfully")
            return property
        except (PropertyNotFoundException, UnauthorizedException, RepositoryException):
            raise
        except Exception as e:
            logger.error(f"[PropertyService] Error getting property by id: {str(e)}")
            raise ServiceException(str(e))

    async def update_property(
        self, property_id: uuid.UUID, tenant_id: uuid.UUID, property_data: dict
    ) -> Property:
        logger.info(f"[PropertyService] Updating property: {property_id}")
        try:
            existing_property = await self.get_property_by_id(property_id, tenant_id)
            if not existing_property:
                logger.error(
                    f"[PropertyService] Property with id {property_id} not found"
                )
                raise PropertyNotFoundException(f"Property {property_id} not found")

            updated = await self.property_repository.update_property(
                property_id, tenant_id, property_data
            )
            if not updated:
                logger.error(
                    f"[PropertyService] Property with id {property_id} not found"
                )
                raise PropertyNotFoundException(f"Property {property_id} not found")
            return updated
        except (PropertyNotFoundException, RepositoryException):
            raise
        except Exception as e:
            logger.error(f"[PropertyService] Error updating property: {str(e)}")
            raise ServiceException(str(e))

    async def delete_property(
        self, property_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> bool:
        logger.info(f"[PropertyService] Deleting property: {property_id}")
        try:
            existing_property = await self.get_property_by_id(property_id, tenant_id)
            if not existing_property:
                logger.error(
                    f"[PropertyService] Property with id {property_id} not found"
                )
                raise PropertyNotFoundException(f"Property {property_id} not found")
            success = await self.property_repository.delete_property(
                property_id, tenant_id
            )
            if not success:
                logger.error(
                    f"[PropertyService] Failed to delete property with id {property_id}"
                )
                raise RepositoryException(
                    f"Failed to delete property with id {property_id}"
                )
            return True
        except (PropertyNotFoundException, RepositoryException):
            raise
        except Exception as e:
            logger.error(f"[PropertyService] Error deleting property: {str(e)}")
            raise ServiceException(str(e))

    async def upload_images(
        self, property_id: uuid.UUID, files: list[UploadFile], tenant_id: uuid.UUID
    ) -> list[PropertyPhoto]:
        logger.info(f"[PropertyService] Uploading images for property: {property_id}")
        try:
            existing_property = await self.get_property_by_id(property_id, tenant_id)
            if not existing_property:
                logger.error(
                    f"[PropertyService] Property with id {property_id} not found"
                )
                raise PropertyNotFoundException(f"Property {property_id} not found")

            photo_objects = []

            for file in files:
                # 1. Read bytes safely
                file_bytes = await file.read()
                # 2. Process image (this handles all validation & resizing)
                filename = await run_in_threadpool(process_property_image, file_bytes)

                # Create the relative URL for the frontend to consume
                relative_url = f"/static/uploads/properties/{filename}"
                new_photo = PropertyPhoto(
                    property_id=property_id, photo_url=relative_url
                )
                photo_objects.append(new_photo)

            return await self.property_repository.add_images_to_property(
                property_id, photo_objects
            )
        except (PropertyNotFoundException, InvalidImageException):
            raise
        except Exception as exc:
            logger.error(
                f"[PropertyService] Error uploading images for {property_id}: {exc}"
            )
            raise ServiceException("Failed to upload images.")
