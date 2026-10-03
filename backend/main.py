"""
EcoNITH — AI-Powered Campus Environmental Management for NIT Hamirpur
Main application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import BACKEND_HOST, BACKEND_PORT, FRONTEND_URL, STATIC_DIR, DEMO_MODE
from database import init_db, seed_data
from routes import router

# Initialize database on startup
init_db()
seed_data()

app = FastAPI(
    title="EcoNITH API",
    description="AI-Powered Campus Environmental Management for NIT Hamirpur",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (uploads, charts, maps)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# API routes
app.include_router(router)


@app.get("/")
async def root():
    return {
        "service": "EcoNITH — Campus Environmental Management",
        "institution": "NIT Hamirpur, Himachal Pradesh",
        "version": "1.0.0",
        "demo_mode": DEMO_MODE,
        "docs": "/docs",
        "health": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn
    print(f"""
    ╔══════════════════════════════════════════════╗
    ║  🌿 EcoNITH — NIT Hamirpur Environment AI   ║
    ║  Mode: {"DEMO" if DEMO_MODE else "PRODUCTION":^38s}║
    ║  URL: http://{BACKEND_HOST}:{BACKEND_PORT:<26}║
    ║  Docs: http://{BACKEND_HOST}:{BACKEND_PORT}/docs{" " * 17}║
    ╚══════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host=BACKEND_HOST, port=BACKEND_PORT)
