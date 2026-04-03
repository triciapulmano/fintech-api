from fastapi import FastAPI

from app.database import Base, engine
from app.routes import user, wallet, transaction
from app.models import User, Wallet, Transaction

app = FastAPI()

# Create table
Base.metadata.create_all(bind=engine)

# Include routes
app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(wallet.router, prefix="/wallet", tags=["Wallet"])
app.include_router(transaction.router, prefix="/transactions", tags=["Transactions"])

@app.get("/", tags=["Root"])
def root():
    return {"message": "Fintech API running"}