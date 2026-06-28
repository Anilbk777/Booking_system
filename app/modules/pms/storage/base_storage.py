import uuid
import aiofiles
import asyncio
import cloudinary.uploader
from abc import ABC, abstractmethod
from pathlib import Path
from dotenv import load_dotenv
import os
from app.utils.logging import LoggerFactory
from app.utils.exceptions import ImageStorageException

load_dotenv()

logger = LoggerFactory.get_logger(__name__)

class ImageStorageStrategy(ABC):
    @abstractmethod
    async def save_image(self, folder_name: str, image_bytes: bytes) -> str:
        pass


class LocalImageStorage(ImageStorageStrategy):
    def __init__(self, base_path: str = "static/uploads"):
        self.base_path = Path(base_path)

    async def save_image(self, folder_name: str, image_bytes: bytes) -> str:
        logger.info(f"[LocalImageStorage] Saving image in {folder_name} folder")
        filename = f"{uuid.uuid4().hex}.webp"
        target_dir = self.base_path / folder_name
        
        # Ensure the specific folder (e.g., 'properties' or 'users') exists
        target_dir.mkdir(parents=True, exist_ok=True)
        filepath = target_dir / filename

        # Asynchronously write the bytes to disk
        try:
            async with aiofiles.open(filepath, 'wb') as out_file:
                await out_file.write(image_bytes)
            logger.info(f"[LocalImageStorage] Image saved successfully at {filepath}")
            return f"/{self.base_path.name}/{folder_name}/{filename}"
        except Exception as e:
            logger.error(f"Error saving image to disk: {str(e)}")
            raise ImageStorageException("Error saving image to disk", f"Error saving image to disk: {str(e)}")


class CloudinaryImageStorage(ImageStorageStrategy):
    def __init__(self):
        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET"),
            secure=True,
        )
    
    async def save_image(self, folder_name: str, image_bytes: bytes) -> str:
        # Cloudinary's upload is synchronous and involves network I/O.
        # We offload it to a thread so it doesn't block the FastAPI event loop.
        logger.info(f"[CloudinaryImageStorage] Uploading image to Cloudinary in {folder_name} folder")
        try:
            def _upload_to_cloudinary():
                return cloudinary.uploader.upload(
                    image_bytes,
                    folder=folder_name,
                    resource_type="image",
                    format="webp"
                )

            response = await asyncio.to_thread(_upload_to_cloudinary)
            
            secure_url = response.get("secure_url")
            if not secure_url:
                raise ValueError("Cloudinary response did not contain a valid secure_url parameter field.")
                
            logger.info(f"[CloudinaryImageStorage] Image uploaded successfully to Cloudinary at {secure_url}")
            return secure_url
        except Exception as e:
            logger.error(f"Error uploading image to Cloudinary: {str(e)}")
            raise ImageStorageException("Error uploading image to Cloudinary", f"Error uploading image to Cloudinary: {str(e)}")


class StorageFactory:
    @staticmethod
    def get_storage() -> ImageStorageStrategy:
        """
        Returns the appropriate storage strategy based on the provider string.
        """
        provider = os.getenv("IMAGE_STORAGE_PROVIDER", "local")
        provider_clean = provider.strip().lower()
        
        if provider_clean == "local":
            logger.info("[StorageFactory] Using Local Storage")
            return LocalImageStorage()
        elif provider_clean == "cloudinary":
            logger.info("[StorageFactory] Using Cloudinary Storage")
            return CloudinaryImageStorage()
        else:
            raise ValueError(f"Unsupported storage provider: {provider}")