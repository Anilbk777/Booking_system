from app.modules.pms.repositories.tenants_repo import TenantRepository
from app.utils.exceptions import (
    ServiceException,
    TenantAlreadyExistsException,
    TenantNotFoundException,
)
from app.utils.logging import LoggerFactory
import uuid
from app.modules.pms.models.tenants_model import Tenant

logger = LoggerFactory.get_logger(__name__)


class TenantService:
    def __init__(self, tenant_repo: TenantRepository):
        self.tenant_repo = tenant_repo

    async def create_tenant(self, tenant: dict, owner_id: uuid.UUID) -> Tenant:
        logger.info(f"[TenantService] Creating tenant: {tenant}")
        tenant_data = tenant
        tenant_data["owner_id"] = owner_id
        try:
            existing_tenant = await self.tenant_repo.get_tenant_by_name(tenant["name"], owner_id)
            if existing_tenant:
                logger.info("[TenantService] Tenant already exists")
                raise TenantAlreadyExistsException(
                    f"Tenant with name {tenant_data['name']} already exists"
                )
            new_tenant = await self.tenant_repo.create_tenant(tenant_data)
            logger.info("[TenantService] Tenant created successfully")
            return new_tenant

        except TenantAlreadyExistsException:
            raise
        except Exception as e:
            logger.error(f"[TenantService] Error creating tenant: {str(e)}")
            raise ServiceException(str(e))

    async def get_tenant_by_owner_id(
        self, owner_id: uuid.UUID
    ) -> Tenant:
        logger.info(f"[TenantService] Getting tenant by owner id: {owner_id}")
        try:
            tenant = await self.tenant_repo.get_tenant_by_owner_id(owner_id)
            if not tenant:
                logger.error("[TenantService] Tenant not found")
                raise TenantNotFoundException(f"Tenant with owner id {owner_id} not found")
            logger.info("[TenantService] Tenant found")
            return tenant
        except TenantNotFoundException:
            raise
        except Exception as e:
            logger.error(f"[TenantService] Error getting tenant by owner id: {str(e)}")
            raise ServiceException(str(e))

    async def get_tenant_by_id(
        self, tenant_id: uuid.UUID, owner_id: uuid.UUID
    ) -> Tenant:
        logger.info(f"[TenantService] Getting tenant by id: {tenant_id}")
        try:
            tenant = await self.tenant_repo.get_tenant_by_id(tenant_id)
            if not tenant:
                logger.error("[TenantService] Tenant not found")
                raise TenantNotFoundException(f"Tenant with id {tenant_id} not found")
            if tenant.owner_id != owner_id:
                logger.error("[TenantService] Tenant not found")
                raise TenantNotFoundException(f"Tenant with id {tenant_id} not found")
            logger.info("[TenantService] Tenant found")
            return tenant
        except TenantNotFoundException:
            raise
        except Exception as e:
            logger.error(f"[TenantService] Error getting tenant by id: {str(e)}")
            raise ServiceException(str(e))
