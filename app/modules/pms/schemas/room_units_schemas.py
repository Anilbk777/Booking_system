from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
import uuid
from app.modules.pms.models.rooms_model import RoomStatus

class RoomUnitBase(BaseModel):
    room_number: str = Field(..., description="Room number or label")
    floor: Optional[str] = Field(None, description="Floor level")
    status: RoomStatus = Field(default=RoomStatus.AVAILABLE)
    smoking: bool = Field(default=False)
    accessible: bool = Field(default=False)

class RoomUnitCreate(RoomUnitBase):
    property_id: uuid.UUID
    room_type_id: uuid.UUID

class RoomUnitUpdate(BaseModel):
    room_number: Optional[str] = None
    floor: Optional[str] = None
    status: Optional[RoomStatus] = None
    smoking: Optional[bool] = None
    accessible: Optional[bool] = None
    room_type_id: Optional[uuid.UUID] = None

class RoomUnitResponse(RoomUnitBase):
    id: uuid.UUID
    property_id: uuid.UUID
    room_type_id: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)
