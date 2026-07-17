import secrets

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Url

app = FastAPI()


class UrlCreateRequest(BaseModel):
    original_url: str


class UrlResponse(BaseModel):
    short_code: str
    original_url: str

    class Config:
        from_attributes = True


@app.post("/urls", response_model=UrlResponse)
def create_short_url(payload: UrlCreateRequest, db: Session = Depends(get_db)):
    short_code = secrets.token_urlsafe(6)[:8]
    url = Url(short_code=short_code, original_url=payload.original_url)
    db.add(url)
    db.commit()
    db.refresh(url)
    return url


@app.get("/{short_code}")
def redirect_to_original(short_code: str, db: Session = Depends(get_db)):
    url = db.query(Url).filter(Url.short_code == short_code).first()
    if url is None:
        raise HTTPException(status_code=404, detail="Short URL not found")
    return RedirectResponse(url.original_url)
