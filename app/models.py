from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True) # Supabase Auth UUID'si string olarak tutulacak
    email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # İlişkiler: Bir kullanıcının birden fazla işlemi ve kategorisi olabilir
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True) # Null ise herkesin kullanabileceği varsayılan kategoridir
    name = Column(String, nullable=False)
    type = Column(String, nullable=False) # 'income' (gelir) veya 'expense' (gider)
    icon = Column(String, default="fa-wallet") # Arayüzde responsive panelde gösterilecek ikon kodu

    # İlişkiler
    user = relationship("User", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    amount = Column(Numeric(10, 2), nullable=False) # Kuruşlu hassas finansal veri için Numeric
    type = Column(String, nullable=False) # 'income' veya 'expense'
    description = Column(Text, nullable=True)
    transaction_date = Column(Date, default=datetime.utcnow().date)
    created_at = Column(DateTime, default=datetime.utcnow)

    # İlişkiler
    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")