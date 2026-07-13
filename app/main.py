from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.routers import listings

app = FastAPI(title="K-Emlak API")

app.include_router(listings.router)

@app.get("/")
def read_root():
    return {"message" : "K-Emlak API calisiyor"}

@app.get("/health")
def health_check(db:Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status" : "ok", "database" : "connected"}

