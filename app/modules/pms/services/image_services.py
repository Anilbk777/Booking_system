import asyncio
from fastapi import UploadFile
from app.utils.imgae_utils import process_image
from app.modules.pms.storage.base_storage import StorageFactory
from app.utils.exceptions import (
    ServiceException,
    ImageStorageException,
    InvalidImageException,
)
from app.utils.logging import LoggerFactory
import re

logger = LoggerFactory.get_logger(__name__)


class ImageService:
    def __init__(self):
        self.provider = StorageFactory.get_storage()

    async def upload_property_images(
        self, folder_name: str, files: list[UploadFile]
    ) -> list[str]:

        try:
            tasks = [
                self._process_and_upload_single(folder_name=folder_name, file=file)
                for file in files
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            uploaded_urls = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error uploading image: {str(result)}")
                    raise ServiceException(
                        f"Failed to process one or more images: {str(result)}"
                    )
                else:
                    uploaded_urls.append(result)
            return uploaded_urls
        except (InvalidImageException, ImageStorageException, ValueError):
            raise
        except Exception as e:
            logger.error(f"Error processing or uploading images: {str(e)}")
            raise ServiceException(f"Error processing or uploading images: {str(e)}")

    async def _process_and_upload_single(
        self, folder_name: str, file: UploadFile
    ) -> str:
        try:
            raw_bytes = await file.read()

            optimized_webp_bytes = await asyncio.to_thread(process_image, raw_bytes)

            saved_url = await self.provider.save_image(
                folder_name=folder_name, image_bytes=optimized_webp_bytes
            )

            logger.info(f"[ImageService] Image uploaded successfully to: {saved_url}")
            return saved_url
        except (InvalidImageException, ImageStorageException, ValueError):
            raise
        except Exception as e:
            logger.error(f"Error processing or uploading image: {str(e)}")
            raise ServiceException(f"Error processing or uploading image: {str(e)}")
        finally:
            await file.close()

    def extract_fake_id_from_public_id(self, public_id: str, segment: str) -> str:
        """
        public_id looks like:
            "temp/properties/9f3a1c2e-8b21-4a11-9c3d-1719999999/wtjpjac0dcyqv3epr5l6"

        We want the folder segment right after "{segment}":
            "9f3a1c2e-8b21-4a11-9c3d-1719999999"
        """
        parts = public_id.split("/")

        try:
            idx = parts.index(segment)
        except ValueError:
            raise ValueError(f"'{segment}' segment not found in public_id: {public_id}")

        if idx + 1 >= len(parts):
            raise ValueError(
                f"No folder segment after '{segment}' in public_id: {public_id}"
            )

        return parts[idx + 1]

    def extract_public_id_from_url(self, url: str) -> str:
        # https://res.cloudinary.com/<cloud>/image/upload/v1782893339/test/properties/.../file.webp
        try:
            after_upload = url.split("/upload/", 1)[1]
            # after_upload = "v1782893339/test/properties/.../wtjpjac0dcyqv3epr5l6.webp"

            # strip the leading version segment (v followed by digits)
            segments = after_upload.split("/", 1)
            if segments[0].startswith("v") and segments[0][1:].isdigit():
                after_upload = segments[1]

            # strip the file extension
            return re.sub(r"\.[^/.]+$", "", after_upload)
        except Exception as e:
            raise InvalidImageException(
                internal_detail=f"Invalid URL format: {url} , error occured {str(e)}"
            )

    def extract_fake_property_id_from_url(self, url: str) -> str:
        return self.extract_fake_property_id_from_public_id(
            self.extract_public_id_from_url(url)
        )
