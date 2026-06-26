import uuid

from sqlalchemy import delete, func, select, update, and_ , or_

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.pms.models.rooms_model import (
    BedType,
    RoomAmenity,
    RoomPhoto,
    Rooms,
    RoomType,
)
from app.utils.exceptions import RepositoryException, RoomNameAlreadyExistsException
from app.utils.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class RoomRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
            
    async def create_rooms(self, room_data: list[dict], hotel_id: uuid.UUID) -> list[dict]:
        logger.info(f"[RoomRepository] Initiating bulk transaction for {len(room_data)} rooms")
        
        # Store all created rooms data to avoid overwriting references
        saved_batch_results = []

        try:
            for room_in in room_data:
                room_type_data = room_in.pop("room_type")
                bed_type_data = room_in.pop("bed_type")
                photos_data = room_in.pop("photos")
                amenities_data = room_in.pop("amenities")
                rooms_data = room_in

                # --- RESOLVE ROOM TYPE ---
                rt_name = room_type_data["room_type_name"].strip()
                is_rt_default = room_type_data.get("is_default", False)

                # Check if this room type was already loaded or saved during this batch session
                rt_stmt = select(RoomType).where(
                    and_(
                        func.lower(RoomType.room_type_name) == rt_name.lower(),
                        RoomType.hotel_detail_id == hotel_id
                    )
                )
                rt_result = await self.db.execute(rt_stmt)
                room_type_record = rt_result.scalar_one_or_none()

                # If it doesn't exist, create it once
                if not room_type_record:
                    room_type_record = RoomType(
                        hotel_detail_id=hotel_id,
                        room_type_name=rt_name,
                        is_default=is_rt_default,
                    )
                    self.db.add(room_type_record)
                    await self.db.flush()  # Generate room_type_record.id

                # --- RESOLVE BED TYPE ---
                bt_name = bed_type_data["bed_name"].strip()
                is_bt_default = bed_type_data.get("is_default", False)

                bt_stmt = select(BedType).where(
                    and_(
                        func.lower(BedType.bed_name) == bt_name.lower(),
                        BedType.hotel_detail_id == hotel_id
                    )
                )
                bt_result = await self.db.execute(bt_stmt)
                bed_type_record = bt_result.scalar_one_or_none()

                if not bed_type_record:
                    bed_type_record = BedType(
                        hotel_detail_id=hotel_id,
                        bed_name=bt_name,
                        is_default=is_bt_default,
                    )
                    self.db.add(bed_type_record)
                    await self.db.flush()  # Generate bed_type_record.id

                # --- CREATE THE ROOM ---
                new_room = Rooms(
                    hotel_detail_id=hotel_id,
                    room_type_id=room_type_record.id,
                    bed_type_id=bed_type_record.id,
                    **rooms_data,
                )
                self.db.add(new_room)
                await self.db.flush()  # Generate new_room.id

                # --- PROCESS PHOTOS ---
                photos_list = []
                for photo in photos_data:
                    if photo.strip():
                        new_photo = RoomPhoto(room_id=new_room.id, photo_url=photo.strip())
                        self.db.add(new_photo)
                        photos_list.append(new_photo)

                # --- PROCESS AMENITIES ---
                amenities_list = []
                for amenity_id in amenities_data:
                    new_room_amenity = RoomAmenity(room_id=new_room.id, amenity_id=amenity_id)
                    self.db.add(new_room_amenity)
                    amenities_list.append(new_room_amenity)

                # Append the structured record dictionary to the batch tracking collection
                saved_batch_results.append({
                    "room": new_room,
                    "room_type": room_type_record,
                    "bed_type": bed_type_record,
                    "room_photos": photos_list,
                    "room_amenities": amenities_list
                })

            # Commit everything as a single atomic unit
            await self.db.commit()
            return saved_batch_results

        except IntegrityError as e:
            await self.db.rollback()
            error_msg = str(e.orig) if hasattr(e, "orig") else str(e)
            logger.error(f"[RoomRepository] Bulk integrity violation crash: {error_msg}")
            if "uq_rooms_hotel_detail_room_name" in error_msg:
                raise RoomNameAlreadyExistsException("A room with this room name/number already exists in this hotel.")
            raise RepositoryException(f"Database consistency error during batch: {error_msg}")

        except Exception as e:
            await self.db.rollback()
            logger.error(f"[RoomRepository] Unexpected bulk creation collapse: {str(e)}")
            raise RepositoryException(f"Failed to batch create rooms: {str(e)}")


#     async def create_room_type(self, room_type: dict) -> RoomType:
#         logger.info(f"[RoomRepository] Creating room type: {room_type}")
#         try:
#             new_room_type = RoomType(**room_type)
#             self.db.add(new_room_type)
#             await self.db.commit()
#             await self.db.refresh(new_room_type)
#             logger.info("[RoomRepository] Room type created successfully")
#             return new_room_type
#         except Exception as e:
#             await self.db.rollback()
#             logger.error(f"[RoomRepository] Error creating room type: {str(e)}")
#             # Let it bubble up, IntegrityError will be caught by global handler
#             raise

#     async def get_room_types(self, property_id: uuid.UUID) -> list[RoomType]:
#         logger.info(f"[RoomRepository] Getting room types for property {property_id}")
#         try:
#             result = await self.db.execute(
#                 select(RoomType).where(RoomType.property_id == property_id)
#             )
#             room_types = result.scalars().all()
#             logger.info("[RoomRepository] Room types fetched successfully")
#             return room_types
#         except Exception as e:
#             logger.error(f"[RoomRepository] Error fetching room types: {str(e)}")
#             raise RepositoryException(str(e))

