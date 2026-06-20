from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, categories, transactions

app = FastAPI(
    title="CüzdanAPP API",
    description="Kişisel Bütçe ve Finans Yönetimi Backend Servisi",
    version="1.0.0"
)

# --- CORS AYARLARI ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTERS (ROTALAR) ---
app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(transactions.router)

# --- İLK AÇILIŞTA VERİTABANI TABLOLARINI OLUŞTURMA ---
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# --- İLK TEST ENDPOINT'İ ---
@app.get("/")
def read_root():
    return {
        "status": "success",
        "message": "CüzdanAPP Backend API başarıyla çalışıyor!",
        "version": "1.0.0"
    }