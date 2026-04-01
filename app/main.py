from fastapi import FastAPI
from app.database import Base, engine
from app.routes import user

app = FastAPI()

# Create table
Base.metadata.create_all(bind=engine)

# Include routes
app.include_router(user.router, prefix="/users", tags=["Users"])

@app.get("/")
def root():
    return {"message": "Fintech API running"}