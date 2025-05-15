from fastapi import BackgroundTasks
from fastapi import HTTPException, status
from app.email_utils import send_verification_email
from fastapi import APIRouter, Depends, Request, Form, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models import User
from jose import jwt, JWTError
from datetime import datetime, timedelta
import bcrypt
import os

router = APIRouter(prefix="/users", tags=["Users"])
templates = Jinja2Templates(directory="app/templates")

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# Load secrets
SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key").encode("utf-8")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))


@router.get("/login")
def show_login_page(request: Request, message: str = ""):
    return templates.TemplateResponse("login.html", {"request": request, "message": message})


@router.post("/login")
async def login(email: str = Form(...), password: str = Form(...), db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not bcrypt.checkpw(password.encode(), user.hashed_password.encode()):
        return RedirectResponse(url="/users/login?message=Invalid%20credentials", status_code=303)

    if not user.is_verified:
        return RedirectResponse(url="/users/login?message=Please%20verify%20your%20email%20before%20login", status_code=303)

    token = jwt.encode(
        {"sub": user.email, "user_id": user.id, "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="Lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return response


@router.get("/register")
def show_register_page(request: Request, message: str = ""):
    return templates.TemplateResponse("register.html", {"request": request, "message": message})


@router.post("/register")
async def register(
background_tasks: BackgroundTasks,
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

    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    new_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        is_verified=False
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    token_data = {
        "sub": new_user.email,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    verification_link = f"{BASE_URL}/users/verify?token={token}"

    background_tasks.add_task(send_verification_email, to_email=new_user.email, verification_link=verification_link)

    return RedirectResponse(
        url="/users/login?message=Account%20created.%20Please%20check%20your%20email%20to%20verify%20your%20account.",
        status_code=303
    )


@router.get("/logout")
def logout(response: Response):
    response = RedirectResponse(url="/users/login", status_code=303)
    response.delete_cookie("access_token")
    return response


@router.get("/verify")
async def verify_user(token: str, db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            return {"error": "Invalid token"}

        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalars().first()

        if not user:
            return {"error": "User not found"}

        user.is_verified = True
        await db.commit()

        return RedirectResponse(url="/users/login?message=Account verified! Please login.")
    except Exception:
        return {"error": "Verification failed or token expired"}

@router.post("/change-password")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_new_password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    # Extract user info from your session or cookie (depends on your auth flow)
    # Example assumes you extract email from JWT in cookie:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    stmt = select(User).where(User.email == user_email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify current password
    if not bcrypt.checkpw(current_password.encode(), user.hashed_password.encode()):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    # Check if new passwords match
    if new_password != confirm_new_password:
        raise HTTPException(status_code=400, detail="New passwords do not match")

    # Hash new password
    hashed_new_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    user.hashed_password = hashed_new_password

    await db.commit()

    return RedirectResponse(url="/dashboard?message=Password%20changed%20successfully", status_code=303)
