from fastapi import APIRouter, Depends, status
from app.modules.pms.schemas.room_schemas import (
    RoomTypeCreate,
    RoomTypeUpdate,
    RoomTypeResponse,
    RatePlanCreate,
    RatePlanUpdate,
    RatePlanResponse,
    DateOverrideCreate,
    DateOverrideUpdate,
    DateOverrideResponse,
    DiscountCodeCreate,
    DiscountCodeUpdate,
    DiscountCodeResponse,
)
from app.modules.pms.services.room_services import RoomService
from app.modules.pms.dependencies import get_room_service
from app.modules.auth.auth_middlewares import CurrentUser
import uuid

router = APIRouter(prefix="/pms/properties", tags=["Rooms"])


@router.post(
    "/{property_id}/room-types",
    response_model=RoomTypeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_room_type(
    property_id: uuid.UUID,
    room_type: RoomTypeCreate,
    user: CurrentUser,
    room_service: RoomService = Depends(get_room_service),
):
    return await room_service.create_room_type(
        room_type_data=room_type.model_dump(),
        tenant_id=user.tenant_id,
        property_id=property_id,
    )


@router.get(
    "/{property_id}/room-types",
    response_model=list[RoomTypeResponse],
    status_code=status.HTTP_200_OK,
)
async def get_room_types(
    property_id: uuid.UUID,
    user: CurrentUser,
    room_service: RoomService = Depends(get_room_service),
):
    return await room_service.get_room_types(user.tenant_id, property_id)


@router.get(
    "/{property_id}/room-types/{room_type_id}",
    response_model=RoomTypeResponse,
)
async def get_room_type(
    property_id: uuid.UUID,
    room_type_id: uuid.UUID,
    user: CurrentUser,
    room_service: RoomService = Depends(get_room_service),
):
    return await room_service.get_room_type_by_id(
        room_type_id, property_id, user.tenant_id
    )


@router.put(
    "/{property_id}/room-types/{room_type_id}",
    response_model=RoomTypeResponse,
)
async def update_room_type(
    property_id: uuid.UUID,
    room_type_id: uuid.UUID,
    room_type_data: RoomTypeUpdate,
    user: CurrentUser,
    room_service: RoomService = Depends(get_room_service),
):
    return await room_service.update_room_type(
        room_type_id,
        property_id,
        user.tenant_id,
        room_type_data.model_dump(exclude_unset=True),
    )


@router.delete("/{property_id}/room-types/{room_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room_type(
    property_id: uuid.UUID,
    room_type_id: uuid.UUID,
    user: CurrentUser,
    room_service: RoomService = Depends(get_room_service),
):
    await room_service.delete_room_type(room_type_id, property_id, user.tenant_id)
    return None


# --- Rate Plans ---

@router.post("/{property_id}/rate-plans", response_model=RatePlanResponse, status_code=status.HTTP_201_CREATED)
async def create_rate_plan(
    property_id: uuid.UUID,
    rate_plan: RatePlanCreate,
    user: CurrentUser,
    room_service: RoomService = Depends(get_room_service),
):
    return await room_service.create_rate_plan(rate_plan.model_dump(), property_id, user.tenant_id)


@router.get("/{property_id}/rate-plans", response_model=list[RatePlanResponse])
async def get_rate_plans(
    property_id: uuid.UUID,
    user: CurrentUser,
    room_service: RoomService = Depends(get_room_service),
):
    return await room_service.get_rate_plans(property_id, user.tenant_id)


@router.put("/rate-plans/{rate_plan_id}", response_model=RatePlanResponse)
async def update_rate_plan(
    rate_plan_id: uuid.UUID,
    property_id: uuid.UUID, # Pass property_id to verify ownership
    rate_plan_data: RatePlanUpdate,
    user: CurrentUser,
    room_service: RoomService = Depends(get_room_service),
):
    return await room_service.update_rate_plan(
        rate_plan_id, property_id, user.tenant_id, rate_plan_data.model_dump(exclude_unset=True)
    )


# --- Date Overrides ---

@router.post("/{property_id}/date-overrides", response_model=DateOverrideResponse, status_code=status.HTTP_201_CREATED)
async def create_date_override(
    property_id: uuid.UUID,
    override: DateOverrideCreate,
    user: CurrentUser,
    room_service: RoomService = Depends(get_room_service),
):
    return await room_service.create_date_override(override.model_dump(), property_id, user.tenant_id)


@router.get("/{property_id}/date-overrides", response_model=list[DateOverrideResponse])
async def get_date_overrides(
    property_id: uuid.UUID,
    user: CurrentUser,
    room_service: RoomService = Depends(get_room_service),
):
    return await room_service.get_date_overrides(property_id, user.tenant_id)


@router.put("/date-overrides/{override_id}", response_model=DateOverrideResponse)
async def update_date_override(
    override_id: uuid.UUID,
    property_id: uuid.UUID,
    override_data: DateOverrideUpdate,
    user: CurrentUser,
    room_service: RoomService = Depends(get_room_service),
):
    await room_service._validate_property(property_id, user.tenant_id)
    return await room_service.room_repo.update_date_override(override_id, override_data.model_dump(exclude_unset=True))


@router.delete("/date-overrides/{override_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_date_override(
    override_id: uuid.UUID,
    property_id: uuid.UUID,
    user: CurrentUser,
    room_service: RoomService = Depends(get_room_service),
):
    await room_service._validate_property(property_id, user.tenant_id)
    await room_service.room_repo.delete_date_override(override_id)
    return None


# --- Discount Codes ---

@router.post("/{property_id}/discounts", response_model=DiscountCodeResponse, status_code=status.HTTP_201_CREATED)
async def create_discount_code(
    property_id: uuid.UUID,
    discount: DiscountCodeCreate,
    user: CurrentUser,
    room_service: RoomService = Depends(get_room_service),
):
    return await room_service.create_discount_code(discount.model_dump(), property_id, user.tenant_id)


@router.get("/{property_id}/discounts", response_model=list[DiscountCodeResponse])
async def get_discount_codes(
    property_id: uuid.UUID,
    user: CurrentUser,
    room_service: RoomService = Depends(get_room_service),
):
    return await room_service.get_discount_codes(property_id, user.tenant_id)


@router.put("/discounts/{discount_id}", response_model=DiscountCodeResponse)
async def update_discount_code(
    discount_id: uuid.UUID,
    property_id: uuid.UUID,
    discount_data: DiscountCodeUpdate,
    user: CurrentUser,
    room_service: RoomService = Depends(get_room_service),
):
    await room_service._validate_property(property_id, user.tenant_id)
    return await room_service.room_repo.update_discount_code(discount_id, discount_data.model_dump(exclude_unset=True))


@router.delete("/discounts/{discount_id}", status_code=status.HTTP_24_NO_CONTENT)
async def delete_discount_code(
    discount_id: uuid.UUID,
    property_id: uuid.UUID,
    user: CurrentUser,
    room_service: RoomService = Depends(get_room_service),
):
    await room_service._validate_property(property_id, user.tenant_id)
    await room_service.room_repo.delete_discount_code(discount_id)
    return None