#     async def get_room_type_by_id(
#         self, room_type_id: uuid.UUID, property_id: uuid.UUID
#     ) -> RoomType | None:
#         logger.info(f"[RoomRepository] Getting room type by id: {room_type_id}")
#         try:
#             result = await self.db.execute(
#                 select(RoomType).where(
#                     RoomType.id == room_type_id, RoomType.property_id == property_id
#                 )
#             )
#             return result.scalar_one_or_none()
#         except Exception as e:
#             logger.error(f"[RoomRepository] Error getting room type by id: {str(e)}")
#             raise RepositoryException(str(e))

#     async def update_room_type(
#         self, room_type_id: uuid.UUID, property_id: uuid.UUID, room_type_data: dict
#     ) -> RoomType | None:
#         logger.info(f"[RoomRepository] Updating room type: {room_type_id}")
#         try:
#             query = (
#                 update(RoomType)
#                 .where(RoomType.id == room_type_id, RoomType.property_id == property_id)
#                 .values(**room_type_data)
#                 .returning(RoomType)
#             )
#             result = await self.db.execute(query)
#             updated = result.scalar_one_or_none()
#             await self.db.commit()
#             return updated
#         except Exception as e:
#             await self.db.rollback()
#             logger.error(f"[RoomRepository] Error updating room type: {str(e)}")
#             raise RepositoryException(str(e))

#     async def delete_room_type(
#         self, room_type_id: uuid.UUID, property_id: uuid.UUID
#     ) -> bool:
#         logger.info(f"[RoomRepository] Deleting room type: {room_type_id}")
#         try:
#             query = delete(RoomType).where(
#                 RoomType.id == room_type_id, RoomType.property_id == property_id
#             )
#             result = await self.db.execute(query)
#             await self.db.commit()
#             return result.rowcount > 0
#         except Exception as e:
#             await self.db.rollback()
#             logger.error(f"[RoomRepository] Error deleting room type: {str(e)}")
#             raise RepositoryException(str(e))

#     # --- Rate Plans ---

#     async def create_rate_plan(self, rate_plan_data: dict) -> RatePlan:
#         try:
#             new_rate_plan = RatePlan(**rate_plan_data)
#             self.db.add(new_rate_plan)
#             await self.db.commit()
#             await self.db.refresh(new_rate_plan)
#             return new_rate_plan
#         except Exception:
#             await self.db.rollback()
#             raise

#     async def get_rate_plans(self, property_id: uuid.UUID, room_type_id: uuid.UUID = None) -> list[RatePlan]:
#         query = select(RatePlan).where(RatePlan.property_id == property_id)
#         if room_type_id:
#             query = query.where(RatePlan.room_type_id == room_type_id)
#         result = await self.db.execute(query)
#         return result.scalars().all()

#     async def get_rate_plan_by_id(self, rate_plan_id: uuid.UUID) -> RatePlan | None:
#         result = await self.db.execute(select(RatePlan).where(RatePlan.id == rate_plan_id))
#         return result.scalar_one_or_none()

#     async def update_rate_plan(self, rate_plan_id: uuid.UUID, data: dict) -> RatePlan | None:
#         query = update(RatePlan).where(RatePlan.id == rate_plan_id).values(**data).returning(RatePlan)
#         result = await self.db.execute(query)
#         await self.db.commit()
#         return result.scalar_one_or_none()

#     async def delete_rate_plan(self, rate_plan_id: uuid.UUID) -> bool:
#         query = delete(RatePlan).where(RatePlan.id == rate_plan_id)
#         result = await self.db.execute(query)
#         await self.db.commit()
#         return result.rowcount > 0

#     # --- Date Overrides ---

#     async def create_date_override(self, data: dict) -> DateOverride:
#         new_obj = DateOverride(**data)
#         self.db.add(new_obj)
#         await self.db.commit()
#         await self.db.refresh(new_obj)
#         return new_obj

#     async def get_date_overrides(self, property_id: uuid.UUID) -> list[DateOverride]:
#         result = await self.db.execute(select(DateOverride).where(DateOverride.property_id == property_id))
#         return result.scalars().all()

#     async def update_date_override(self, override_id: uuid.UUID, data: dict) -> DateOverride | None:
#         query = update(DateOverride).where(DateOverride.id == override_id).values(**data).returning(DateOverride)
#         result = await self.db.execute(query)
#         await self.db.commit()
#         return result.scalar_one_or_none()

#     async def delete_date_override(self, override_id: uuid.UUID) -> bool:
#         query = delete(DateOverride).where(DateOverride.id == override_id)
#         result = await self.db.execute(query)
#         await self.db.commit()
#         return result.rowcount > 0

#     # --- Discount Codes ---

#     async def create_discount_code(self, data: dict) -> DiscountCode:
#         new_obj = DiscountCode(**data)
#         self.db.add(new_obj)
#         await self.db.commit()
#         await self.db.refresh(new_obj)
#         return new_obj

#     async def get_discount_codes(self, property_id: uuid.UUID) -> list[DiscountCode]:
#         result = await self.db.execute(select(DiscountCode).where(DiscountCode.property_id == property_id))
#         return result.scalars().all()

#     async def update_discount_code(self, discount_id: uuid.UUID, data: dict) -> DiscountCode | None:
#         query = update(DiscountCode).where(DiscountCode.id == discount_id).values(**data).returning(DiscountCode)
#         result = await self.db.execute(query)
#         await self.db.commit()
#         return result.scalar_one_or_none()

#     async def delete_discount_code(self, discount_id: uuid.UUID) -> bool:
#         query = delete(DiscountCode).where(DiscountCode.id == discount_id)
#         result = await self.db.execute(query)
#         await self.db.commit()
#         return result.rowcount > 0
