import uuid

from fastapi import APIRouter, Depends, HTTPException,  status

from app.modules.auth.auth_middlewares import CurrentUser
from app.modules.pms.dependencies import get_property_service
from app.modules.pms.schemas.properties_schemas import (
    AmenityResponse,
    PropertyCreate,
    PropertyHotelDetailResponse,
    PropertyPhotoResponse,
    PropertyResponse,
    PropertyDetailResponse,
    DefaultAmenityResponse,
)
from app.modules.pms.services.properties_scervices import PropertyService
from app.utils.schemas import StandardResponse

router = APIRouter(prefix="/pms/properties", tags=["Property Management System"])


@router.post(
    "/",
    response_model=StandardResponse[PropertyResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_property(
    payload: PropertyCreate,
    current_user: CurrentUser,
    property_service: PropertyService = Depends(get_property_service),
):
    if current_user.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not authorized to create a property. You should have a tenant.",
        )
    response = await property_service.create_property(
        payload=payload,
        tenant_id=current_user.tenant_id,
    )
    property_data = PropertyResponse(
        id=response["property"].id,
        tenant_id=response["property"].tenant_id,
        is_active=response["property"].is_active,
        name=response["property"].name,
        type=response["property"].type,
        description=response["property"].description,
        country=response["property"].country,
        state=response["property"].state,
        city=response["property"].city,
        zip_code=response["property"].zip_code,
        address=response["property"].address,
        latitude=response["property"].latitude,
        longitude=response["property"].longitude,
        created_at=response["property"].created_at,
        updated_at=response["property"].updated_at,
        hotel_detail=PropertyHotelDetailResponse.model_validate(
            response["hotel_detail"]
        ),
        photos=[
            PropertyPhotoResponse.model_validate(photo)
            for photo in response["photo_urls"]
        ],
        amenities=[
            AmenityResponse.model_validate(amenity) for amenity in response["amenities"]
        ],
    )
    return {"success": True, "data": property_data}


@router.get(
    "/",
    response_model=StandardResponse[list[PropertyDetailResponse]],
    status_code=status.HTTP_200_OK,
)
async def get_all_properties(
    current_user: CurrentUser,
    property_service: PropertyService = Depends(get_property_service),
):
    if current_user.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not authorized to get a property.",
        )

    response = await property_service.get_all_properties(current_user.tenant_id)
    property_list = []
    for property in response:
        property_data = PropertyDetailResponse(
            id=property.id,
            tenant_id=property.tenant_id,
            is_active=property.is_active,
            name=property.name,
            type=property.type,
            description=property.description,
            country=property.country,
            state=property.state,
            city=property.city,
            zip_code=property.zip_code,
            address=property.address,
            latitude=property.latitude,
            longitude=property.longitude,
            created_at=property.created_at,
            updated_at=property.updated_at,
        )
        property_list.append(property_data)

    return {"success": True, "data": property_list}


@router.get(
    "/amenities",
    response_model=StandardResponse[list[DefaultAmenityResponse]],
    status_code=status.HTTP_200_OK,
)
async def get_all_amenities(
    current_user: CurrentUser,
    property_service: PropertyService = Depends(get_property_service),
):
    if current_user.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not authorized to get a amenities.",
        )
    response = await property_service.get_all_amenities()
    return {"success": True, "data": response}


@router.get(
    "/{property_id}",
    response_model=StandardResponse[PropertyResponse],
    status_code=status.HTTP_200_OK,
)
async def get_property_by_id(
    property_id: uuid.UUID,
    current_user: CurrentUser,
    property_service: PropertyService = Depends(get_property_service),
):
    if current_user.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not authorized to get a property.",
        )

    response = await property_service.get_property_details_by_id(
        property_id, current_user.tenant_id
    )
    property_data = PropertyResponse(
        id=response.id,
        tenant_id=response.tenant_id,
        is_active=response.is_active,
        name=response.name,
        type=response.type,
        description=response.description,
        country=response.country,
        state=response.state,
        city=response.city,
        zip_code=response.zip_code,
        address=response.address,
        latitude=response.latitude,
        longitude=response.longitude,
        created_at=response.created_at,
        updated_at=response.updated_at,
        hotel_detail=PropertyHotelDetailResponse.model_validate(response.hotel_detail),
        photos=[
            PropertyPhotoResponse(
                id=photo.id,
                property_id=photo.property_id,
                photo_url=photo.photo_url,
                created_at=photo.created_at,
                updated_at=photo.updated_at,
            )
            for photo in response.photos
        ],
        amenities=[
            AmenityResponse(
                id=amenity.id,
                name=amenity.name,
                is_default=amenity.is_default,
                created_at=amenity.created_at,
                updated_at=amenity.updated_at,
            )
            for amenity in response.owned_custom_amenities
        ],
    )
    return {"success": True, "data": property_data}


@router.patch(
    "/{property_id}",
    response_model=StandardResponse[PropertyResponse],
    status_code=status.HTTP_200_OK,
)
async def update_property(
    property_id: uuid.UUID,
    current_user: CurrentUser,
    payload: PropertyCreate,
    property_service: PropertyService = Depends(get_property_service),
):
    if current_user.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not authorized to update a property.",
        )

    response = await property_service.update_property(
        property_id, current_user.tenant_id, payload
    )
    property_data = PropertyResponse(
        id=response["property"].id,
        tenant_id=response["property"].tenant_id,
        is_active=response["property"].is_active,
        name=response["property"].name,
        type=response["property"].type,
        description=response["property"].description,
        country=response["property"].country,
        state=response["property"].state,
        city=response["property"].city,
        zip_code=response["property"].zip_code,
        address=response["property"].address,
        latitude=response["property"].latitude,
        longitude=response["property"].longitude,
        created_at=response["property"].created_at,
        updated_at=response["property"].updated_at,
        hotel_detail=PropertyHotelDetailResponse.model_validate(
            response["hotel_detail"]
        ),
        photos=[
            PropertyPhotoResponse.model_validate(photo)
            for photo in response["photo_urls"]
        ],
        amenities=[
            AmenityResponse.model_validate(amenity) for amenity in response["amenities"]
        ],
    )
    return {"success": True, "data": property_data}


@router.post(
    "/{property_id}/activation",
    status_code=status.HTTP_200_OK,
)
async def update_property_activation(
    property_id: uuid.UUID,
    current_user: CurrentUser,
    property_service: PropertyService = Depends(get_property_service),
):
    if current_user.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not authorized to update a property.",
        )

    await property_service.update_property_activation(
        property_id, current_user.tenant_id
    )

    return {"success": True, "data": "Property is activated"}


@router.delete("/{property_id}", status_code=status.HTTP_200_OK)
async def delete_property(
    property_id: uuid.UUID,
    current_user: CurrentUser,
    property_service: PropertyService = Depends(get_property_service),
):
    if current_user.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not authorized to delete a property.",
        )

    await property_service.delete_property(property_id, current_user.tenant_id)

    return {"success": True, "data": "Property is deleted"}
