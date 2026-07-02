import uuid
from app.modules.pms.repositories.discount_code_repo import DiscountCodeRepository
from app.modules.pms.schemas.discount_code_schema import DiscountCodeCreate , DiscountCodeResponse

from app.utils.logging import LoggerFactory
from app.utils.exceptions import ServiceException,RepositoryException,DiscountCodeAlreadyExistException,DiscountCodeNotFoundException

# from app.modules.pms.models.discount_code_model import DiscountCode

logger = LoggerFactory.get_logger(__name__)

class DiscountCodeService:
    def __init__(self,discount_code_repo:DiscountCodeRepository):
        self.discount_code_repo = discount_code_repo

    async def _exists_by_code(self, property_id: uuid.UUID, code: str) -> bool:
        logger.info(f"[DiscountCodeService] Checking existence for code '{code}' under property {property_id}")

        try: 
            db_discount = await self.discount_code_repo.get_discount_code(property_id, code)
            if db_discount:
                return True
            return False
        except RepositoryException:
            raise

        except Exception as e:
            logger.error(f"[DiscountCodeService] Error checking existence: {str(e)}")
            raise ServiceException(str(e))

    async def create_discount_code(self, property_id:uuid.UUID, payload:DiscountCodeCreate):
        logger.info(f"[DiscountCodeService] Commencing registration process for property: {property_id}")
        discount_code_data = payload.model_dump()
        discount_code_data["property_id"] = property_id

        try:
            exists = await self._exists_by_code(property_id, discount_code_data["code"])
            if exists:
                logger.warning(f"[DiscountCodeService] Validation rejected. '{discount_code_data['code']}' already exists under property scope '{property_id}'.")
                raise DiscountCodeAlreadyExistException(f"Discount code '{discount_code_data['code']}' already exists.")
            
            # 2. Delegate insertion processing task to the repository layer
            result = await self.discount_code_repo.create_discount_code(discount_code_data)
            
            # 3. Commit transaction on the DB session managed by the service block context
            await self.discount_code_repo.db.commit()
            await self.discount_code_repo.db.refresh(result)
            
            logger.info(f"[DiscountCodeService] Discount code registered and committed successfully.")
            return DiscountCodeResponse.model_validate(result)
            
        except (DiscountCodeAlreadyExistException, RepositoryException) as e:
            await self.discount_code_repo.db.rollback()
            logger.error(f"[DiscountCodeService] Failed to create discount code: {str(e)}")
            raise

        except Exception as e:
            await self.discount_code_repo.db.rollback()
            logger.error(f"[DiscountCodeService] Critical failure encountered during creation: {str(e)}")
            raise ServiceException(f"An unexpected internal error occurred: {str(e)}")

    async def get_all_discount_codes(self,property_id:uuid.UUID):
        logger.info(f"[DiscountCodeService] Fetching all discount codes for property: {property_id}")
        try:
            all_discount_codes = await self.discount_code_repo.get_all_discount_codes(property_id)
            return [DiscountCodeResponse.model_validate(discount_code) for discount_code in all_discount_codes]
        except RepositoryException:
            raise
        except Exception as e:
            logger.error(f"[DiscountCodeService] Error fetching discount codes: {str(e)}")
            raise ServiceException(str(e))
            
    
    async def get_discount_code(self,property_id:uuid.UUID,discount_id:uuid.UUID):
        logger.info(f"[DiscountCodeService] Fetching discount code for property: {property_id} and discount code: {discount_id}")
        try:
            db_discount = await self.discount_code_repo.get_discount_code_by_id(property_id,discount_id)
            if not db_discount:
                logger.info(f"[DiscountCodeService] Discount code '{discount_id}' not found for property: {property_id}")
                raise DiscountCodeNotFoundException(f"Discount code '{discount_id}' not found for property: {property_id}")

            logger.info(f"[DiscountCodeService] Discount code '{discount_id}' fetched successfully for property: {property_id}")
            return DiscountCodeResponse.model_validate(db_discount)

        except (DiscountCodeNotFoundException,RepositoryException) as e:
            raise
        except Exception as e:
            logger.error(f"[DiscountCodeService] Error fetching discount code: {str(e)}")
            raise ServiceException(f"An unexpected internal error occurred: {str(e)}")
        
