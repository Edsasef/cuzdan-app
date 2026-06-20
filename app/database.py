from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings
from supabase import create_client, Client

# Supabase PostgreSQL linkimizi asenkron yapıya uyarlıyoruz
DATABASE_URL = settings.DATABASE_URL
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

# Asenkron Veritabanı Motoru
engine = create_async_engine(DATABASE_URL, pool_pre_ping=True, echo=False)

# Veritabanı Oturum Fabrikası
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# Dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# --- SUPABASE AUTH / CLIENT ENTEGRASYONU ---
# O alandaki her şeyi sil ve YERİNE SADECE BU 4 SATIRI YAPIŞTIR:

SUPABASE_URL = "https://psoqdrasppeugrslphdx.supabase.co"
SUPABASE_KEY = "sb_publishable_kRdd3_Op6eFgOETkbs7bMw_kDOQx..." # Supabase panelinden kopyaladığın o uzun anahtarı buraya yapıştır

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

if not SUPABASE_URL.startswith("http"):
    # Eğer url otomatik ayıklanamadıysa temiz bir fallback
    SUPABASE_URL = "https://your-supabase-project.supabase.co" 

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)