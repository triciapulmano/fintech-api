from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer 
import logging

from app.database import Base, engine
from app.routes import wallet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

security = HTTPBearer()

app = FastAPI(
    title="Wallet Service",
    description="Microservice for wallet management",
    version="1.0.0",
    swagger_ui_init_oauth={}
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(wallet.router, prefix="/wallet", tags=["Wallet"])

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "wallet-service"}

@app.get("/", tags=["Root"])
def root():
    return {"message": "Wallet Service running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)