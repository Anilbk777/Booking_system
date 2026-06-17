from app.modules.pms.models.tenants_model import Tenant
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.utils.exceptions import RepositoryException
from app.utils.logging import LoggerFactory
import uuid

logger = LoggerFactory.get_logger(__name__)


class TenantRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_tenant(self, tenant: dict) -> Tenant:
        logger.info(f"[TenantsRepoitory] Creating tenant: {tenant}")
        try:
            new_tenant = Tenant(**tenant)
            self.db.add(new_tenant)
            await self.db.commit()
            await self.db.refresh(new_tenant)
            logger.info("[TenantsRepoitory] Tenant created successfully")
            return new_tenant
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[TenantsRepoitory] Error creating tenant: {str(e)}")
            raise RepositoryException(str(e))

    async def get_tenant_by_id(self, tenant_id: uuid.UUID) -> Tenant | None:
        logger.info(f"[TenantsRepoitory] Getting tenant by id: {tenant_id}")
        try:
            result = await self.db.execute(select(Tenant).where(Tenant.id == tenant_id))
            tenant = result.scalar_one_or_none()
            if tenant:
                logger.info("[TenantsRepoitory] Tenant found")
            else:
                logger.error("[TenantsRepoitory] Tenant not found")
            return tenant
        except Exception as e:
            logger.error(f"[TenantsRepoitory] Error getting tenant by id: {str(e)}")
            raise RepositoryException(str(e))

    async def get_tenant_by_owner_id(self, owner_id:uuid.UUID) -> Tenant | None:
        logger.info(f"[TenantsRepoitory] Getting tenant by id: {owner_id}")
        try:
            result = await self.db.execute(select(Tenant).where(Tenant.owner_id == owner_id))
            tenant = result.scalar_one_or_none()
            if tenant:
                logger.info("[TenantsRepoitory] Tenant found")
            else:
                logger.error("[TenantsRepoitory] Tenant not found")
            return tenant
        except Exception as e:
            logger.error(f"[TenantsRepoitory] Error getting tenant by id: {str(e)}")
            raise RepositoryException(str(e))


    async def get_tenant_by_name(
        self, tenant_name: str, owner_id: uuid.UUID
    ) -> Tenant | None:
        logger.info(f"[TenantsRepoitory] Getting tenant by name: {tenant_name}")
        try:
            result = await self.db.execute(
                select(Tenant).where(
                    func.lower(Tenant.name) == tenant_name.lower(),
                    Tenant.owner_id == owner_id,
                )
            )
            tenant = result.scalar_one_or_none()
            if tenant:
                logger.info("[TenantsRepoitory] Tenant found")
            else:
                logger.error("[TenantsRepoitory] Tenant not found")
            return tenant
        except Exception as e:
            logger.error(f"[TenantsRepoitory] Error getting tenant by name: {str(e)}")
            raise RepositoryException(str(e))
