# from pydantic import BaseModel, Field, ConfigDict
# from typing import Optional, List
# from app.modules.pms.models.rooms_model import RoomTypes, BedType
# import uuid
# from datetime import date
# class RoomTypeBase(BaseModel):
#     name: RoomTypes = Field(..., description="Name of the room type", examples= ["Standard", "Deluxe", "Suite", "Twin", "Double", "Single"])
#     description: Optional[str] = Field(None, description="Description of the room type")
#     max_occupancy: int = Field(..., ge=1, le=30, description="Maximum occupancy of the room type")
#     bed_type: BedType = Field(..., description="Bed type of the room type", examples= ["King", "Queen", "Twin", "Double", "Single"])
#     base_rate: float = Field(..., ge=0, description="Base rate of the room type")
#     photos: List[str] = Field(default_factory=list, description="Photos of the room type")
#     is_active: bool = Field(default=True, description="Whether the room type is active")

# class RoomTypeCreate(RoomTypeBase):
#     pass

# class RoomTypeResponse(RoomTypeBase):
#     id: uuid.UUID
#     property_id: uuid.UUID
    
#     model_config = ConfigDict(from_attributes=True)