# from app.modules.pms.models.rooms_model import PropertyRoomUnit
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select, update, delete
# from app.utils.exceptions import RepositoryException
# from app.utils.logging import LoggerFactory
# import uuid

# logger = LoggerFactory.get_logger(__name__)

# class RoomUnitRepository:
#     def __init__(self, db: AsyncSession):
#         self.db = db

#     async def create_room_unit(self, data: dict) -> PropertyRoomUnit:
#         try:
#             new_unit = PropertyRoomUnit(**data)
#             self.db.add(new_unit)
#             await self.db.commit()
#             await self.db.refresh(new_unit)
#             return new_unit
#         except Exception as e:
#             await self.db.rollback()
#             raise RepositoryException(str(e))

#     async def get_room_units(self, property_id: uuid.UUID, room_type_id: uuid.UUID = None) -> list[PropertyRoomUnit]:
#         query = select(PropertyRoomUnit).where(PropertyRoomUnit.property_id == property_id)
#         if room_type_id:
#             query = query.where(PropertyRoomUnit.room_type_id == room_type_id)
#         result = await self.db.execute(query)
#         return result.scalars().all()

#     async def get_room_unit_by_id(self, unit_id: uuid.UUID) -> PropertyRoomUnit | None:
#         result = await self.db.execute(select(PropertyRoomUnit).where(PropertyRoomUnit.id == unit_id))
#         return result.scalar_one_or_none()

#     async def update_room_unit(self, unit_id: uuid.UUID, data: dict) -> PropertyRoomUnit | None:
#         query = update(PropertyRoomUnit).where(PropertyRoomUnit.id == unit_id).values(**data).returning(PropertyRoomUnit)
#         result = await self.db.execute(query)
#         await self.db.commit()
#         return result.scalar_one_or_none()

#     async def delete_room_unit(self, unit_id: uuid.UUID) -> bool:
#         query = delete(PropertyRoomUnit).where(PropertyRoomUnit.id == unit_id)
#         result = await self.db.execute(query)
#         await self.db.commit()
#         return result.rowcount > 0
