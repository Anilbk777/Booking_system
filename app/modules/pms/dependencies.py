from app.modules.pms.services.tenant_services import TenantService
from app.modules.pms.repositories.tenants_repo import TenantRepository

from app.modules.pms.services.properties_scervices import PropertyService
from app.modules.pms.repositories.properties_repo import PropertyRepository
from app.config.database_config import get_db
from fastapi import Depends


async def get_tenant_service(db=Depends(get_db)) -> TenantService:
    return TenantService(tenant_repo=TenantRepository(db=db))


async def get_property_service(db=Depends(get_db)) -> PropertyService:
    return PropertyService(
        property_repo=PropertyRepository(db=db), tenant_service=get_tenant_service(db)
    )
