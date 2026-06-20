import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Yerel geliştirme için .env dosyasını yükle
load_dotenv()

class Settings(BaseSettings):
    # Supabase Ayarları
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    
    # Güvenlik ve JWT Ayarları (Giriş/Kayıt için)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "bunu_daha_sonra_degistirebilirsin_cok_gizli_anahtar")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 Günlük Oturum Süresi

settings = Settings()