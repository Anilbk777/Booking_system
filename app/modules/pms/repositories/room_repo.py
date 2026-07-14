from app.modules.pms.services.image_services import ImageService
import uuid

from sqlalchemy import delete, func, select, and_, or_
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.pms.models.properties_model import Amenity
from app.modules.pms.models.rooms_model import (
    BedType,

    Rooms,
    RoomType,
)
from app.utils.exceptions import (
    RepositoryException,
    RoomNameAlreadyExistsException,
    RoomNotFoundException,
    AmenityNotFoundException,
    ImageStorageException,
    InvalidImageException
)
from app.utils.logging import LoggerFactory
import psycopg.errors

logger = LoggerFactory.get_logger(__name__)


class RoomRepository:
    def __init__(self, db: AsyncSession, image_service:ImageService):
        self.db = db
        self.image_service = image_service

    async def create_rooms(
        self, property_id :uuid.UUID, rooms_data: list[dict]
    ) -> list[dict]:
        logger.info(
            f"[RoomRepository] Initiating bulk transaction for {len(rooms_data)} rooms"
        )
        try:
            rooms = [
                Rooms(
                    property_id=property_id,
                    room_type_id=room["room_type_id"],
                    bed_type_id=room["bed_type_id"],
                    floor_number=room["floor_number"],
                    room_name=room["room_name"],
                    max_adults=room["max_adults"],
                    max_children=room["max_children"],
                    base_rate=room["base_rate"],
                    status=room["status"],
                    cancellation_policy=room["cancellation_policy"],
                    cancellation_title=room["cancellation_title"],
                    cancellation_description=room["cancellation_description"],
                    photos=room["photos"],
                    system_amenity_ids=room["system_amenity_ids"],
                    custom_amenities=room["custom_amenities"],
                )

                for room in rooms_data
            ]
            self.db.add_all(rooms)
            await self.db.flush()

            for room in rooms:
                await self.db.refresh(room)

            return rooms
     
        except IntegrityError as e:
            await self.db.rollback()
            
            # Extract the underlying driver error (asyncpg)
            orig_err = getattr(e, "orig", None)
            
            if orig_err and hasattr(orig_err, "__cause__"):
                pg_exc = orig_err.__cause__
                
                if isinstance(pg_exc, psycopg.errors.UniqueViolation):
                    # Target unique index/constraints (e.g., uq_room_types_property_id_room_type_name or your rooms unique name index)
                    constraint_name = pg_exc.constraint_name or pg_exc.index_name
                    logger.warning(f"[RoomRepository] Unique key or index conflict hit: {constraint_name}")
                    raise RepositoryException(
                        internal_detail=f"A room configuration or name collision occurred (Violated: {constraint_name}).",
                        status_code = 400
                    )
                    
                elif isinstance(pg_exc, psycopg.errors.CheckViolation):
                    # Target check constraints (e.g., chk_room_types_default_property_consistency)
                    constraint_name = pg_exc.constraint_name
                    logger.warning(f"[RoomRepository] Check constraint broken: {constraint_name}")
                    raise RepositoryException(
                        internal_detail= f"Data failed business logic checks. Ensure standard/default flags are valid (Violated: {constraint_name}).",
                        status_code = 400
                    )
                    
                elif isinstance(pg_exc, psycopg.errors.ForeignKeyViolation):
                    logger.warning(f"[RoomRepository] Foreign key link missing: {pg_exc.detail}")
                    raise RepositoryException(
                        internal_detail= f"The specified room type, bed type, or property ID does not exist.",
                    
                        status_code = 400
                    )

            # Fallback for generic integrity issues (e.g. non-nullable failures)
            logger.error(f"[RoomRepository] Database consistency violation: {str(e)}")
            raise RepositoryException(f"Database consistency error during batch processing: {str(e)}")


        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"[RoomRepository] Unexpected bulk creation collapse: {str(e)}"
            )
            raise RepositoryException(f"Failed to batch create rooms: {str(e)}")



    async def get_exisitng_room_type_name(
        self, property_id:uuid.UUID, name:str
    ):
        """check name collision"""
        logger.info(f"[RoomRepository] Validating room type name collision")
        try:
            stmt = select(RoomType).where(
            # Match either this specific property OR a global default (property_id is NULL)
            or_(
                RoomType.property_id == property_id,
                RoomType.property_id.is_(None)
            ),
            func.lower(RoomType.room_type_name) == func.lower(name)
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(
                f"[RoomRepository] Unexpected error checking room type name collision: {str(e)}"
            )
            raise RepositoryException(f"Failed to check room type name collision: {str(e)}")
            

    async def get_exisiting_bed_type_name(
        self, property_id:uuid.UUID, name:str
    ):
        logger.info(f"[RoomRepository] validating bed type name collision")
        try:
            stmt = select(BedType).where(
            # Match either this specific property OR a global default (property_id is NULL)
            or_(
                BedType.property_id == property_id,
                BedType.property_id.is_(None)
            ),
            func.lower(BedType.bed_name) == func.lower(name)
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"[RoomRepository] Unexpected error checking bed type name collision: {str(e)}"
            )
            raise RepositoryException(f"Failed to check bed type name collision: {str(e)}")


    async def create_room_type(
        self, property_id:uuid.UUID, room_type_data:dict
    ):
        try:
            room_type = RoomType(
                property_id=property_id,
                room_type_name=room_type_data["room_type_name"],
                is_default=False,
            )
            self.db.add(room_type)
            await self.db.commit()
            await self.db.refresh(room_type)
            return room_type
        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"[RoomRepository] Unexpected error creating room type: {str(e)}"
            )
            raise RepositoryException(f"Failed to create room type: {str(e)}")

    async def create_bed_type(
        self, property_id:uuid.UUID, bed_type_data:dict
    ):
        try:
            bed_type = BedType(
                property_id=property_id,
                bed_name=bed_type_data["bed_name"],
                is_default=False,
            )
            self.db.add(bed_type)
            await self.db.commit()
            await self.db.refresh(bed_type)
            return bed_type
        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"[RoomRepository] Unexpected error creating bed type: {str(e)}"
            )
            raise RepositoryException(f"Failed to create bed type: {str(e)}")
