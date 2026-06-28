from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File
from typing import List
from app.modules.auth.auth_middlewares import CurrentUser
from app.modules.pms.services.image_services import ImageService
from app.modules.pms.dependencies import get_image_service
from app.utils.schemas import StandardResponse
from app.utils.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)

router = APIRouter(prefix="/pms", tags=["Image"])


@router.post("/properties/images", status_code=status.HTTP_201_CREATED, response_model=StandardResponse[List[str]])
async def upload_images(
    user: CurrentUser,
    files: List[UploadFile] = File(...),
    image_service:ImageService = Depends(get_image_service),
):
    logger.info(f"[ImageRouter] Uploading images")
    
    if user.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not authorized to upload images. You must belong to an active tenant.",
        )

    # 1. Enforce payload array count boundaries
    if len(files) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bulk upload constraint violation: Maximum allowed limit is 5 files per request.",
        )

    # 2. Enforce explicit image mime-type checking before starting file read routines
    for file in files:
        if not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"File '{file.filename}' is invalid. Only valid image media files are accepted.",
            )
     
    uploaded_image_urls = await image_service.upload_property_images(folder_name=f"properties/{user.tenant_id}", files=files)
    
    return {
        "success":True,
        "data":uploaded_image_urls
    }

# @router.post("/properties/rooms/images", status_code=status.HTTP_201_CREATED, response_model=StandardResponse[List[str]])
# async def upload_room_images(
#     user: CurrentUser,
#     files: List[UploadFile] = File(...),
#     image_service:ImageService = Depends(get_image_service),
# ):
#     logger.info(f"[ImageRouter] Uploading images")
    
#     if user.tenant_id is None:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="You are not authorized to upload images. You must belong to an active tenant.",
#         )

#     # 1. Enforce payload array count boundaries
#     if len(files) > 5:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Bulk upload constraint violation: Maximum allowed limit is 5 files per request.",
#         )

#     # 2. Enforce explicit image mime-type checking before starting file read routines
#     for file in files:
#         if not file.content_type.startswith("image/"):
#             raise HTTPException(
#                 status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#                 detail=f"File '{file.filename}' is invalid. Only valid image media files are accepted.",
#             )
     
#     uploaded_image_urls = await image_service.upload_property_images(folder_name=f"properties/{user.tenant_id}", files=files)
    
#     return {
#         "success":True,
#         "data":uploaded_image_urls
#     }