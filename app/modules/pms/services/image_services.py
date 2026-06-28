import asyncio
from fastapi import UploadFile
from app.utils.imgae_utils import process_image
from app.modules.pms.storage.base_storage import StorageFactory
from app.utils.exceptions import ServiceException, ImageStorageException, InvalidImageException
from app.utils.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)

class ImageService:
    def __init__(self):
        self.provider = StorageFactory.get_storage()

    async def upload_property_images(self, folder_name:str, files:list[UploadFile]) -> list[str]:
        try:
            tasks = [self._process_and_upload_single(folder_name=folder_name, file=file) for file in files]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            uploaded_urls = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error uploading image: {str(result)}")
                    raise ServiceException(f"Failed to process one or more images: {str(result)}")
                else:
                    uploaded_urls.append(result)
            return uploaded_urls
        except (InvalidImageException,ImageStorageException, ValueError):
            raise
        except Exception as e:
            logger.error(f"Error processing or uploading images: {str(e)}")
            raise ServiceException(f"Error processing or uploading images: {str(e)}")

    async def _process_and_upload_single(self,folder_name:str,file:UploadFile) -> str:
        try:
            raw_bytes = await file.read()

            optimized_webp_bytes = await asyncio._to_thread(process_image, raw_bytes)

            saved_url = await self.provider.save_image(
                folder_name=folder_name,
                image_bytes=optimized_webp_bytes
            )

            logger.info(f"[ImageService] Image uploaded successfully to: {saved_url}")
            return saved_url
        except (InvalidImageException,ImageStorageException, ValueError):
            raise
        except Exception as e:
            logger.error(f"Error processing or uploading image: {str(e)}")
            raise ServiceException(f"Error processing or uploading image: {str(e)}")
        finally:
            await file.close()
            