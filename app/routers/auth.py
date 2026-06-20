import uuid
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

# Şifreleri güvenli şekilde hash'lemek için bCrypt altyapısı
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# --- YARDIMCI FONKSİYONLAR ---

def hash_password(password: str) -> str:
    """Gelen düz metin şifreyi geri döndürülemez şekilde şifreler (Hash)."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kullanıcının girdiği şifre ile veritabanındaki hash'i karşılaştırır."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    """Kullanıcı başarılı giriş yaptığında JWT Token üretir."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

# --- 1. KAYIT OLMA (REGISTER) ENDPOINT'İ ---

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    import sqlalchemy as sa
    
    # E-posta adresi kullanımda mı kontrol et
    query = sa.select(models.User).where(models.User.email == user_data.email)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Bu e-posta adresi zaten kullanımda."
        )
    
    # Formdan gelen gerçek şifreyi hash'le
    hashed = hash_password(user_data.password)
    
    # Supabase Auth üzerinde de hesabı asıl verileriyle açıyoruz
    try:
        supabase.auth.sign_up({
            "email": user_data.email, 
            "password": user_data.password,
            "options": {
                "data": {
                    "full_name": user_data.full_name
                }
            }
        })
    except Exception:
        pass  # Supabase tarafında halihazırda varsa yerel akış kesilmesin

    # Tamamen benzersiz yeni bir UUID üretiyoruz
    generated_id = str(uuid.uuid4())

    new_user = models.User(
        id=generated_id,
        email=user_data.email,
        hashed_password=hashed,
        full_name=user_data.full_name
    )
    
    db.add(new_user)
    await db.commit()
    
    return {"status": "success", "message": "Kullanıcı başarıyla oluşturuldu."}

# --- 2. GİRİŞ YAPMA (LOGIN) ENDPOINT'İ ---

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(user_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    import sqlalchemy as sa
    
    # Kullanıcıyı e-posta ile ara
    query = sa.select(models.User).where(models.User.email == user_data.email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    # Kullanıcı yoksa veya şifre eşleşmiyorsa hata fırlat
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="E-posta veya şifre hatalı."
        )
    
    # Kullanıcı için JWT Token üret
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    
    return {
        "access_token": access_token, 
        "token_type": "bearer"
    }

# --- 3. ŞİFREMİ UNUTTUM (FORGOT PASSWORD) ENDPOINT'İ ---

class ForgotPasswordRequest(BaseModel):
    email: str

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    try:
        # Supabase istemcisi üzerinden şifre sıfırlama mailini tetikle
        supabase.auth.reset_password_for_email(
            request.email,
            {"redirect_to": "http://127.0.0.1:5500/reset-password.html"}
        )
        return {"status": "success", "message": "Şifre sıfırlama bağlantısı e-postanıza gönderildi."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Sıfırlama işlemi başlatılamadı: {str(e)}"
        )