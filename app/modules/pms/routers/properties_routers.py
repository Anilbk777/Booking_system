# from fastapi import APIRouter, Depends, status, UploadFile, File, HTTPException
# from app.modules.pms.schemas.properties_schemas import (
#     PropertyCreate,
#     PropertyResponse,
#     PropertyUpdate,
#     PropertyPhotoResponse,
# )
# from app.modules.pms.services.properties_scervices import PropertyService
# from app.modules.pms.dependencies import get_property_service
# from app.modules.auth.auth_middlewares import CurrentUser
# import uuid

# router = APIRouter(prefix="/pms/properties", tags=["Property Management System"])


# @router.post("/", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
# async def create_property(
#     property_data: PropertyCreate,
#     current_user: CurrentUser,
#     property_service: PropertyService = Depends(get_property_service),
# ):
#     if current_user.tenant_id is None:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="You are not authorized to create a property. You should have a tenant.",
#         )
#     return await property_service.create_property(
#         property_data.model_dump(), current_user.tenant_id
#     )


# @router.get(
#     "/{property_id}",
#     response_model=PropertyResponse,
#     status_code=status.HTTP_200_OK,
# )
# async def get_property(
#     property_id: uuid.UUID,
#     current_user: CurrentUser,
#     property_service: PropertyService = Depends(get_property_service),
# ):
#     if current_user.tenant_id is None:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="You are not authorized to get a property.",
#         )
#     return await property_service.get_property_by_id(
#         property_id, current_user.tenant_id
#     )


# @router.patch(
#     "/{property_id}",
#     response_model=PropertyResponse,
#     status_code=status.HTTP_200_OK,
# )
# async def update_property(
#     property_id: uuid.UUID,
#     property_data: PropertyUpdate,
#     current_user: CurrentUser,
#     property_service: PropertyService = Depends(get_property_service),
# ):
#     if current_user.tenant_id is None:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="You are not authorized to update a property.",
#         )
#     return await property_service.update_property(
#         property_id, property_data.model_dump(), current_user.tenant_id
#     )


# @router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_property(
#     property_id: uuid.UUID,
#     current_user: CurrentUser,
#     property_service: PropertyService = Depends(get_property_service),
# ):
#     if current_user.tenant_id is None:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="You are not authorized to delete a property.",
#         )
#     await property_service.delete_property(property_id, current_user.tenant_id)
#     return None


# @router.post("/{property_id}/images", response_model=list[PropertyPhotoResponse])
# async def upload_images(
#     property_id: uuid.UUID,
#     current_user: CurrentUser,
#     files: list[UploadFile] = File(..., description="Select max 5 property images"),
#     property_service: PropertyService = Depends(get_property_service),
# ):
#     if current_user.tenant_id is None:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="You are not authorized to upload images for a property.",
#         )
#     if len(files) > 5:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="You can only upload a maximum of 5 photos at a time.",
#         )

#     images = await property_service.upload_images(
#         property_id, files, current_user.tenant_id
#     )
#     return [
#         PropertyPhotoResponse(
#             id=image.id,
#             property_id=image.property_id,
#             photo_url=image.photo_url,
#             created_at=image.created_at,
#         )
#         for image in images
#     ]
