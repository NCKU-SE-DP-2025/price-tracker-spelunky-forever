from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from src.schemas.user import UserAuthSchema, TokenResponse
from src.repositories.user_repository import UserRepository
from src.core.config import settings
from src.db.session import get_db_session
from src.services.auth_service import AuthService
from src.api.deps import pwd_context, oauth2_scheme
from datetime import timedelta

router = APIRouter()

@router.post("/register")
def create_user(user: UserAuthSchema, db=Depends(get_db_session)):
    hashed_password = pwd_context.hash(user.password)
    user_repo = UserRepository(db)
    db_user = user_repo.create_user(user.username, hashed_password)
    return {"id": db_user.id, "username": db_user.username}

@router.post("/login")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db_session)):
    # reproduce original helper get_user_if_password_correct
    user_repo = UserRepository(db)
    user = user_repo.get_by_username(form_data.username)
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    auth_service = AuthService(db, secret_key=settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    access_token = auth_service.create_access_token(data={"sub": str(user.username)}, expires_delta=timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
def read_users_me(token: str = Depends(oauth2_scheme), db=Depends(get_db_session)):
    auth_service = AuthService(db, secret_key=settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    current_user = auth_service.authenticate_token(token)
    return {"username": current_user.username}
