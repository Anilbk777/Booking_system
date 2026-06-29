from app.modules.pms.services.room_services import RoomService
from app.utils.logging import LoggerFactory
from app.modules.pms.repositories.offers_repo import SpecialOfferRepository
from app.modules.pms.schemas.offers_schema import SpecialOffersCreate, SpecialOfferBase

import uuid
from app.utils.exceptions import (
    RepositoryException,
    ServiceException,
    InvalidDateException,
    PropertyNotFoundException,
    UnauthorizedException,
    OfferNotFoundException,
    OfferNameAlreadyExistsException,
)

logger = LoggerFactory.get_logger(__name__)


class SpecialOfferService:
    def __init__(
        self,
        special_offer_repo: SpecialOfferRepository,
    ):
        self.offer_repo = special_offer_repo

    async def create_property_offers(
        self, property_id: uuid.UUID, payload: SpecialOffersCreate
    ):
        logger.info(
            f"[OfferService] Processing {len(payload.offers)} offers for property: {property_id}"
        )

        try:
            # Convert Pydantic array to a flat list of dictionaries for the repository
            offers_raw_list = [offer.model_dump() for offer in payload.offers]

            # Delegate handling directly to your atomic repository transaction method
            return await self.offer_repo.create_special_offers_bulk(
                property_id=property_id, offers_data=offers_raw_list
            )

        except (RepositoryException, InvalidDateException):
            # Pass known database errors straight up to the global handler
            raise
        except Exception as e:
            logger.error(
                f"[OfferService] Error orchestrating bulk offer save: {str(e)}"
            )
            raise ServiceException(f"Failed to create special offers: {str(e)}")

    async def get_all_offers(self, property_id: uuid.UUID):
        logger.info(f"[OfferService] Fetching all offers for property: {property_id}")

        try:
            # Delegate handling directly to your atomic repository transaction method
            return await self.offer_repo.get_all_offers(property_id=property_id)

        except RepositoryException:
            # Pass known database errors straight up to the global handler
            raise
        except Exception as e:
            logger.error(f"[OfferService] Error fetching all offers: {str(e)}")
            raise ServiceException(f"Failed to fetch all offers: {str(e)}")

    async def update_offer(
        self,
        property_id: uuid.UUID,
        tenant_id: uuid.UUID,
        offer_id: uuid.UUID,
        payload: SpecialOfferBase,
        room_service: RoomService,
    ):
        logger.info(
            f"[OfferService] Processing offer for property: {property_id} and offer_id: {offer_id}"
        )
        await room_service._validate_property(property_id, tenant_id)

        try:
            # Convert Pydantic array to a flat list of dictionaries for the repository
            offers_raw = payload.model_dump()

            # Delegate handling directly to your atomic repository transaction method
            return await self.offer_repo.update_offer(
                property_id=property_id, offer_id=offer_id, offer_data=offers_raw
            )

        except (
            InvalidDateException,
            PropertyNotFoundException,
            OfferNameAlreadyExistsException,
            OfferNotFoundException,
            UnauthorizedException,
            RepositoryException,
        ):
            # Pass known database errors straight up to the global handler
            raise
        except Exception as e:
            logger.error(
                f"[OfferService] Error orchestrating bulk offer update: {str(e)}"
            )
            raise ServiceException(f"Failed to update special offers: {str(e)}")
