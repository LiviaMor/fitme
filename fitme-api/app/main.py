from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import traceback

from app.config import settings
from app.routers import analysis, health, garments, stadiometer, tryon, scan360, vectors, scan360_multi, stylist, tryon_ai

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="FITME - Provador Virtual com IA. API para análise corporal, tom de pele e consultoria de estilo.",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    print(f"❌ ERRO 500 em {request.method} {request.url}:\n{tb}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": tb},
    )

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    print(f"🚀 {settings.app_name} v{settings.app_version} iniciando...")
    print(f"📍 Ambiente: {settings.app_env}")

    # Inicializar banco (cria tabelas + extensão pgvector)
    try:
        from app.database import init_db
        await init_db()
        print("🗄️  Banco de dados inicializado (pgvector)")
    except Exception as e:
        print(f"⚠️  Banco não disponível (rode sem pgvector): {e}")


# Routers
app.include_router(health.router, tags=["Health"])
app.include_router(analysis.router, prefix="/api/v1", tags=["Análise Corporal"])
app.include_router(garments.router, prefix="/api/v1", tags=["Peças de Roupa"])
app.include_router(stadiometer.router, prefix="/api/v1", tags=["Estadiômetro Digital"])
app.include_router(tryon.router, prefix="/api/v1", tags=["Virtual Try-On"])
app.include_router(scan360.router, prefix="/api/v1", tags=["Scanner 360°"])
app.include_router(vectors.router, prefix="/api/v1", tags=["Vetores & Similaridade"])
app.include_router(scan360_multi.router, prefix="/api/v1", tags=["Scanner 360° Multi-Frame"])
app.include_router(stylist.router, prefix="/api/v1", tags=["Personal Stylist"])
app.include_router(tryon_ai.router, prefix="/api/v1", tags=["Try-On IA (IDM-VTON)"])
