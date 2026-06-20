from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from app.database import get_db, supabase
from app.config import settings
from app import models, schemas
from pydantic import BaseModel

router = APIRouter(
    prefix="/auth",
    tags=["Authentication (Giriş/Kayıt)"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

# --- KAYIT OLMA (REGISTER) ---
@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    import sqlalchemy as sa
    query = sa.select(models.User).where(models.User.email == user_data.email)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kullanımda.")
    
    new_user = models.User(id=user_data.id, email=user_data.email)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

# --- GİRİŞ YAPMA (LOGIN) ---
@router.post("/login", response_model=schemas.Token)
async def login(user_data: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    import sqlalchemy as sa
    query = sa.select(models.User).where(models.User.id == user_data.id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        user = models.User(id=user_data.id, email=user_data.email)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    access_token = create_access_token(data={"sub": user.id, "email": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# --- ŞİFREMİ UNUTTUM (FORGOT PASSWORD) ---
class ForgotPasswordRequest(BaseModel):
    email: str

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    try:
        supabase.auth.reset_password_for_email(
            request.email,
            {"redirect_to": "http://127.0.0.1:5500/reset-password.html"}
        )
        return {"status": "success", "message": "Şifre sıfırlama bağlantısı e-postanıza gönderildi."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"E-posta gönderilirken bir hata oluştu: {str(e)}"
        )