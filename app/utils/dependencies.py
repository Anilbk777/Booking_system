from typing import Annotated
from fastapi import Depends, HTTPException
from app.config.database_config import get_db
from app.repository.users_repo import UserRepository
from app.services.user_service import UserService
from app.core.auth import oauth2_scheme, verify_access_token
from app.models.users_model import UserModel


async def get_user_repository(db=Depends(get_db)):
    return UserRepository(db)


async def get_user_service(user_repository=Depends(get_user_repository)):
    return UserService(user_repository)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(get_user_service),
):
    user_id = verify_access_token(token)
    if not user_id:
        raise HTTPException(
            status_code=401, detail="Invalid authentication credentials"
        )
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=401, detail="Invalid authentication credentials"
        )
    return user


CurrentUser = Annotated[UserModel, Depends(get_current_user)]
