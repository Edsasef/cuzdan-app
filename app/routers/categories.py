from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import sqlalchemy as sa
from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/categories",
    tags=["Categories (Kategoriler)"]
)

# --- 1. KATEGORİLERİ LİSTELEME ENDPOINT'İ ---
@router.get("/", response_model=List[schemas.CategoryResponse])
async def get_categories(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Kullanıcının görebileceği kategorileri listeler.
    Hem genel (user_id IS NULL) kategorileri hem de kullanıcının kendine özel eklediği kategorileri getirir.
    """
    query = sa.select(models.Category).where(
        sa.or_(
            models.Category.user_id == None,
            models.Category.user_id == user_id
        )
    )
    result = await db.execute(query)
    return result.scalars().all()


# --- 2. YENİ KATEGORİ OLUŞTURMA ENDPOINT'İ ---
@router.post("/", response_model=schemas.CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(user_id: str, category_data: schemas.CategoryCreate, db: AsyncSession = Depends(get_db)):
    """Kullanıcıya özel yeni bir gelir/gider kategorisi oluşturur."""
    
    # Aynı isimde ve aynı tipte kategori daha önce eklenmiş mi kontrol et
    query = sa.select(models.Category).where(
        models.Category.user_id == user_id,
        models.Category.name == category_data.name,
        models.Category.type == category_data.type
    )
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu isimde bir kategoriyi daha önce zaten eklediniz."
        )
        
    new_category = models.Category(
        user_id=user_id,
        name=category_data.name,
        type=category_data.type,
        icon=category_data.icon
    )
    
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    return new_category