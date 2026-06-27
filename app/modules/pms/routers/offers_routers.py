import uuid
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from app.modules.auth.auth_middlewares import CurrentUser
from app.modules.pms.dependencies import get_special_offer_service
from app.modules.pms.schemas.offers_schema import (
    SpecialOffersCreate,
    SpecialOfferResponse,
)
from app.utils.schemas import StandardResponse
from app.modules.pms.services.offers_services import SpecialOfferService

router = APIRouter(prefix="/pms", tags=["Special Offers"])


@router.post(
    "/{property_id}/special-offers",
    response_model=StandardResponse[List[SpecialOfferResponse]],
    status_code=status.HTTP_201_CREATED,
)
async def bulk_create_special_offers(
    property_id: uuid.UUID,
    payload: SpecialOffersCreate,
    user: CurrentUser,
    offer_service: SpecialOfferService = Depends(get_special_offer_service),
):
    # Enforce basic security access restrictions
    if user.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not authorized to create special offers. You must belong to a tenant.",
        )

    # Execute transactional routine
    saved_models = await offer_service.create_property_offers(
        property_id=property_id, payload=payload
    )

    # Map raw SQLAlchemy model entries to Pydantic Response schemas
    formatted_offers = [
        SpecialOfferResponse.model_validate(model_row) for model_row in saved_models
    ]

    # Return everything packed neatly inside your standardized API envelope configuration
    return {
        "success": True,
        "data": formatted_offers
    }

@router.get(
    "/{property_id}/special-offers",
    response_model=StandardResponse[List[SpecialOfferResponse]],
    status_code=status.HTTP_200_OK,
)
async def get_property_special_offers(
    property_id: uuid.UUID,
    user: CurrentUser,
    offer_service: SpecialOfferService = Depends(get_special_offer_service),
):
    # Enforce basic security access restrictions
    if user.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not authorized to get special offers. You must belong to a tenant.",
        )

    # Execute transactional routine
    saved_models = await offer_service.get_all_offers(
        property_id=property_id
    )
    print(f"[OfferRouter] Fetched {len(saved_models)} offers for property: {property_id}")

    # Map raw SQLAlchemy model entries to Pydantic Response schemas
    formatted_offers = [
        SpecialOfferResponse.model_validate(model_row) for model_row in saved_models
    ]

    # Return everything packed neatly inside your standardized API envelope configuration
    return {
        "success": True,
        "data": formatted_offers
    }