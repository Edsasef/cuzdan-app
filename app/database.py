from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# Supabase PostgreSQL linkimizi asenkron yapıya uyarlıyoruz.
# Eğer link postgresql:// ile başlıyorsa, SQLAlchemy asenkron motoru için bunu postgresql+asyncpg:// yapmalıyız.
DATABASE_URL = settings.DATABASE_URL
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

# Asenkron Veritabanı Motoru (Engine) Oluşturma
# pool_pre_ping=True sayesinde düşen bağlantılar otomatik olarak yenilenir, Vercel'de kopma yaşanmaz.
engine = create_async_engine(DATABASE_URL, pool_pre_ping=True, echo=False)

# Veritabanı Oturum Fabrikası (Sessionmaker)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Tablolarımızı türeteceğimiz ana Base sınıfı
Base = declarative_base()

# FastAPI endpoint'lerinde veritabanı bağlantısını güvenli açıp kapatmak için Dependency (Bağımlılık)
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()