from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # 1. Import this
from app.db.base import Base
from app.db.session import engine
from app.api.v1.endpoints import router as api_router
from app.models.lead_magnet import LeadMagnet, Lead 

Base.metadata.create_all(bind=engine)

app = FastAPI(title="GenieOps Lead Magnet Engine")

# 2. Add this block to allow React to talk to your API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # The React URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def health_check():
    return {"status": "Backend is online", "database": "Connected"}