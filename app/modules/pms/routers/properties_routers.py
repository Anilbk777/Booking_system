from fastapi import APIRouter, Depends, status
from app.modules.pms.schemas.properties_schemas import PropertyCreate, PropertyResponse
from app.modules.pms.services.properties_scervices import PropertyService
from app.modules.pms.dependencies import get_property_service
from app.modules.auth.auth_middlewares import CurrentUser
import uuid

router = APIRouter(prefix="/pms", tags=["Property Management System"])


@router.post(
    "/properties", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED
)
async def create_property(
    property: PropertyCreate,
    current_user: CurrentUser,
    property_service: PropertyService = Depends(get_property_service),
):
    return await property_service.create_property(
        property.model_dump(), current_user.tenant_id
    )


@router.get(
    "/properties/{property_id}",
    response_model=PropertyResponse,
    status_code=status.HTTP_200_OK,
)
async def get_property(
    property_id: uuid.UUID,
    current_user: CurrentUser,
    property_service: PropertyService = Depends(get_property_service),
):
    return await property_service.get_property_by_id(
        property_id, current_user.tenant_id
    )
