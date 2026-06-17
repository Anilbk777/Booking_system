from app.modules.pms.repositories.properties_repo import PropertyRepository
from app.modules.pms.services.tenant_services import TenantService
from app.modules.pms.models.properties_model import Property
from app.modules.pms.models.tenants_model import Tenant
from app.utils.exceptions import (
    ServiceException,
    PropertyAlreadyExistsException,
    PropertyNotFoundException,
    TenantNotFoundException,
)
from app.utils.logging import LoggerFactory
import uuid

logger = LoggerFactory.get_logger(__name__)


class PropertyService:
    def __init__(
        self, property_repository: PropertyRepository, tenant_service: TenantService
    ):
        self.property_repository = property_repository
        self.tenant_service = tenant_service

    async def _get_tenant_by_owner_id(self, owner_id: uuid.UUID) -> Tenant:
        logger.info(f"[PropertyService] Getting tenant by owner id: {owner_id}")
        try:
            tenant = await self.tenant_service.get_tenant_by_owner_id(owner_id)
            if not tenant:
                raise TenantNotFoundException(
                    f"Tenant with owner id {owner_id} not found"
                )
            logger.info("[PropertyService] Tenant found successfully")
            return tenant
        except TenantNotFoundException:
            raise
        except Exception as e:
            logger.error(
                f"[PropertyService] Error getting tenant by owner id: {str(e)}"
            )
            raise ServiceException(str(e))

    async def create_property(self, property: dict, owner_id: uuid.UUID) -> Property:

        logger.info(f"[PropertyService] Creating property: {property}")
        tenant = await self._get_tenant_by_owner_id(owner_id)
        try:
            # Check if property already exists
            existing_property = await self.property_repository.get_property_by_name(
                property["name"], tenant.id
            )
            if existing_property:
                raise PropertyAlreadyExistsException(
                    f"Property with name {property['name']} already exists"
                )

            # Create property
            property["tenant_id"] = tenant.id
            new_property = await self.property_repository.create_property(property)
            logger.info("[PropertyService] Property created successfully")
            return new_property

        except (PropertyAlreadyExistsException, TenantNotFoundException):
            raise
        except Exception as e:
            logger.error(f"[PropertyService] Error creating property: {str(e)}")
            raise ServiceException(str(e))

    async def get_property_by_id(
        self, property_id: uuid.UUID, owner_id: uuid.UUID
    ) -> Property:
        logger.info(f"[PropertyService] Getting property by id: {property_id}")
        tenant = await self._get_tenant_by_owner_id(owner_id)
        tenant_id = tenant.id
        try:
            property = await self.property_repository.get_property_by_id(property_id)
            if not property:
                raise PropertyNotFoundException(
                    f"Property with id {property_id} not found"
                )
            if property.tenant_id != tenant_id:
                raise PropertyNotFoundException(
                    f"Property does not belong to the tenant {tenant_id}"
                )
            logger.info("[PropertyService] Property found successfully")
            return property
        except (PropertyNotFoundException, TenantNotFoundException):
            raise
        except Exception as e:
            logger.error(f"[PropertyService] Error getting property by id: {str(e)}")
            raise ServiceException(str(e))
