from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas import UserCreate, UserRead, Token, TokenData
from app.services.auth import verify_password, create_access_token
from app.services.db_service import get_user_by_email, create_user
from app.api.deps import get_current_user

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/token", response_model=Token)
async def login(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, user_in.email)
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token({"sub": str(user.id)})
    return Token(access_token=access_token)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    user = await create_user(db, user_in)
    return user


@router.get("/me", response_model=UserRead)
async def me(user=Depends(get_current_user)):
    return user