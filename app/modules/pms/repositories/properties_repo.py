import uuid
from typing import Any, Awaitable, Callable, TypeVar

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.exc import DBAPIError, IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.pms.models.properties_model import (
    Amenity,
    Property,
    PropertyAmenity,
    PropertyHotelDetail,
    PropertyPhoto,
)
from app.utils.exceptions import DefaultAmenityNotExistsException, RepositoryException
from app.utils.logging import LoggerFactory

T = TypeVar("T")

logger = LoggerFactory.get_logger(__name__)


# class PropertyRepository:
#     def __init__(self, db: AsyncSession):
#         self.db = db

#     async def create_property(self, property_data: dict) -> Property:
#         logger.info(
#             f"[PropertyRepository] Creating property: {property_data['name']} of tenant {property_data['tenant_id']}"
#         )
#         try:
#             new_property = Property(**property_data)
#             self.db.add(new_property)
#             await self.db.commit()
#             await self.db.refresh(new_property)
#             logger.info("[PropertyRepository] Property created successfully")
#             return new_property
#         except IntegrityError as e:
#             await self.db.rollback()
#             logger.error(
#                 "[PropertyRepository] Error creating property: Integrity constraint violated"
#             )
#             raise RepositoryException(f"Integrity constraint violated: {str(e)}")
#         except SQLAlchemyError as e:
#             await self.db.rollback()
#             logger.error("[PropertyRepository] Error creating property: SQLA  ")
#             raise RepositoryException(f"SQLAlchemy error: {str(e)}")
#         except Exception as e:
#             await self.db.rollback()
#             logger.error(f"[PropertyRepository] Error creating property: {str(e)}")
#             raise RepositoryException(str(e))

#     async def get_property_by_id(
#         self, property_id: uuid.UUID, tenant_id: uuid.UUID
#     ) -> Property | None:
#         logger.info(f"[PropertyRepository] Getting property by id: {property_id}")
#         try:
#             result = await self.db.execute(
#                 select(Property).where(
#                     Property.id == property_id,
#                     Property.tenant_id == tenant_id,
#                 )
#             )
#             property = result.scalar_one_or_none()
#             return property
#         except Exception as e:
#             logger.error(f"[PropertyRepository] Error getting property by id: {str(e)}")
#             raise RepositoryException(str(e))


#     async def update_property(
#         self, property_id: uuid.UUID, tenant_id: uuid.UUID, property_data: dict
#     ) -> Property | None:
#         logger.info(f"[PropertyRepository] Updating property: {property_id}")
#         try:
#             query = (
#                 update(Property)
#                 .where(Property.id == property_id, Property.tenant_id == tenant_id)
#                 .values(**property_data)
#                 .returning(Property)
#             )
#             result = await self.db.execute(query)
#             updated_property = result.scalars().first()
#             await self.db.commit()
#             return updated_property
#         except Exception as e:
#             await self.db.rollback()
#             logger.error(f"[PropertyRepository] Error updating property: {str(e)}")
#             raise RepositoryException(str(e))

#     async def delete_property(
#         self, property_id: uuid.UUID, tenant_id: uuid.UUID
#     ) -> bool:
#         logger.info(f"[PropertyRepository] Deleting property: {property_id}")
#         try:
#             query = delete(Property).where(
#                 Property.id == property_id, Property.tenant_id == tenant_id
#             )
#             result = await self.db.execute(query)
#             await self.db.commit()
#             return result.rowcount > 0
#         except Exception as e:
#             await self.db.rollback()
#             logger.error(f"[PropertyRepository] Error deleting property: {str(e)}")
#             raise RepositoryException(str(e))

#     async def add_images_to_property(
#         self, property_id: uuid.UUID, photos: list[PropertyPhoto]
#     ) -> list[PropertyPhoto]:
#         logger.info(
#             f"[PropertyRepository] Adding {len(photos)} images to property {property_id}"
#         )
#         if not photos:
#             return []

#         try:
#             self.db.add_all(photos)
#             await self.db.commit()

#             for photo in photos:
#                 await self.db.refresh(photo)

#             return photos

