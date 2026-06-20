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
# settings içinde SUPABASE_URL ve SUPABASE_ANON_KEY tanımlıysa oradan çeker, yoksa DATABASE_URL tabanını dener
SUPABASE_URL = getattr(settings, "SUPABASE_URL", settings.DATABASE_URL.split("@")[1].split(":")[0] if "@" in settings.DATABASE_URL else "")
# Eğer ayarlarda yoksa buraya doğrudan Supabase panelindeki url ve anon_key'ini tırnak içinde gömebilirsin.
SUPABASE_KEY = getattr(settings, "SUPABASE_ANON_KEY", "SENIN_SUPABASE_ANON_KEYIN")

if not SUPABASE_URL.startswith("http"):
    # Eğer url otomatik ayıklanamadıysa temiz bir fallback
    SUPABASE_URL = "https://your-supabase-project.supabase.co" 

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)