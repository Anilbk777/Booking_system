from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select, func
from app.modules.pms.models.discount_code_model import DiscountCode
from app.utils.logging import LoggerFactory
from app.utils.exceptions import RepositoryException
import uuid

logger = LoggerFactory.get_logger(__name__)
class DiscountCodeRepository:
    def __init__(self, db:AsyncSession):
        self.db = db

    async def get_discount_code(self,property_id:uuid.UUID, code:str) -> DiscountCode:
        logger.info(f"[DiscountCodeRepository] Checking existence for code '{code}' under property {property_id}")
    
        try:
            # 1. Clean and normalize the text variable input
            clean_code = code.strip().upper()
            
            # 2. Build the query to fetch the full row entity matching your target rules
            stmt = select(DiscountCode).where(
                and_(
                    DiscountCode.property_id == property_id,
                    func.upper(DiscountCode.code) == clean_code
                )
            )
            
            # 3. Execute the statement asynchronously against the DB connection pool
            result = await self.db.execute(stmt)
            db_discount = result.scalar_one_or_none()
            return db_discount

        except Exception as e:
            logger.error(f"[DiscountCodeRepository] Error getting discount code: {str(e)}")
            raise RepositoryException(
                "Failed to get the discount code",
                f"Error getting discount code: {str(e)}"
            )

    async def get_discount_code_by_id(self,property_id:uuid.UUID,discount_id:uuid.UUID)->DiscountCode:
        logger.info(f"[DiscountCodeRepository] get for code '{discount_id}' under property {property_id}")
        try:
            stmt = select(DiscountCode).where(
                and_(
                    DiscountCode.property_id == property_id,
                    DiscountCode.id == discount_id
                )
            )
            result = await self.db.execute(stmt)
            db_discount = result.scalar_one_or_none()
            return db_discount
        except Exception as e:
            logger.error(f"[DiscountCodeRepository] Error getting discount code: {str(e)}")
            raise RepositoryException(
                "Failed to get the discount code",
                f"Error getting discount code: {str(e)}"
            )

    async def create_discount_code(self,discount_code:dict) -> DiscountCode:
        logger.info(f"[DiscountCodeRepository] Creating discount code")
        
        try:
            new_discount_code = DiscountCode(**discount_code)
            self.db.add(new_discount_code)

            await self.db.flush()
            return new_discount_code
        except Exception as e:
            logger.error(f"[DiscountCodeRepository] Error creating discount code: {str(e)}")
            raise RepositoryException(
                "Failed to create the discount code",
                f"Error creating discount code: {str(e)}"
            )
    
    async def get_all_discount_codes(self,property_id:uuid.UUID)->list[DiscountCode]:
        logger.info(f"[DiscountCodeRepository] Fetching all discount codes for property {property_id}")
        try:
            stmt = select(DiscountCode).where(
                DiscountCode.property_id == property_id
            )
            result = await self.db.execute(stmt)
            db_discount_codes = result.scalars().all()
            return db_discount_codes
        except Exception as e:
            logger.error(f"[DiscountCodeRepository] Error fetching discount codes: {str(e)}")
            raise RepositoryException(
                "Failed to fetch discount codes",
                f"Error fetching discount codes: {str(e)}"
            )
