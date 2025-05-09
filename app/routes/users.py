from fastapi import APIRouter, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import APIRouter, Depends, Request, Form, Response
from app.database import get_db
from app.models import User
from jose import jwt, JWTError
from datetime import datetime, timedelta
import bcrypt
import os

router = APIRouter(prefix="/users", tags=["Users"])
templates = Jinja2Templates(directory="app/templates")

# ✅ Load Secret Key and Algorithm Securely
SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key").encode("utf-8")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))


# ✅ Login Page
@router.get("/login")
def show_login_page(request: Request, message: str = ""):
    return templates.TemplateResponse("login.html", {"request": request, "message": message})


# ✅ Login Function (Redirects to Dashboard)
@router.post("/login")
async def login(
        email: str = Form(...),
        password: str = Form(...),
        db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not bcrypt.checkpw(password.encode(), user.hashed_password.encode()):
        return RedirectResponse(url="/users/login?message=Invalid%20credentials", status_code=303)

    # ✅ Generate JWT (Includes user_id for better security)
    token = jwt.encode(
        {"sub": user.email, "user_id": user.id, "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    # ✅ Redirect to Dashboard with Secure Cookie
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,  # Prevent JavaScript access (XSS protection)
        samesite="Lax",  # CSRF Protection
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Set expiration time in seconds
    )
    return response


# ✅ Register Page
@router.get("/register")
def show_register_page(request: Request, message: str = ""):
    return templates.TemplateResponse("register.html", {"request": request, "message": message})


# ✅ Register Function (POST)
@router.post("/register")
async def register(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    existing_user = result.scalars().first()

    if existing_user:
        return RedirectResponse(url="/users/register?message=Email%20already%20registered", status_code=303)

    # ✅ Hash Password Securely with Bcrypt
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    # ✅ Create New User
    new_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        is_verified=True  # Set this to False if you want email verification
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return RedirectResponse(url="/users/login?message=Account%20created.%20Please%20login.", status_code=303)

@router.get("/logout")
def logout(response: Response):
    response = RedirectResponse(url="/users/login", status_code=303)
    response.delete_cookie("access_token")
    return response