from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from typing import List
import sqlalchemy as sa
from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions (Gelir/Gider Hareketleri)"]
)

# --- 1. TÜM İŞLEMLERİ LİSTELEME ENDPOINT'İ ---
@router.get("/", response_model=List[schemas.TransactionResponse])
async def get_transactions(user_id: str, db: AsyncSession = Depends(get_db)):
    """Kullanıcının yaptığı tüm gelir ve gider hareketlerini geçmişe göre sıralı listeler."""
    # joinedload(models.Transaction.category) sayesinde işleme ait kategori detaylarını (isim, ikon) otomatik çekeriz.
    query = (
        sa.select(models.Transaction)
        .where(models.Transaction.user_id == user_id)
        .options(joinedload(models.Transaction.category))
        .order_by(models.Transaction.transaction_date.desc(), models.Transaction.created_at.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()


# --- 2. YENİ GELİR/GİDER EKLEME ENDPOINT'İ ---
@router.post("/", response_model=schemas.TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(user_id: str, transaction_data: schemas.TransactionCreate, db: AsyncSession = Depends(get_db)):
    """Kullanıcının cüzdanına yeni bir gelir veya gider hareketi kaydeder."""
    
    # Eğer kategori ID'si gönderildiyse, veritabanında böyle bir kategori gerçekten var mı kontrol et
    if transaction_data.category_id:
        cat_query = sa.select(models.Category).where(models.Category.id == transaction_data.category_id)
        cat_result = await db.execute(cat_query)
        category = cat_result.scalar_one_or_none()
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seçilen kategori bulunamadı."
            )
            
    new_transaction = models.Transaction(
        user_id=user_id,
        category_id=transaction_data.category_id,
        amount=transaction_data.amount,
        type=transaction_data.type,
        description=transaction_data.description,
        transaction_date=transaction_data.transaction_date
    )
    
    db.add(new_transaction)
    await db.commit()
    await db.refresh(new_transaction)
    
    # Kategori ilişkisini de yükleyip frontend'e eksiksiz detay dönmek için tekrar sorguluyoruz
    query = (
        sa.select(models.Transaction)
        .where(models.Transaction.id == new_transaction.id)
        .options(joinedload(models.Transaction.category))
    )
    res = await db.execute(query)
    return res.scalar_one()