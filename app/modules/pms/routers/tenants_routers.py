from fastapi import APIRouter, Depends, status
from app.modules.auth.auth_middlewares import CurrentUser
from app.modules.pms.schemas.tenant_scheams import TenantCreateSchema, TenantResponseSchema
from app.modules.pms.services.tenant_services import TenantService
from app.modules.pms.dependencies import get_tenant_service
import uuid

router = APIRouter(prefix="/tenants", tags=["Tenants"])

@router.post("/", response_model=TenantResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant: TenantCreateSchema,
    current_user: CurrentUser,
    tenant_service: TenantService = Depends(get_tenant_service),
):
    new_tenant= await tenant_service.create_tenant(tenant.model_dump(), current_user.id)
    await tenant_service.update_user_tenant_id(current_user.id, new_tenant.id)
    return new_tenant


@router.get("/{tenant_id}", response_model=TenantResponseSchema)
async def get_tenant(
    tenant_id: uuid.UUID,
    current_user: CurrentUser,
    tenant_service: TenantService = Depends(get_tenant_service),
):
    return await tenant_service.get_tenant_by_id(tenant_id, current_user.id)
