from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from dotenv import load_dotenv
from app.database import get_db
from app.models import User
from app.routes.users import router as users_router
from app.routes.auth import router as auth_router
import os

# ✅ Load environment variables
load_dotenv(".env")

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

# ✅ Load JWT Configurations with Debugging
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
REDIRECT_URI = os.getenv("REDIRECT_URI")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# ✅ Debugging Print Statements
print(f"✅ SECRET_KEY Loaded: {bool(SECRET_KEY)}")
print(f"✅ ALGORITHM Loaded: {ALGORITHM}")
print(f"✅ REDIRECT_URI Loaded: {REDIRECT_URI}")
print(f"✅ GOOGLE_CLIENT_ID Loaded: {GOOGLE_CLIENT_ID}")

# ✅ Validate Critical Configurations
if not SECRET_KEY:
    raise ValueError("❌ SECRET_KEY not loaded. Make sure it's set in your .env file.")
if not ALGORITHM:
    raise ValueError("❌ ALGORITHM not loaded. Make sure it's set in your .env file.")

# ✅ Include Routers
app.include_router(users_router)
app.include_router(auth_router)

# ✅ Redirect the home route to the login page
@app.get("/", response_class=RedirectResponse)
def home():
    return RedirectResponse(url="/users/login", status_code=307)


# ✅ Secure Dashboard Route (JWT Protected)
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/users/login?message=Please%20log%20in", status_code=307)

    try:
        # ✅ Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            return RedirectResponse(url="/users/login?message=Invalid%20session.%20Please%20log%20in%20again", status_code=307)

        # ✅ Fetch User from Database
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalars().first()
        if not user:
            return RedirectResponse(url="/users/login?message=User%20not%20found", status_code=307)

        # ✅ Pass User to Template
        return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

    except JWTError:
        return RedirectResponse(url="/users/login?message=Session%20Expired.%20Please%20log%20in%20again", status_code=307)

# ✅ Logout Route (Clears JWT Cookie)
@app.get("/logout", response_class=RedirectResponse)
def logout():
    response = RedirectResponse(url="/users/login?message=Logged%20out%20successfully")
    response.delete_cookie("access_token")
    print("✅ User logged out successfully.")
    return response
