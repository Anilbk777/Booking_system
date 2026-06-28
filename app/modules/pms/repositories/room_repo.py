import uuid

from sqlalchemy import delete, func, select, update, and_ , or_
from sqlalchemy.orm import joinedload, selectinload
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

    async def get_all_rooms(self, hotel_id:uuid.UUID) -> list[Rooms]:
        logger.info(f"[RoomRepository] Fetching all rooms for hotel {hotel_id}")
        try:
            stmt = (
            select(Rooms)
            .where(Rooms.hotel_detail_id == hotel_id)
            .options(
                # Use joinedload for many-to-one objects (1-to-1 relations)
                joinedload(Rooms.bed_type),
                joinedload(Rooms.room_type),
                # Use selectinload for collection lists (1-to-many relations)
                selectinload(Rooms.room_photos),
                selectinload(Rooms.room_amenities).selectinload(RoomAmenity.amenity)
                )
            )
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"[RoomRepository] Unexpected fetch collapse: {str(e)}")
            raise RepositoryException(internal_detail=f"Failed to fetch rooms: {str(e)}")

