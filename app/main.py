import secrets
from typing import Optional

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Url

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
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


def _get_url_or_404(db: Session, short_code: str) -> Url:
    url = db.query(Url).filter(Url.short_code == short_code).first()
    if url is None:
        raise HTTPException(status_code=404, detail="Short URL not found")
    return url


@app.get("/")
def index(request: Request, created: Optional[str] = None, db: Session = Depends(get_db)):
    urls = db.query(Url).order_by(Url.id.desc()).all()
    created_url = None
    if created:
        created_url = db.query(Url).filter(Url.short_code == created).first()
    return templates.TemplateResponse(
        request, "index.html", {"urls": urls, "created": created_url}
    )


@app.post("/")
def create_short_url_form(original_url: str = Form(...), db: Session = Depends(get_db)):
    url = _create_url(db, original_url)
    return RedirectResponse(url=f"/?created={url.short_code}", status_code=303)

@app.post("/urls", response_model=UrlResponse)
def create_short_url(payload: UrlCreateRequest, db: Session = Depends(get_db)):
    return _create_url(db, payload.original_url)


@app.delete("/urls/{short_code}", status_code=204)
def delete_url(short_code: str, db: Session = Depends(get_db)):
    url = _get_url_or_404(db, short_code)
    db.delete(url)
    db.commit()


@app.post("/delete/{short_code}")
def delete_url_form(short_code: str, db: Session = Depends(get_db)):
    url = _get_url_or_404(db, short_code)
    db.delete(url)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.post("/update/{short_code}")
def update_url_form(
    short_code: str,
    original_url: str = Form(...),
    db: Session = Depends(get_db),
):
    url = _get_url_or_404(db, short_code)
    url.original_url = original_url
    db.commit()
    return RedirectResponse(url="/", status_code=303)



@app.get("/{short_code}")
def redirect_to_original(short_code: str, db: Session = Depends(get_db)):
    url = _get_url_or_404(db, short_code)
    return RedirectResponse(url.original_url)

