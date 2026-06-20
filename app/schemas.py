from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from decimal import Decimal
from datetime import date, datetime

# --- KULLANICI (USER) ŞEMALARI ---
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    id: str  # Supabase Auth'dan dönecek UUID'yi buraya eşleyeceğiz

class UserResponse(UserBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- KATEGORİ (CATEGORY) ŞEMALARI ---
class CategoryBase(BaseModel):
    name: str
    type: str = Field(..., description="'income' veya 'expense' olmalı")
    icon: Optional[str] = "fa-wallet"

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    user_id: Optional[str]

    class Config:
        from_attributes = True


# --- İŞLEM / HAREKET (TRANSACTION) ŞEMALARI ---
class TransactionBase(BaseModel):
    category_id: Optional[int] = None
    amount: Decimal = Field(..., max_digits=10, decimal_places=2)
    type: str = Field(..., description="'income' veya 'expense' olmalı")
    description: Optional[str] = None
    transaction_date: Optional[date] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: int
    user_id: str
    created_at: datetime
    category: Optional[CategoryResponse] = None

    class Config:
        from_attributes = True


# --- TOKEN / GİRİŞ ŞEMALARI (Auth için) ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None