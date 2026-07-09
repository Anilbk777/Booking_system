from app.modules.pms.services.image_services import ImageService
import uuid
from datetime import date
from collections import defaultdict
from sqlalchemy import and_, delete, func, select, or_, not_
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.modules.pms.models.properties_model import (
    Amenity,
    Property,
    PropertyAmenity,
    PropertyHotelDetail,
    PropertyPhoto,
)
from app.modules.booking.models.booking_model import (
    BookingRoom,
    Booking,
    MasterBookingStatus,
)
from app.modules.pms.models.rooms_model import Rooms, RoomStatus
from app.utils.exceptions import (
    DefaultAmenityNotExistsException,
    RepositoryException,
    PropertyNotFoundException,
    ImageStorageException,
    InvalidImageException,
)
from app.utils.logging import LoggerFactory
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from app.modules.pms.services.search_engine import (
    HeterogeneousGuestAllocationEngine,
    calculate_stay_total,
    RoomCapacity,
)

logger = LoggerFactory.get_logger(__name__)


@dataclass(frozen=True)
class _CandidateRoom:
    """Raw per-row data pulled from the DB, before allocation checking."""

    property_id: uuid.UUID
    property_name: str
    address: str
    city: str
    state: str
    country: str
    photo_url: Optional[str]
    room_type_id: uuid.UUID
    room_id: uuid.UUID
    max_adults: int
    max_children: int
    base_rate: Optional[Decimal]


