from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.backend.database.database import get_db
from app.backend.models.models import User
from app.backend.services.security import verify_token
from app.backend.services.user_service import UserService
from typing import Optional


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)


def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Optional[User]:
    if not token:
        return None

    try:
        payload = verify_token(token)
        if payload is None:
            return None

        username: str = payload.get("sub")
        if username is None:
            return None

        user_service = UserService(db)
        user = user_service.get_user_by_username(username)
        if user is None:
            return None

        return user
    except Exception:
        return None