#         except SQLAlchemyError as e:
#             await self.db.rollback()
#             logger.error(f"[PropertyRepository] Database error adding images: {str(e)}")
#             raise RepositoryException("Failed to save property images to the database.")
#         except Exception as e:
#             await self.db.rollback()
#             logger.error(
#                 f"[PropertyRepository] Unexpected error adding images: {str(e)}"
#             )
#             raise RepositoryException(
#                 "An unexpected error occurred while saving images."
#             )


class PropertyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _execute_creation(
        self,
        operation_name: str,
        db_op: Callable[[], Awaitable[T]],
    ) -> T:
        """Helper to handle common transaction and error logic."""
        logger.info(f"[PropertyRepository] {operation_name}")
        try:
            result = await db_op()
            await self.db.commit()
            await self.db.refresh(result)
            logger.info(f"[PropertyRepository] {operation_name} completed successfully")
            return result
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(
                f"[PropertyRepository] {operation_name} failed: Integrity constraint"
            )
            raise RepositoryException(f"Integrity constraint violated: {str(e)}")
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(
                f"[PropertyRepository] {operation_name} failed: SQLAlchemy error"
            )
            raise RepositoryException(f"SQLAlchemy error: {str(e)}")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[PropertyRepository] {operation_name} failed: {str(e)}")
            raise RepositoryException(str(e))

    async def create_property(self, property_data: dict) -> Property:
        async def operation():
            new_property = Property(
                tenant_id=property_data["tenant_id"],
                name=property_data["name"],
                type=property_data["type"],
                description=property_data["description"],
                country=property_data["country"],
                state=property_data["state"],
                city=property_data["city"],
                zip_code=property_data["zip_code"],
                address=property_data["address"],
                latitude=property_data["latitude"],
                longitude=property_data["longitude"],
                is_active=True,
            )
            self.db.add(new_property)
            return new_property

        return await self._execute_creation("Creating property", operation)

    async def create_hotel_detail(
        self, property_id: uuid.UUID, hotel_detail_data: dict
    ) -> PropertyHotelDetail:
        async def operation():
            new_hotel_detail = PropertyHotelDetail(
                property_id=property_id,
                check_in_time_from=hotel_detail_data["check_in_time_from"],
                check_in_time_to=hotel_detail_data["check_in_time_to"],
                check_out_time_from=hotel_detail_data["check_out_time_from"],
                check_out_time_to=hotel_detail_data["check_out_time_to"],
                total_rooms=hotel_detail_data["total_rooms"],
                number_of_floors=hotel_detail_data["number_of_floors"],
                year_built=hotel_detail_data["year_built"],
            )
            self.db.add(new_hotel_detail)
            return new_hotel_detail

        return await self._execute_creation("Creating hotel detail", operation)

    async def create_property_photo(
        self, property_id: uuid.UUID, photo_url: str
    ) -> PropertyPhoto:
        async def operation():
            new_photo = PropertyPhoto(
                property_id=property_id,
                photo_url=photo_url,
            )
            self.db.add(new_photo)
            return new_photo

        return await self._execute_creation("Creating property photo", operation)

    async def create_amenity(
        self, property_id: uuid.UUID, amenity_data: dict
    ) -> PropertyAmenity:
        async def operation():
            new_amenity = Amenity(
                property_id=property_id,
                name=amenity_data["name"],
                is_default=amenity_data["is_default"],
            )
            self.db.add(new_amenity)
            return new_amenity

        return await self._execute_creation("Creating amenity", operation)

    async def create_property_amenity(
        self, property_id: uuid.UUID, amenity_id: uuid.UUID
    ):
        async def operation():
            new_property_amenity = PropertyAmenity(
                property_id=property_id,
                amenity_id=amenity_id,
            )
            self.db.add(new_property_amenity)
            return new_property_amenity

        return await self._execute_creation("Creating property amenity", operation)

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

    def _is_valid_uuid(self, val: str) -> bool:
        try:
            uuid.UUID(str(val))
            return True
        except ValueError:
            return False

    async def save_property_graph(
        self,
        tenant_id: uuid.UUID,
        property_data: dict,
        hotel_detail_data: dict,
        amenities_input: list,
        photo_urls: list,
    ) -> Property:
        # 1. Instantiate and add the root Property model
        new_property = Property(
            tenant_id=tenant_id,
            **property_data,
        )
        # CRITICAL: Manually initialize the relationship lists on the new unsaved object
        # This prevents SQLAlchemy from trying to lazy-load them after a flush()
        new_property.property_amenities = []
        new_property.photos = []
        self.db.add(new_property)

        # 2. Force a flush so PostgreSQL generates the new_property.id
        # which is required to link custom amenities and details securely
        await self.db.flush()

        # 3. Handle Hotel Detail Insertion
        new_property.hotel_detail = PropertyHotelDetail(
            property_id=new_property.id,
            **hotel_detail_data,
        )

        # 4. Resolve Mixed Amenities (UUID Checkboxes + Custom Text Strings)
        for item in amenities_input:
            matched_amenity = None

            # Scenario A: Inbound item is a UUID identifier
            if isinstance(item, uuid.UUID) or (
                isinstance(item, str) and self._is_valid_uuid(item)
            ):
                stmt = select(Amenity).where(Amenity.id == item)
                result = await self.db.execute(stmt)
                matched_amenity = result.scalar_one_or_none()

            # Scenario B: Inbound item is a raw text string name
            elif isinstance(item, str):
                clean_name = item.strip()
                if not clean_name:
                    continue

                stmt = select(Amenity).where(
                    and_(
                        func.lower(Amenity.name) == clean_name.lower(),
                        or_(
                            Amenity.property_id.is_(None),
                            Amenity.property_id == new_property.id,
                        ),
                    )
                )

                result = await self.db.execute(stmt)
                matched_amenity = result.scalar_one_or_none()

                if not matched_amenity:
                    matched_amenity = Amenity(
                        name=clean_name,
                        is_default=False,
                        property_id=new_property.id,
                    )
                    self.db.add(matched_amenity)
                    await self.db.flush()

            if matched_amenity:
                # REFACTORED: Append the actual Amenity object directly to the proxy collection.
                # SQLAlchemy automatically generates the PropertyAmenity row for you.
                new_property.amenities.append(matched_amenity)

        # 5. Process and sequence Property Photos
        for photo_url in photo_urls:
            if photo_url.strip():  # Ensure non-empty URLs
                new_photo = PropertyPhoto(
                    property_id=new_property.id,
                    photo_url=photo_url.strip(),
                )
                new_property.photos.append(new_photo)

        # 6. Commit the entire Transaction graph to the database
        try:
            await self.db.commit()
            await self.db.refresh(
                new_property,
                attribute_names=["hotel_detail", "property_amenities", "photos"],
            )
            return new_property
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[PropertyRepository] Error saving property graph: {str(e)}")
            raise RepositoryException(str(e))

    async def get_existing_amenities(self) -> list[Amenity]:
        logger.info("[PropertyRepository] Fetching existing amenities")
        try:
            result = await self.db.execute(
                select(Amenity).where(Amenity.is_default == True)
            )
            return list(result.scalars().all())

        except Exception as e:
            logger.error(
                f"[PropertyRepository] Error fetching existing amenities: {str(e)}"
            )
            raise RepositoryException(str(e))

    async def manage_property_amenities(
        self, property_id: uuid.UUID, amenities_input: list
    ) -> list[Amenity]:
        """
        Manages, creates, and links amenities for a specific property independently.
        Returns a complete list of Amenity objects selected for this property.
        """
        logger.info(
            f"[PropertyRepository] Managing amenities for property {property_id} with {amenities_input} input items."
        )
        final_amenities: list[Amenity] = []
        junction_rows_to_add: list[PropertyAmenity] = []
        try:
            for amenity_in in amenities_input:
                clean_name = amenity_in["name"].strip()
                if not clean_name:
                    continue

                matched_amenity = None

                # SCENARIO A: Global default amenity lookup
                if amenity_in["is_default"]:
                    stmt = select(Amenity).where(
                        and_(
                            func.lower(Amenity.name) == clean_name.lower(),
                            Amenity.is_default,
                            Amenity.property_id.is_(None),
                        )
                    )
                    result = await self.db.execute(stmt)
                    matched_amenity = result.scalar_one_or_none()

                    if not matched_amenity:
                        logger.warning(
                            f"Global default amenity '{clean_name}' not found."
                        )

                # SCENARIO B: Custom amenity lookup / creation
                else:
                    stmt = select(Amenity).where(
                        and_(
                            func.lower(Amenity.name) == clean_name.lower(),
                            Amenity.property_id == property_id,
                        )
                    )
                    result = await self.db.execute(stmt)
                    matched_amenity = result.scalar_one_or_none()

                    if not matched_amenity:
                        matched_amenity = Amenity(
                            name=clean_name,
                            is_default=False,
                            property_id=property_id,
                        )
                        self.db.add(matched_amenity)
                        # Flush ensures PostgreSQL generates matched_amenity.id instantly
                        await self.db.flush()

                # If a valid amenity is found or created, prepare the junction row linkage
                if matched_amenity:
                    final_amenities.append(matched_amenity)

                    # Check if this specific link already exists to prevent duplicate key errors
                    link_stmt = select(PropertyAmenity).where(
                        and_(
                            PropertyAmenity.property_id == property_id,
                            PropertyAmenity.amenity_id == matched_amenity.id,
                        )
                    )
                    link_result = await self.db.execute(link_stmt)
                    existing_link = link_result.scalar_one_or_none()

                    if not existing_link:
                        new_link = PropertyAmenity(
                            property_id=property_id, amenity_id=matched_amenity.id
                        )
                        junction_rows_to_add.append(new_link)

            # Bulk add all new junction table connections to the database session
            if junction_rows_to_add:
                self.db.add_all(junction_rows_to_add)
                await self.db.flush()

            return final_amenities

        except IntegrityError as e:
            # Catch explicit database constraint rejections
            await self.db.rollback()
            error_msg = str(e.orig) if hasattr(e, "orig") else str(e)
            logger.error(
                f"[PropertyRepository] Integrity constraint violation: {error_msg}"
            )

            if "uq_property_amenities_property_amenity" in error_msg:
                raise RepositoryException(
                    "This amenity is already linked to the specified property."
                )
            if "uq_amenities_property_id_name" in error_msg:
                raise RepositoryException(
                    "A custom amenity with this name already exists for this property."
                )
            if (
                "fk_property_amenities_property" in error_msg
                or "properties.id" in error_msg
            ):
                raise RepositoryException(
                    "Cannot link amenities. The specified property ID does not exist."
                )

            raise RepositoryException(
                f"Database consistency error while saving amenities: {error_msg}"
            )

        except DBAPIError as e:
            # Catch driver-level connectivity drops or general operational problems
            await self.db.rollback()
            logger.error(f"[PropertyRepository] Database operational error: {str(e)}")
            raise RepositoryException(
                "Internal database error occurred while organizing amenities."
            )

        except Exception as e:
            # Generic fallback block
            await self.db.rollback()
            logger.error(
                f"[PropertyRepository] Unexpected amenities management crash: {str(e)}"
            )
            raise RepositoryException(f"Failed to manage property amenities: {str(e)}")

    async def create_property_photos(
        self, property_id: uuid.UUID, photo_urls: list[str]
    ) -> list[PropertyPhoto]:
        logger.info(
            f"[PropertyRepository] Adding {len(photo_urls)} images to property {property_id}"
        )
        if not photo_urls:
            return []

        try:
            new_photos = [
                PropertyPhoto(property_id=property_id, photo_url=url.strip())
                for url in photo_urls
                if url.strip()
            ]
            self.db.add_all(new_photos)
            await self.db.flush()

            return new_photos

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"[PropertyRepository] Database error adding images: {str(e)}")
            raise RepositoryException("Failed to save property images to the database.")
        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"[PropertyRepository] Unexpected error adding images: {str(e)}"
            )
            raise RepositoryException(
                "An unexpected error occurred while saving images."
            )

    async def create_property_transactional(
        self,
        tenant_id: uuid.UUID,
        property_data: dict,
        hotel_detail_data: dict,
        amenities_input: list,
        photo_urls: list,
    ) -> dict:
        """
        Creates a property and all its related child sub-graphs atomically.
        Ensures complete success or rolls back the entire database change state.
        """
        logger.info("[PropertyRepository] Initiating atomic property graph insertion")

        try:
            # 1. Instantiate and stage the root Property model
            new_property = Property(
                tenant_id=tenant_id,
                **property_data,
            )
            self.db.add(new_property)

            # 2. Flush to force PostgreSQL to safely generate new_property.id
            await self.db.flush()

            # 3. Instantiate and stage the Hotel Details configuration
            hotel_detail = PropertyHotelDetail(
                property_id=new_property.id,
                **hotel_detail_data,
            )
            self.db.add(hotel_detail)

            # 4. Resolve and stage Selections Amenities
            final_amenities: list[Amenity] = []
            for amenity_in in amenities_input:
                if isinstance(amenity_in, dict):
                    name_val = amenity_in.get("name", "")
                    is_default_val = amenity_in.get("is_default", False)
                else:
                    name_val = getattr(amenity_in, "name", "")
                    is_default_val = getattr(amenity_in, "is_default", False)

                clean_name = name_val.strip() if name_val else ""
                if not clean_name:
                    continue

                matched_amenity = None

                if is_default_val:
                    stmt = select(Amenity).where(
                        and_(
                            func.lower(Amenity.name) == clean_name.lower(),
                            Amenity.is_default,
                            Amenity.property_id.is_(None),
                        )
                    )
                    result = await self.db.execute(stmt)
                    matched_amenity = result.scalar_one_or_none()
                    if not matched_amenity:
                        logger.error(
                            f"[PropertyRepository] Default amenity '{clean_name}' does not exist in system."
                        )
                        raise DefaultAmenityNotExistsException(
                            f"The default amenity '{clean_name}' is not supported by the platform. "
                            f"Please use custom amenities for unique options."
                        )
                else:
                    stmt = select(Amenity).where(
                        and_(
                            func.lower(Amenity.name) == clean_name.lower(),
                            Amenity.property_id == new_property.id,
                        )
                    )
                    result = await self.db.execute(stmt)
                    matched_amenity = result.scalar_one_or_none()

                    if not matched_amenity:
                        matched_amenity = Amenity(
                            name=clean_name,
                            is_default=False,
                            property_id=new_property.id,
                        )
                        self.db.add(matched_amenity)
                        await self.db.flush()

                if matched_amenity:
                    final_amenities.append(matched_amenity)

                    # Verify link row uniqueness before staging
                    link_stmt = select(PropertyAmenity).where(
                        and_(
                            PropertyAmenity.property_id == new_property.id,
                            PropertyAmenity.amenity_id == matched_amenity.id,
                        )
                    )
                    link_result = await self.db.execute(link_stmt)
                    if not link_result.scalar_one_or_none():
                        new_link = PropertyAmenity(
                            property_id=new_property.id, amenity_id=matched_amenity.id
                        )
                        self.db.add(new_link)

            # 5. Process and stage Property Photos
            final_photos: list[PropertyPhoto] = []
            for url in photo_urls:
                if isinstance(url, str) and url.strip():
                    new_photo = PropertyPhoto(
                        property_id=new_property.id,
                        photo_url=url.strip(),
                    )
                    self.db.add(new_photo)
                    final_photos.append(new_photo)

            # 6. Flush all staged items to validate constraints before committing
            await self.db.flush()

            # 7. Commit everything together safely
            await self.db.commit()
            logger.info(
                f"[PropertyRepository] Property transactional chain committed: {new_property.id}"
            )

            return {
                "property": new_property,
                "hotel_detail": hotel_detail,
                "amenities": final_amenities,
                "photo_urls": final_photos,
            }

        except DefaultAmenityNotExistsException as e:
            await self.db.rollback()
            logger.error(
                f"[PropertyRepository] Default amenity validation failed: {str(e)}"
            )
            raise
        except IntegrityError as e:
            await self.db.rollback()
            error_msg = str(e.orig) if hasattr(e, "orig") else str(e)
            logger.error(
                f"[PropertyRepository] Transaction integrity failure: {error_msg}"
            )
            raise RepositoryException(f"Database consistency failure: {error_msg}")

        except DBAPIError as e:
            await self.db.rollback()
            logger.error(
                f"[PropertyRepository] Operational db transaction failure: {str(e)}"
            )
            raise RepositoryException(
                "Internal operational database breakdown occurred."
            )

        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"[PropertyRepository] Unexpected transactional crash: {str(e)}"
            )
            raise RepositoryException(f"Unexpected error occurred: {str(e)}")
