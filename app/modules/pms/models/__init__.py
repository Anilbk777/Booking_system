from .tenants_model import Tenant
from .properties_model import (
    Property,
    PropertyPhoto,
    Amenity,
    PropertyAmenity,
    PropertyHotelDetail,
)
from .rooms_model import RoomType, BedType, Rooms, RoomPhoto

__all__ = [
    "Tenant",
    "Amenity",
    "Property",
    "PropertyPhoto",
    "PropertyAmenity",
    "PropertyHotelDetail",
    "RoomType",
    "BedType",
    "Rooms",
    "RoomPhoto",
]
