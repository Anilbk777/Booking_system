from sqlalchemy import and_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from app.utils.exceptions import RepositoryException, InvalidDateException
from app.utils.logging import LoggerFactory

import uuid
from app.modules.pms.models.offers_model import SpecialOffer

logger = LoggerFactory.get_logger(__name__)


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
        if "chk_offer_dates_chronology" in error_msg:
            raise InvalidDateException(
                "One of your offer dates fails the chronology constraint: start_date < end_date."
            )
        raise RepositoryException(
            "Database consistency error happened while executing bulk offer save."
        )

    except Exception as e:
        await self.db.rollback()
        logger.error(f"[OfferRepository] Unexpected rollback execution: {str(e)}")
        raise RepositoryException(f"Failed to process bulk special offers: {str(e)}")
