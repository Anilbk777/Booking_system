from .tenants_model import Tenant
from .properties_model import (
    Property,
    PropertyPhoto,
    Amenity,
    PropertyAmenity,
    PropertyHotelDetail,
)
from .rooms_model import RoomType, BedType, Rooms, RoomPhoto
from .offers_model import SpecialOffer
from .discount_code_model import DiscountCode

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
    "SpecialOffer",
    "DiscountCode"
]
