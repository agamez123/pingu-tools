import secrets

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Url

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")


class UrlCreateRequest(BaseModel):
    original_url: str


class UrlResponse(BaseModel):
    short_code: str
    original_url: str

    class Config:
        from_attributes = True


def _create_url(db: Session, original_url: str) -> Url:
    short_code = secrets.token_urlsafe(6)[:8]
    url = Url(short_code=short_code, original_url=original_url)
    db.add(url)
    db.commit()
    db.refresh(url)
    return url


@app.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    urls = db.query(Url).order_by(Url.id.desc()).all()
    return templates.TemplateResponse(
        request, "index.html", {"urls": urls, "created": None}
    )


@app.post("/")
def create_short_url_form(
    request: Request,
    original_url: str = Form(...),
    db: Session = Depends(get_db),
):
    url = _create_url(db, original_url)
    urls = db.query(Url).order_by(Url.id.desc()).all()
    return templates.TemplateResponse(
        request, "index.html", {"urls": urls, "created": url}
    )


@app.post("/urls", response_model=UrlResponse)
def create_short_url(payload: UrlCreateRequest, db: Session = Depends(get_db)):
    return _create_url(db, payload.original_url)


@app.get("/{short_code}")
def redirect_to_original(short_code: str, db: Session = Depends(get_db)):
    url = db.query(Url).filter(Url.short_code == short_code).first()
    if url is None:
        raise HTTPException(status_code=404, detail="Short URL not found")
    return RedirectResponse(url.original_url)
