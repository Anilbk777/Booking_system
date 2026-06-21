from app.modules.pms.services.tenant_services import TenantService
from app.modules.pms.repositories.tenants_repo import TenantRepository

from app.modules.pms.services.properties_scervices import PropertyService
from app.modules.pms.repositories.properties_repo import PropertyRepository

from app.modules.pms.services.room_services import RoomService
from app.modules.pms.repositories.room_repo import RoomRepository

from app.modules.pms.services.room_units_services import RoomUnitService
from app.modules.pms.repositories.room_units_repo import RoomUnitRepository

from app.config.database_config import get_db
from fastapi import Depends


def get_tenant_service(db=Depends(get_db)) -> TenantService:
    return TenantService(tenant_repo=TenantRepository(db=db))


def get_property_service(db=Depends(get_db)) -> PropertyService:
    return PropertyService(property_repository=PropertyRepository(db=db))


def get_room_service(db=Depends(get_db)) -> RoomService:
    return RoomService(RoomRepository(db=db), PropertyRepository(db=db))


def get_room_unit_service(db=Depends(get_db)) -> RoomUnitService:
    return RoomUnitService(
        room_unit_repo=RoomUnitRepository(db=db), property_repo=PropertyRepository(db=db)
    )
