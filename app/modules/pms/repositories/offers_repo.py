import uuid

from sqlalchemy import and_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.modules.pms.models.offers_model import SpecialOffer
from app.utils.exceptions import (
    InvalidDateException,
    RepositoryException,
    OfferNotFoundException,
    OfferNameAlreadyExistsException,
)
from app.utils.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class SpecialOfferRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_special_offers_bulk(
        self, property_id: uuid.UUID, offers_data: list[dict]
    ) -> list[SpecialOffer]:
        """
        Inserts multiple special offers for a property inside a single transaction chain.
        """
        logger.info(
            f"[OfferRepository] Staging {len(offers_data)} special offers for property {property_id}"
        )
        saved_offers: list[SpecialOffer] = []

        try:
            for offer_dict in offers_data:
                clean_title = offer_dict["title"].strip()

                # 1. Prevent duplicate titles for this property scope
                stmt = select(SpecialOffer).where(
                    and_(
                        func.lower(SpecialOffer.title) == clean_title.lower(),
                        SpecialOffer.property_id == property_id,
                    )
                )
                result = await self.db.execute(stmt)
                if result.scalar_one_or_none():
                    raise RepositoryException(
                        f"An offer with the title '{clean_title}' already exists for this property."
                    )

                # 2. Instantiate individual offer instance
                new_offer = SpecialOffer(
                    property_id=property_id,
                    title=clean_title,
                    description=offer_dict.get("description"),
                    discount_percentage=offer_dict.get("discount_percentage", 0.00),
                    start_date=offer_dict["start_date"],
                    end_date=offer_dict["end_date"],
                    is_active=offer_dict.get("is_active", False),
                    is_custom=True,  # Explicitly marked as user-created custom entries
                )
                self.db.add(new_offer)
                saved_offers.append(new_offer)

            # 3. Commit the entire batch group transaction atomically
            await self.db.flush()
            await self.db.commit()

            logger.info(
                f"[OfferRepository] Successfully committed {len(saved_offers)} offers together."
            )
            return saved_offers

        except IntegrityError as e:
            await self.db.rollback()
            error_msg = str(e.orig) if hasattr(e, "orig") else str(e)
            logger.error(
                f"[OfferRepository] Batch unique index constraint failure: {error_msg}"
            )
            if "uq_property_special_offers_title" in error_msg:
                raise InvalidDateException(
                    "One of your offer dates fails the chronology constraint: start_date < end_date."
                )
            raise RepositoryException(
                "Database consistency error happened while executing bulk offer save."
            )

        except Exception as e:
            await self.db.rollback()
            logger.error(f"[OfferRepository] Unexpected rollback execution: {str(e)}")
            raise RepositoryException(
                f"Failed to process bulk special offers: {str(e)}"
            )

    async def get_all_offers(self, property_id: uuid.UUID):
        logger.info(f"[OfferRepository] Getting all offers for property: {property_id}")
        try:
            stmt = select(SpecialOffer).where(SpecialOffer.property_id == property_id)
            result = await self.db.execute(stmt)
            offers = result.scalars().all()
            return offers
        except Exception as e:
            logger.error(f"[OfferRepository] Error getting all offers: {str(e)}")
            raise RepositoryException(f"Failed to get all offers: {str(e)}")

    async def get_offer_by_id(self, offer_id: uuid.UUID, property_id: uuid.UUID):
        logger.info(
            f"[OfferRepository] Getting offer with id {offer_id} for property {property_id}"
        )
        try:
            stmt = select(SpecialOffer).where(
                SpecialOffer.id == offer_id, SpecialOffer.property_id == property_id
            )
            result = await self.db.execute(stmt)
            offer = result.scalar_one_or_none()
            return offer
        except Exception as e:
            logger.error(f"[OfferRepository] Error getting offer by id: {str(e)}")
            raise RepositoryException(
                "Failed to get offer", f"Failed to get offer by id: {str(e)}"
            )

    async def update_offer(
        self, offer_id: uuid.UUID, property_id: uuid.UUID, offer_data: dict
    ) -> SpecialOffer:
        logger.info(f"[OfferRepository] Initiating graph update for offer: {offer_id}")

        try:
            offer_obj = await self.get_offer_by_id(offer_id, property_id)

            if not offer_obj:
                logger.error(
                    f"[OfferRepository] Offer {offer_id} not found under property context {property_id}."
                )
                raise OfferNotFoundException(
                    "The requested special offer could not be found.",
                    f"Offer with id {offer_id} not found for property {property_id}.",
                )

            for key in [
                "title",
                "description",
                "discount_percentage",
                "start_date",
                "end_date",
                "is_active",
                "is_custom",
            ]:
                if key in offer_data:
                    value = offer_data[key]
                    if isinstance(value, str):
                        value = value.strip()

                    setattr(offer_obj, key, value)

            await self.db.flush()
            await self.db.commit()
            logger.info(
                f"[OfferRepository] Offer {offer_id} transaction fully committed."
            )
            await self.db.refresh(offer_obj)

            return offer_obj

        except OfferNotFoundException:
            await self.db.rollback()
            raise

        except IntegrityError as e:
            await self.db.rollback()
            error_msg = str(e.orig) if hasattr(e, "orig") else str(e)
            logger.error(
                f"[OfferRepository] Unique constraint conflict detected during offer update: {error_msg}"
            )

            # Catch naming uniqueness collisions explicitly
            if "uq_offers_property_title" in error_msg or "unique" in error_msg.lower():
                raise OfferNameAlreadyExistsException(
                    "An offer with this title already exists for your property footprint."
                )
            raise RepositoryException(
                "Database consistency constraint violated.",
                f"Failed to update offer constraints: {error_msg}",
            )

        except Exception as e:
            await self.db.rollback()
            logger.critical(
                f"[OfferRepository] Unexpected update pipeline exception collapse: {str(e)}"
            )
            raise RepositoryException(
                "Failed to complete offer data updates.",
                f"Failed to update offer runtime states: {str(e)}",
            )
