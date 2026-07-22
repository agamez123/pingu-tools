import secrets
from typing import Optional

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session

import os
from starlette.middleware.sessions import SessionMiddleware
from passlib.context import CryptContext

from app.database import get_db
from app.models import Url, User

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

MAX_URLS_PER_USER = 10

class UrlCreateRequest(BaseModel):
    original_url: str


class UrlResponse(BaseModel):
    short_code: str
    original_url: str

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    username: str
    email: str

    class Config:
        from_attributes = True

class UserCreateRequest(BaseModel):
    email: str
    password: str
    username: str

class UserLoginRequest(BaseModel):
    email: str
    password: str

def _create_url(db: Session, original_url: str, user_id: int) -> Url:
    url_count = db.query(Url).filter(Url.user_id == user_id).count()

    if url_count > MAX_URLS_PER_USER:
        raise HTTPException(status_code=403, detail="URL LIMIT REACHED")

    short_code = secrets.token_urlsafe(6)[:8]
    url = Url(short_code=short_code, original_url=original_url, user_id=user_id)
    db.add(url)
    db.commit()
    db.refresh(url)
    return url

def _create_user(db: Session, email: str, password: str, username: str) -> User:
    hashed_password = pwd_context.hash(password)
    user = User(email=email,hashed_password=hashed_password,username=username)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def _get_url_or_404(db: Session, short_code: str) -> Url:
    url = db.query(Url).filter(Url.short_code == short_code).first()
    if url is None:
        raise HTTPException(status_code=404, detail="Short URL not found")
    return url

def _get_owned_url_or_404(db: Session, short_code: str, user_id: int) -> Url:
    url = (
        db.query(Url)
        .filter(Url.short_code == short_code, Url.user_id == user_id)
        .first()
    )
    if url is None:
        raise HTTPException(status_code=404, detail="Short URL not found")
    return url

def _get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not logged in")
    user = db.query(User).get(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Not logged in")
    return user

def _get_logged_in_user(request: Request, db: Session) -> Optional[User]:
    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    user = db.query(User).get(user_id)
    if user is None:
        request.session.clear()
        return None
    return user


@app.get("/")
def index(
    request: Request,
    created: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db),
):
    current_user = _get_logged_in_user(request, db)
    if current_user is None:
        return RedirectResponse(url="/signup")

    urls = (
        db.query(Url)
        .filter(Url.user_id == current_user.id)
        .order_by(Url.id.desc())
        .all()
    )
    created_url = None
    if created:
        created_url = (
            db.query(Url)
            .filter(Url.short_code == created, Url.user_id == current_user.id)
            .first()
        )
    return templates.TemplateResponse(
        request,
        "index.html",
        {"urls": urls, "created": created_url, "limit_reached": error == "limit"},
    )


@app.get("/settings")
def settings_page(request: Request, db: Session = Depends(get_db)):
    current_user = _get_logged_in_user(request, db)
    if current_user is None:
        return RedirectResponse(url="/signup")
    return templates.TemplateResponse(request, "settings.html", {"current_user": current_user})


@app.get("/signup")
def signup_page(request: Request, db: Session = Depends(get_db)):
    if _get_logged_in_user(request, db) is not None:
        return RedirectResponse(url="/")
    return templates.TemplateResponse(request, "signup.html", {})


@app.get("/login")
def login_page(request: Request, db: Session = Depends(get_db)):
    if _get_logged_in_user(request, db) is not None:
        return RedirectResponse(url="/")
    return templates.TemplateResponse(request, "login.html", {})


@app.post("/")
def create_short_url_form(
    original_url: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)):
    try:
        url = _create_url(db, original_url, current_user.id)
    except HTTPException as exc:
        if exc.status_code == 403:
            return RedirectResponse(url="/?error=limit", status_code=303)
        raise
    return RedirectResponse(url=f"/?created={url.short_code}", status_code=303)

@app.post("/urls", response_model=UrlResponse)
def create_short_url(
    payload: UrlCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)):
    return _create_url(db, payload.original_url, current_user.id)

@app.post("/users", response_model=UserResponse, status_code=201)
def create_user(payload: UserCreateRequest, db: Session = Depends(get_db)):
    if _get_user_by_email(db, payload.email):
        raise HTTPException(status_code=409, detail="Email already registered")
    
    return _create_user(db, payload.email, payload.password, payload.username)

@app.post("/login", status_code=200)
def login_user(payload: UserLoginRequest, request: Request, db: Session = Depends(get_db)):
    user = _get_user_by_email(db, payload.email)
    if user is None or not pwd_context.verify(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    request.session["user_id"] = user.id
    return {"message":"Logged in"}

@app.post("/logout", status_code=200)
def logout_user(request: Request):
    request.session.clear()
    return {"message": "Logged out"}
    

@app.delete("/urls/{short_code}", status_code=204)
def delete_url(
    short_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    url = _get_owned_url_or_404(db, short_code, current_user.id)
    db.delete(url)
    db.commit()


@app.post("/delete/{short_code}")
def delete_url_form(
    short_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    url = _get_owned_url_or_404(db, short_code, current_user.id)
    db.delete(url)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.post("/delete-all")
def delete_all_urls_form(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(Url).filter(Url.user_id == current_user.id).delete()
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/update/{short_code}")
def update_url_form(
    short_code: str,
    original_url: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    url = _get_owned_url_or_404(db, short_code, current_user.id)
    url.original_url = original_url
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.get("/{short_code}")
def redirect_to_original(short_code: str, db: Session = Depends(get_db)):
    url = _get_url_or_404(db, short_code)
    return RedirectResponse(url.original_url)


