from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from src.db.session import get_db_session
from src.services.auth_service import AuthService
from src.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")

# dependency to authenticate token (used in routers)
def authenticate_user_token(token: str = Depends(oauth2_scheme)):
    # we cannot import get_db_session directly here because we need a session object in the call
    # The routers that use this will instead create AuthService with the session and call authenticate_token
    raise NotImplementedError("Use auth helpers inside routers with db session and AuthService")