class PropertyRepository:
    def __init__(self, db: AsyncSession, image_service: ImageService):
        self.db = db
        self.image_service = image_service

    async def get_property_by_id(
        self, property_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> Property | None:
        logger.info(f"[PropertyRepository] Getting property by id: {property_id}")
        try:
            result = await self.db.execute(
                select(Property)
                .where(
                    Property.id == property_id,
                    Property.tenant_id == tenant_id,
                )
                .options(joinedload(Property.hotel_detail))
            )
            property = result.scalar_one_or_none()
            return property
        except Exception as e:
            logger.error(f"[PropertyRepository] Error getting property by id: {str(e)}")
            raise RepositoryException(str(e))

    async def get_property_by_name(
        self, property_name: str, tenant_id: uuid.UUID
    ) -> Property | None:
        logger.info(f"[PropertyRepository] Getting property by name: {property_name}")
        try:
            result = await self.db.execute(
                select(Property).where(
                    func.lower(Property.name) == property_name.lower(),
                    Property.tenant_id == tenant_id,
                )
            )
            property = result.scalars().one_or_none()
            return property
        except Exception as e:
            logger.error(
                f"[PropertyRepository] Error getting property by name: {str(e)}"
            )
            raise RepositoryException(str(e))

    # async def get_existing_amenities(self) -> list[Amenity]:
    #     logger.info("[PropertyRepository] Fetching existing amenities")
    #     try:
    #         result = await self.db.execute(select(Amenity).where(Amenity.is_default))
    #         return list(result.scalars().all())

    #     except Exception as e:
    #         logger.error(
    #             f"[PropertyRepository] Error fetching existing amenities: {str(e)}"
    #         )
    #         raise RepositoryException(str(e))

    # async def create_property_transactional(
    #     self,
    #     tenant_id: uuid.UUID,
    #     property_data: dict,
    #     hotel_detail_data: dict,
    #     amenities_input: list,
    #     photo_urls: list,
    # ) -> dict:
    #     """
    #     Creates a property and all its related child sub-graphs atomically.
    #     Ensures complete success or rolls back the entire database change state.
    #     """
    #     logger.info("[PropertyRepository] Initiating atomic property graph insertion")

    #     try:
    #         # 1. Instantiate and stage the root Property model
    #         new_property = Property(
    #             tenant_id=tenant_id,
    #             **property_data,
    #         )
    #         self.db.add(new_property)

    #         # 2. Flush to force PostgreSQL to safely generate new_property.id
    #         await self.db.flush()

    #         final_photo_urls: list[str] = []
    #         if photo_urls:
    #             public_ids = [
    #                 self.image_service.extract_public_id_from_url(url)
    #                 for url in photo_urls
    #             ]
    #             fake_property_id = self.image_service.extract_fake_id_from_public_id(
    #                 public_ids[0], "properties"
    #             )

    #             for old_public_id in public_ids:
    #                 new_public_id = old_public_id.replace(
    #                     fake_property_id, str(new_property.id)
    #                 )
    #                 final_public_id = new_public_id.replace("temp/", "")
    #                 try:
    #                     renamed = await self.image_service.provider.rename_image(
    #                         old_public_id, final_public_id
    #                     )
    #                     final_photo_urls.append(renamed["url"])
    #                 except Exception as e:
    #                     logger.error(
    #                         f"[PropertyRepository] Failed to rename image {old_public_id}: {str(e)}"
    #                     )
    #                     raise ImageStorageException(
    #                         "Failed to finalize property images",
    #                         f"Failed to finalize property images{str(e)}",
    #                     )

    #         # 3. Instantiate and stage the Hotel Details configuration
    #         hotel_detail = PropertyHotelDetail(
    #             property_id=new_property.id,
    #             **hotel_detail_data,
    #         )
    #         self.db.add(hotel_detail)

    #         # 4. Resolve and stage Selections Amenities
    #         final_amenities: list[Amenity] = []
    #         for amenity_in in amenities_input:
    #             if isinstance(amenity_in, dict):
    #                 name_val = amenity_in.get("name", "")
    #                 is_default_val = amenity_in.get("is_default", False)
    #             else:
    #                 name_val = getattr(amenity_in, "name", "")
    #                 is_default_val = getattr(amenity_in, "is_default", False)

    #             clean_name = name_val.strip() if name_val else ""
    #             if not clean_name:
    #                 continue

    #             matched_amenity = None

    #             if is_default_val:
    #                 stmt = select(Amenity).where(
    #                     and_(
    #                         func.lower(Amenity.name) == clean_name.lower(),
    #                         Amenity.is_default,
    #                         Amenity.property_id.is_(None),
    #                     )
    #                 )
    #                 result = await self.db.execute(stmt)
    #                 matched_amenity = result.scalar_one_or_none()
    #                 if not matched_amenity:
    #                     logger.error(
    #                         f"[PropertyRepository] Default amenity '{clean_name}' does not exist in system."
    #                     )
    #                     raise DefaultAmenityNotExistsException(
    #                         f"The default amenity '{clean_name}' is not supported by the platform. "
    #                         f"Please use custom amenities for unique options."
    #                     )
    #             else:
    #                 stmt = select(Amenity).where(
    #                     and_(
    #                         func.lower(Amenity.name) == clean_name.lower(),
    #                         Amenity.property_id == new_property.id,
    #                     )
    #                 )
    #                 result = await self.db.execute(stmt)
    #                 matched_amenity = result.scalar_one_or_none()

    #                 if not matched_amenity:
    #                     matched_amenity = Amenity(
    #                         name=clean_name,
    #                         is_default=False,
    #                         property_id=new_property.id,
    #                     )
    #                     self.db.add(matched_amenity)
    #                     await self.db.flush()

    #             if matched_amenity:
    #                 final_amenities.append(matched_amenity)

    #                 # Verify link row uniqueness before staging
    #                 link_stmt = select(PropertyAmenity).where(
    #                     and_(
    #                         PropertyAmenity.property_id == new_property.id,
    #                         PropertyAmenity.amenity_id == matched_amenity.id,
    #                     )
    #                 )
    #                 link_result = await self.db.execute(link_stmt)
    #                 if not link_result.scalar_one_or_none():
    #                     new_link = PropertyAmenity(
    #                         property_id=new_property.id, amenity_id=matched_amenity.id
    #                     )
    #                     self.db.add(new_link)

    #         # 5. Process and stage Property Photos
    #         final_photos: list[PropertyPhoto] = []
    #         for url in final_photo_urls:
    #             if isinstance(url, str) and url.strip():
    #                 new_photo = PropertyPhoto(
    #                     property_id=new_property.id,
    #                     photo_url=url.strip(),
    #                 )
    #                 self.db.add(new_photo)
    #                 final_photos.append(new_photo)

    #         # 6. Flush all staged items to validate constraints before committing
    #         await self.db.flush()

    #         # 7. Commit everything together safely
    #         await self.db.commit()
    #         logger.info(
    #             f"[PropertyRepository] Property transactional chain committed: {new_property.id}"
    #         )

    #         return {
    #             "property": new_property,
    #             "hotel_detail": hotel_detail,
    #             "amenities": final_amenities,
    #             "photo_urls": final_photos,
    #         }

    #     except (InvalidImageException, ImageStorageException):
    #         await self.db.rollback()
    #         raise

    #     except DefaultAmenityNotExistsException as e:
    #         await self.db.rollback()
    #         logger.error(
    #             f"[PropertyRepository] Default amenity validation failed: {str(e)}"
    #         )
    #         raise
    #     except IntegrityError as e:
    #         await self.db.rollback()
    #         error_msg = str(e.orig) if hasattr(e, "orig") else str(e)
    #         logger.error(
    #             f"[PropertyRepository] Transaction integrity failure: {error_msg}"
    #         )
    #         raise RepositoryException(f"Database consistency failure: {error_msg}")

    #     except DBAPIError as e:
    #         await self.db.rollback()
    #         logger.error(
    #             f"[PropertyRepository] Operational db transaction failure: {str(e)}"
    #         )
    #         raise RepositoryException(
    #             "Internal operational database breakdown occurred."
    #         )

    #     except Exception as e:
    #         await self.db.rollback()
    #         logger.error(
    #             f"[PropertyRepository] Unexpected transactional crash: {str(e)}"
    #         )
    #         raise RepositoryException(f"Unexpected error occurred: {str(e)}")

    # async def get_hotel_detail_by_property_id(
    #     self, property_id: uuid.UUID, hotel_id: uuid.UUID
    # ) -> PropertyHotelDetail | None:
    #     logger.info(
    #         f"[PropertyRepository] Fetching hotel detail for property {property_id} and hotel {hotel_id}"
    #     )
    #     try:
    #         result = await self.db.execute(
    #             select(PropertyHotelDetail).where(
    #                 PropertyHotelDetail.property_id == property_id,
    #                 PropertyHotelDetail.id == hotel_id,
    #             )
    #         )
    #         return result.scalar_one_or_none()
    #     except Exception as e:
    #         logger.error(
    #             f"[PropertyRepository] Error fetching hotel detail for property {property_id} and hotel {hotel_id}: {str(e)}"
    #         )
    #         raise RepositoryException(f"Error fetching hotel detail: {str(e)}")

    # async def get_all_properties(self, tenant_id: uuid.UUID):
    #     logger.info(
    #         f"[PropertyRepository] Fetching all properties for tenant: {tenant_id}"
    #     )
    #     try:
    #         stmt = select(Property).where(Property.tenant_id == tenant_id)
    #         result = await self.db.execute(stmt)
    #         return result.scalars().all()
    #     except Exception as e:
    #         logger.error(
    #             f"[PropertyRepository] Error fetching all properties for tenant: {tenant_id}: {str(e)}"
    #         )
    #         raise RepositoryException(f"Error fetching all properties: {str(e)}")

    # async def get_property_details_by_id(
    #     self, property_id: uuid.UUID, tenant_id: uuid.UUID
    # ):
    #     try:
    #         result = await self.db.execute(
    #             select(Property)
    #             .where(
    #                 Property.id == property_id,
    #                 Property.tenant_id == tenant_id,
    #             )
    #             .options(joinedload(Property.hotel_detail))
    #             .options(
    #                 selectinload(Property.property_amenities).selectinload(
    #                     PropertyAmenity.amenity
    #                 )
    #             )
    #             .options(selectinload(Property.photos))
    #             .options(selectinload(Property.owned_custom_amenities))
    #         )
    #         property = result.scalar_one_or_none()
    #         return property
    #     except Exception as e:
    #         logger.error(
    #             f"[PropertyRepository] Error fetching property details for property {property_id} and tenant {tenant_id}: {str(e)}"
    #         )
    #         raise RepositoryException(
    #             internal_detail=f"Error fetching property details: {str(e)}"
    #         )

    # async def update_property(
    #     self,
    #     property_id: uuid.UUID,
    #     tenant_id: uuid.UUID,
    #     property_data: dict,
    #     hotel_detail_data: dict | None,
    #     amenities_input: list | None,
    #     photo_urls: list | None,
    # ) -> dict:
    #     """
    #     Updates a property graph atomically in an all-or-nothing style.
    #     Returns the fully updated property, hotel detail, amenities list, and photo list.
    #     """
    #     logger.info(
    #         f"[PropertyRepository] Initiating full-graph update for property: {property_id}"
    #     )

    #     try:
    #         # 1. Fetch root property profile to secure tenant isolation boundaries
    #         stmt = select(Property).where(
    #             and_(Property.id == property_id, Property.tenant_id == tenant_id)
    #         )
    #         result = await self.db.execute(stmt)
    #         existing_property = result.scalar_one_or_none()

    #         if not existing_property:
    #             logger.error(
    #                 f"[PropertyRepository] Property {property_id} not found or unauthorized."
    #             )
    #             raise PropertyNotFoundException("Property not found or access denied.")

    #         # 2. Overwrite core fields on the root Property model directly
    #         for key, val in property_data.items():
    #             setattr(existing_property, key, val)

    #         # 3. Overwrite Hotel Details sub-record fields
    #         active_detail = None
    #         if hotel_detail_data is not None:
    #             detail_stmt = select(PropertyHotelDetail).where(
    #                 PropertyHotelDetail.property_id == property_id
    #             )
    #             detail_res = await self.db.execute(detail_stmt)
    #             existing_detail = detail_res.scalar_one_or_none()

    #             if existing_detail:
    #                 for key, val in hotel_detail_data.items():
    #                     setattr(existing_detail, key, val)
    #                 active_detail = existing_detail
    #             else:
    #                 # Fallback if no detail record exists yet
    #                 active_detail = PropertyHotelDetail(
    #                     property_id=property_id, **hotel_detail_data
    #                 )
    #                 self.db.add(active_detail)

    #         # 4. Sync Amenities (Wipe old mapping links and rebuild from the frontend list)
    #         updated_final_amenities = []
    #         if amenities_input is not None:
    #             await self.db.execute(
    #                 delete(PropertyAmenity).where(
    #                     PropertyAmenity.property_id == property_id
    #                 )
    #             )

    #             for amenity_in in amenities_input:
    #                 if isinstance(amenity_in, dict):
    #                     name_val = amenity_in.get("name", "")
    #                     is_default_val = amenity_in.get("is_default", False)
    #                 else:
    #                     name_val = getattr(amenity_in, "name", "")
    #                     is_default_val = getattr(amenity_in, "is_default", False)

    #                 clean_name = name_val.strip() if name_val else ""
    #                 if not clean_name:
    #                     continue

    #                 matched_amenity = None
    #                 if is_default_val:
    #                     # Look up global default amenity entries
    #                     am_stmt = select(Amenity).where(
    #                         and_(
    #                             func.lower(Amenity.name) == clean_name.lower(),
    #                             Amenity.is_default,
    #                             Amenity.property_id.is_(None),
    #                         )
    #                     )
    #                     am_res = await self.db.execute(am_stmt)
    #                     matched_amenity = am_res.scalar_one_or_none()
    #                     if not matched_amenity:
    #                         logger.error(
    #                             f"[PropertyRepository] Default amenity '{clean_name}' does not exist."
    #                         )
    #                         raise DefaultAmenityNotExistsException(
    #                             f"The default amenity '{clean_name}' is not supported by the platform."
    #                         )
    #                 else:
    #                     # Look up or create a custom amenity for this specific property
    #                     am_stmt = select(Amenity).where(
    #                         and_(
    #                             func.lower(Amenity.name) == clean_name.lower(),
    #                             Amenity.property_id == property_id,
    #                         )
    #                     )
    #                     am_res = await self.db.execute(am_stmt)
    #                     matched_amenity = am_res.scalar_one_or_none()

    #                     if not matched_amenity:
    #                         matched_amenity = Amenity(
    #                             name=clean_name,
    #                             is_default=False,
    #                             property_id=property_id,
    #                         )
    #                         self.db.add(matched_amenity)
    #                         await (
    #                             self.db.flush()
    #                         )  # Generates primary key ID immediately

    #                 if matched_amenity:
    #                     updated_final_amenities.append(matched_amenity)
    #                     # Create the modern bridge mapping link
    #                     new_link = PropertyAmenity(
    #                         property_id=property_id, amenity_id=matched_amenity.id
    #                     )
    #                     self.db.add(new_link)

    #         # 5. Sync Photos (Clear out old URLs and completely replace with accidental delete guard)
    #         updated_photos = []
    #         if photo_urls is not None:
    #             clean_photo_urls = [
    #                 url.strip() for url in photo_urls if url and url.strip()
    #             ]

    #             if not clean_photo_urls:
    #                 logger.warning(
    #                     f"[PropertyRepository] Update rejected for {property_id}: Photo list cannot be empty."
    #                 )
    #                 raise RepositoryException(
    #                     user_message="A property must have at least one valid photo.",
    #                     internal_detail="A property must have at least one valid photo url",
    #                     status_code=400,
    #                 )

    #             real_property_id = str(property_id)
    #             final_photo_urls: list[str] = []

    #             for url in clean_photo_urls:
    #                 old_public_id = self.image_service.extract_public_id_from_url(url)

    #                 current_folder_id = (
    #                     self.image_service.extract_fake_id_from_public_id(
    #                         old_public_id, "properties"
    #                     )
    #                 )

    #                 if current_folder_id == real_property_id:
    #                     # Already lives in the correct permanent folder — nothing to rename
    #                     final_photo_urls.append(url)
    #                     continue

    #                 # Still under a fake id (uploaded fresh this edit session) — rename it
    #                 new_public_id = old_public_id.replace(
    #                     current_folder_id, real_property_id
    #                 )
    #                 final_public_id = new_public_id.replace("temp/", "")

    #                 try:
    #                     renamed = await self.image_service.provider.rename_image(
    #                         old_public_id, final_public_id
    #                     )
    #                     final_photo_urls.append(renamed["url"])
    #                 except Exception as e:
    #                     logger.error(
    #                         f"[PropertyRepository] Failed to rename image {old_public_id}: {str(e)}"
    #                     )
    #                     raise ImageStorageException(
    #                         "Failed to finalize property images",
    #                         f"Failed to finalize property images: {str(e)}",
    #                     )

    #             await self.db.execute(
    #                 delete(PropertyPhoto).where(
    #                     PropertyPhoto.property_id == property_id
    #                 )
    #             )
    #             for url in final_photo_urls:
    #                 new_photo = PropertyPhoto(property_id=property_id, photo_url=url)
    #                 self.db.add(new_photo)
    #                 updated_photos.append(new_photo)

    #         # 6. Flush staged data to run database constraint logic checks before committing
    #         await self.db.flush()

    #         # 7. Finalize database transaction permanently
    #         await self.db.commit()
    #         logger.info(
    #             f"[PropertyRepository] Full graph transaction committed for property id: {property_id}"
    #         )

    #         # 8. Refresh instance states to prevent lazy-load expiration bugs out of transaction scope
    #         await self.db.refresh(existing_property)
    #         if active_detail:
    #             await self.db.refresh(active_detail)

    #         return {
    #             "property": existing_property,
    #             "hotel_detail": active_detail,
    #             "amenities": updated_final_amenities,
    #             "photo_urls": updated_photos,
    #         }

    #     except (
    #         PropertyNotFoundException,
    #         DefaultAmenityNotExistsException,
    #         ImageStorageException,
    #         RepositoryException,
    #         InvalidImageException,
    #     ):
    #         await self.db.rollback()
    #         raise

    #     except Exception as e:
    #         # ALL-OR-NOTHING COUNTERMEASURE: Clear out every staged alteration state entry
    #         await self.db.rollback()
    #         logger.critical(
    #             f"[PropertyRepository] Update transaction aborted. State rolled back. Error: {str(e)}"
    #         )
    #         raise RepositoryException(
    #             user_message="Unable to update property.Please try again later.",
    #             internal_detail=f"[PropertyRepository] Update transaction aborted. State rolled back. Error: {str(e)}",
    #             status_code=500,
    #         )

    # async def update_property_activation(
    #     self, property_id: uuid.UUID, tenant_id: uuid.UUID
    # ):
    #     try:
    #         stmt = select(Property).where(
    #             and_(Property.id == property_id, Property.tenant_id == tenant_id)
    #         )
    #         result = await self.db.execute(stmt)
    #         existing_property = result.scalar_one_or_none()
    #         if not existing_property:
    #             logger.error(
    #                 f"[PropertyRepository] Property {property_id} not found or unauthorized."
    #             )
    #             raise PropertyNotFoundException("Property not found or access denied.")
    #         existing_property.is_active = not existing_property.is_active
    #         await self.db.commit()
    #         logger.info(
    #             f"[PropertyRepository] Property {property_id} activation updated successfully"
    #         )
    #         return existing_property
    #     except PropertyNotFoundException:
    #         raise
    #     except Exception as e:
    #         await self.db.rollback()
    #         logger.error(
    #             f"[PropertyRepository] Error updating property {property_id}: {str(e)}"
    #         )
    #         raise RepositoryException(
    #             internal_detail=f"Error updating property: {str(e)}"
    #         )

    # async def delete_property(self, property_id: uuid.UUID, tenant_id: uuid.UUID):
    #     logger.info(f"[PropertyRepository] Deleting property: {property_id}")
    #     try:
    #         stmt = select(Property).where(
    #             and_(Property.id == property_id, Property.tenant_id == tenant_id)
    #         )
    #         result = await self.db.execute(stmt)
    #         existing_property = result.scalar_one_or_none()
    #         if not existing_property:
    #             logger.error(
    #                 f"[PropertyRepository] Property {property_id} not found or unauthorized."
    #             )
    #             raise PropertyNotFoundException("Property not found or access denied.")
    #         await self.db.delete(existing_property)
    #         await self.db.commit()
    #         logger.info(
    #             f"[PropertyRepository] Property {property_id} deleted successfully"
    #         )
    #         return existing_property

    #     except PropertyNotFoundException:
    #         await self.db.rollback()
    #         raise

    #     except LookupError as e:
    #         # Added handler to gracefully catch invalid database enum rows without 500 crashes
    #         await self.db.rollback()
    #         logger.error(
    #             f"[PropertyRepository] Database Enum conversion failure: {str(e)}"
    #         )
    #         raise RepositoryException(
    #             internal_detail="Database parsing failure: Related data records contain invalid data values."
    #         )
    #     except Exception as e:
    #         await self.db.rollback()
    #         logger.error(
    #             f"[PropertyRepository] Error deleting property {property_id}: {str(e)}"
    #         )
    #         raise RepositoryException(
    #             internal_detail=f"Error deleting property: {str(e)}"
    #         )

    # async def get_all_amenities(self):
    #     logger.info("[PropertyRepository] Fetching all default amenities")
    #     try:
    #         stmt = select(Amenity).where(
    #             and_(Amenity.is_default, Amenity.property_id.is_(None))
    #         )
    #         result = await self.db.execute(stmt)
    #         amenities = result.scalars().all()
    #         logger.info(
    #             f"[PropertyRepository] Fetched {len(amenities)} default amenities"
    #         )
    #         return amenities
    #     except Exception as e:
    #         logger.error(
    #             f"[PropertyRepository] Error fetching default amenities: {str(e)}"
    #         )
    #         raise RepositoryException(
    #             internal_detail=f"Error fetching default amenities: {str(e)}"
    #         )

    # async def get_images_count_by_property_id(self, property_id: uuid.UUID):
    #     logger.info(
    #         f"[PropertyRepository] Fetching image count for property {property_id}"
    #     )
    #     try:
    #         stmt = select(func.count(PropertyPhoto.id)).where(
    #             PropertyPhoto.property_id == property_id
    #         )
    #         result = await self.db.execute(stmt)
    #         count = result.scalar_one()
    #         logger.info(
    #             f"[PropertyRepository] Fetched {count} images for property {property_id}"
    #         )
    #         return count
    #     except Exception as e:
    #         logger.error(
    #             f"[PropertyRepository] Error fetching image count for property {property_id}: {str(e)}"
    #         )
    #         raise RepositoryException(
    #             internal_detail=f"Error fetching image count for property: {str(e)}"
    #         )

    # # async def get_available_properties(
    # #     self,
    # #     destination: str,
    # #     check_in: date,
    # #     check_out: date,
    # #     adults: int,
    # #     children: int,
    # #     room_count: int,
    # # ):
    # #     logger.info(
    # #         f"[PropertyRepository] Fetching available properties for destination: {destination}, check-in: {check_in}, check-out: {check_out}, adults: {adults}, children: {children}, room count: {room_count}"
    # #     )
    # #     try:
    # #         # 1. Subquery: Extract room IDs actively booked
    # #         booked_rooms_subquery = (
    # #             select(BookingRoom.room_unit_id)
    # #             .join(Booking, BookingRoom.booking_id == Booking.id)
    # #             .where(
    # #                 and_(
    # #                     Booking.checkin_date < check_out,
    # #                     Booking.checkout_date > check_in,
    # #                     Booking.status != MasterBookingStatus.CANCELLED,
    # #                 )
    # #             )
    # #             .scalar_subquery()
    # #         )

    # #         # 2. Subquery: Fetch exactly ONE image url per property row
    # #         # Sorts by id or an order column if you have one, limiting output to 1 row
    # #         single_photo_subquery = (
    # #             select(PropertyPhoto.photo_url)
    # #             .where(PropertyPhoto.property_id == Property.id)
    # #             .order_by(PropertyPhoto.id)
    # #             .limit(1)
    # #             .scalar_subquery()
    # #         )

    # #         # 3. Text filters for destination matching
    # #         destination_wildcard = f"%{destination}%"
    # #         search_filter = or_(
    # #             func.lower(Property.name).like(destination_wildcard),
    # #             func.lower(Property.country).like(destination_wildcard),
    # #             func.lower(Property.state).like(destination_wildcard),
    # #             func.lower(Property.city).like(destination_wildcard),
    # #             func.lower(Property.address).like(destination_wildcard),
    # #         )

    # #         # 4. Complete structural query execution
    # #         stmt = (
    # #             select(
    # #                 Property.id.label("property_id"),
    # #                 Property.name.label("property_name"),
    # #                 func.min(Rooms.base_rate).label("lowest_price"),
    # #                 Property.address,
    # #                 Property.city,
    # #                 Property.state,
    # #                 Property.country,
    # #                 single_photo_subquery.label("photo_url"),
    # #             )
    # #             .join(Property.hotel_detail)
    # #             .join(PropertyHotelDetail.rooms)
    # #             .where(
    # #                 and_(
    # #                     Property.is_active == True,
    # #                     search_filter,
    # #                     Rooms.max_adults >= adults,
    # #                     Rooms.max_children >= children,
    # #                     Rooms.status == RoomStatus.AVAILABLE,
    # #                     not_(Rooms.id.in_(booked_rooms_subquery)),
    # #                 )
    # #             )
    # #             .group_by(
    # #                 Property.id,
    # #                 Property.name,
    # #                 Property.address,
    # #                 Property.city,
    # #                 Property.state,
    # #                 Property.country,
    # #             )
    # #             .having(func.count(Rooms.id) >= room_count)
    # #         )
    # #         result = await self.db.execute(stmt)
    # #         available_properties = result.all()
    # #         logger.info(
    # #             f"[PropertyRepository] Found {len(available_properties)} available properties"
    # #         )

    # #         return available_properties
    # #     except Exception as e:
    # #         logger.error(
    # #             f"[PropertyRepository] Error fetching available properties: {str(e)}"
    # #         )
    # #         raise RepositoryException(
    # #             "Error fetching available properties",
    # #             f"Error fetching available properties: {str(e)}",
    # #         )

    # async def get_available_properties(
    #     self,
    #     destination: str,
    #     check_in: date,
    #     check_out: date,
    #     adults: int,
    #     children: int,
    #     room_count: int,
    # ) -> list[dict]:
    #     logger.info(
    #         f"[PropertyRepository] Fetching available properties for destination: "
    #         f"{destination}, check-in: {check_in}, check-out: {check_out}, "
    #         f"adults: {adults}, children: {children}, room count: {room_count}"
    #     )
    #     try:
    #         candidate_rooms = await self._fetch_candidate_rooms(
    #             destination, check_in, check_out
    #         )

    #         available_properties = self._select_feasible_properties(
    #             candidate_rooms,
    #             check_in=check_in,
    #             check_out=check_out,
    #             adults=adults,
    #             children=children,
    #             room_count=room_count,
    #         )

    #         logger.info(
    #             f"[PropertyRepository] Found {len(available_properties)} available properties"
    #         )
    #         return available_properties

    #     except Exception as e:
    #         logger.error(
    #             f"[PropertyRepository] Error fetching available properties: {str(e)}"
    #         )
    #         raise RepositoryException(
    #             "Error fetching available properties",
    #             f"Error fetching available properties: {str(e)}",
    #         )

    # # ------------------------------------------------------------------
    # # Stage 1 — SQL: cheap, per-row-only conditions.
    # # No adults/children capacity filtering here — that requires
    # # reasoning across multiple rows (the whole point of room_count).
    # # ------------------------------------------------------------------
    # async def _fetch_candidate_rooms(
    #     self, destination: str, check_in: date, check_out: date
    # ) -> list[_CandidateRoom]:
    #     booked_rooms_subquery = (
    #         select(BookingRoom.room_unit_id)
    #         .join(Booking, BookingRoom.booking_id == Booking.id)
    #         .where(
    #             and_(
    #                 Booking.checkin_date < check_out,
    #                 Booking.checkout_date > check_in,
    #                 Booking.status != MasterBookingStatus.CANCELLED,
    #             )
    #         )
    #         .scalar_subquery()
    #     )

    #     destination_wildcard = f"%{destination.lower()}%"
    #     search_filter = or_(
    #         func.lower(Property.name).like(destination_wildcard),
    #         func.lower(Property.country).like(destination_wildcard),
    #         func.lower(Property.state).like(destination_wildcard),
    #         func.lower(Property.city).like(destination_wildcard),
    #         func.lower(Property.address).like(destination_wildcard),
    #     )

    #     # One representative photo per property (first by id; swap to an
    #     # is_cover flag / order column if PropertyPhoto has one).
    #     single_photo_subquery = (
    #         select(PropertyPhoto.photo_url)
    #         .where(PropertyPhoto.property_id == Property.id)
    #         .order_by(PropertyPhoto.id)
    #         .limit(1)
    #         .scalar_subquery()
    #     )

    #     stmt = (
    #         select(
    #             Property.id.label("property_id"),
    #             Property.name.label("property_name"),
    #             Property.address,
    #             Property.city,
    #             Property.state,
    #             Property.country,
    #             single_photo_subquery.label("photo_url"),
    #             Rooms.id.label("room_id"),
    #             Rooms.room_type_id,
    #             Rooms.max_adults,
    #             Rooms.max_children,
    #             Rooms.base_rate,
    #         )
    #         .select_from(Property)
    #         .join(Property.hotel_detail)
    #         .join(PropertyHotelDetail.rooms)
    #         .where(
    #             and_(
    #                 Property.is_active == True,  # noqa: E712
    #                 search_filter,
    #                 Rooms.status == RoomStatus.AVAILABLE,
    #                 Rooms.max_adults >= 1,  # a 0-adult room can never host anyone
    #                 not_(Rooms.id.in_(booked_rooms_subquery)),
    #             )
    #         )
    #     )

    #     result = await self.db.execute(stmt)
    #     rows = result.all()
    #     return [
    #         _CandidateRoom(
    #             property_id=r.property_id,
    #             property_name=r.property_name,
    #             address=r.address,
    #             city=r.city,
    #             state=r.state,
    #             country=r.country,
    #             photo_url=r.photo_url,
    #             room_type_id=r.room_type_id,
    #             room_id=r.room_id,
    #             max_adults=r.max_adults,
    #             max_children=r.max_children,
    #             base_rate=r.base_rate,
    #         )
    #         for r in rows
    #     ]

    # # ------------------------------------------------------------------
    # # Stage 2 — Python: group by property_id, run the
    # # HETEROGENEOUS allocation engine on each group's ACTUAL per-room
    # # capacities, then price the specific winning rooms for the stay.
    # # ------------------------------------------------------------------
    # def _select_feasible_properties(
    #     self,
    #     candidate_rooms: list[_CandidateRoom],
    #     *,
    #     check_in: date,
    #     check_out: date,
    #     adults: int,
    #     children: int,
    #     room_count: int,
    # ) -> list[dict]:
    #     grouped: dict[uuid.UUID, list[_CandidateRoom]] = defaultdict(list)
    #     for room in candidate_rooms:
    #         grouped[room.property_id].append(room)

    #     best_price_by_property: dict[uuid.UUID, dict] = {}

    #     for property_id, rooms in grouped.items():
    #         if len(rooms) < room_count:
    #             continue  # not enough rooms of any type to attempt a split

    #         # Real per-room capacity list — NOT a group-level min/average,
    #         # since rooms sharing a room_type_id can genuinely differ.
    #         capacities = [
    #             RoomCapacity(
    #                 max_adults=r.max_adults,
    #                 max_children=r.max_children,
    #                 max_total_occupancy=r.max_adults + r.max_children,
    #             )
    #             for r in rooms
    #         ]

    #         allocation = HeterogeneousGuestAllocationEngine(capacities).allocate(
    #             total_adults=adults,
    #             total_children=children,
    #             room_count=room_count,
    #         )
    #         if not allocation.feasible:
    #             continue

    #         used_rooms = [rooms[a.room_index] for a in allocation.rooms]
    #         rates = [r.base_rate for r in used_rooms]
    #         if any(rate is None for rate in rates):
    #             continue  # can't quote a price if any chosen room has no rate set

    #         stay_price = calculate_stay_total(
    #             room_base_rates=rates, check_in=check_in, check_out=check_out
    #         )

    #         existing = best_price_by_property.get(property_id)
    #         if existing is None or stay_price < existing["price"]:
    #             sample = rooms[0]
    #             best_price_by_property[property_id] = {
    #                 "property_id": property_id,
    #                 "property_name": sample.property_name,
    #                 "country": sample.country,
    #                 "state": sample.state,
    #                 "city": sample.city,
    #                 "address": sample.address,
    #                 "photo_url": sample.photo_url,  # None if property has no photos yet
    #                 "price": stay_price,
    #             }

    #     return list(best_price_by_property.values())
