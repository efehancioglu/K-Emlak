from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from contextlib import asynccontextmanager

from app.core.database import get_db
from app.core.scheduler import scheduler_baslat, scheduler_durdur
from app.routers import listings, scraper, valuation



@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler_baslat()
    yield
    scheduler_durdur()


app = FastAPI(title="K-Emlak API", lifespan=lifespan)

app.include_router(listings.router)
app.include_router(scraper.router)
app.include_router(valuation.router)

@app.get("/")
def read_root():
    return {"message" : "K-Emlak API calisiyor"}

@app.get("/health")
def health_check(db:Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status" : "ok", "database" : "connected"}

