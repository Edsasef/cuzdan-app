from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from app.database import get_db
from app.config import settings
from app import models, schemas

router = APIRouter(
    prefix="/auth",
    tags=["Authentication (Giriş/Kayıt)"]
)

# Şifreleri hash'lemek için bCrypt altyapısını hazırlıyoruz
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Frontend'den token'ı alabilmek için standart OAuth2 yapısı
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# --- YARDIMCI FONKSİYONLAR ---

def hash_password(password: str) -> str:
    """Gelen düz metin şifreyi geri döndürülemez şekilde şifreler (Hash)."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kullanıcının girdiği şifre ile veritabanındaki hash'i karşılaştırır."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    """Kullanıcı başarılı giriş yaptığında 1 gün geçerli JWT Token üretir."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# --- KAYIT OLMA (REGISTER) ENDPOINT'İ ---

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    # 1. Bu e-posta adresiyle daha önce kayıt olunmuş mu kontrol et
    import sqlalchemy as sa
    query = sa.select(models.User).where(models.User.email == user_data.email)
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu e-posta adresi zaten kullanımda."
        )
    
    # 2. Yeni kullanıcıyı oluştur (Şifreleme Supabase Auth tarafında veya doğrudan backend'de yönetilebilir, 
    # şimdilik şemadan gelen UUID ve email ile kullanıcımızı yerel tablomuza işliyoruz)
    new_user = models.User(
        id=user_data.id,
        email=user_data.email
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user

# --- GİRİŞ YAPMA (LOGIN) ENDPOINT'İ ---

@router.post("/login", response_model=schemas.Token)
async def login(user_data: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    import sqlalchemy as sa
    # 1. Kullanıcı veritabanımızda var mı kontrol et
    query = sa.select(models.User).where(models.User.id == user_data.id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    # 2. Eğer kullanıcı henüz veritabanımızda yoksa (Supabase Auth ile ilk kez giriş yapıyorsa)
    # onu otomatik olarak 'users' tablomuza kaydet (Sorunsuz bir senkronizasyon için)
    if not user:
        user = models.User(
            id=user_data.id,
            email=user_data.email
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    # 3. Kullanıcı için 1 gün geçerli JWT Token üret
    access_token = create_access_token(data={"sub": user.id, "email": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }