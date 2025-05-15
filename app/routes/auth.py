from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models import User
from jose import jwt
from requests_oauthlib import OAuth2Session
from dotenv import load_dotenv
import os

router = APIRouter()

# ✅ Load Environment Variables
load_dotenv()  # Ensure environment variables are loaded
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# ✅ Debugging Print Statements
print(f"✅ GOOGLE_CLIENT_ID Loaded: {bool(GOOGLE_CLIENT_ID)}")
print(f"✅ REDIRECT_URI Loaded: {REDIRECT_URI}")
print(f"✅ SECRET_KEY Loaded: {bool(SECRET_KEY)}")
print(f"✅ ALGORITHM Loaded: {ALGORITHM}")

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Allow HTTP for local development


@router.get("/auth/google")
def google_login():
    print("✅ Initiating Google OAuth2 Login")
    oauth = OAuth2Session(
        client_id=GOOGLE_CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile"
        ],
    )
    authorization_url, state = oauth.authorization_url(
        "https://accounts.google.com/o/oauth2/auth",
        access_type="offline",
        prompt="consent"
    )
    print(f"✅ Redirecting to Google: {authorization_url}")
    return RedirectResponse(authorization_url)


@router.get("/auth/google/callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            print("❌ Google OAuth credentials not properly loaded.")
            return RedirectResponse("/users/login?message=Google%20OAuth%20configuration%20error")

        # ✅ Initialize OAuth2 Session here (not globally)
        oauth = OAuth2Session(
            client_id=GOOGLE_CLIENT_ID,
            redirect_uri=REDIRECT_URI,
            scope=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile"
            ],
        )

        print(f"✅ Google OAuth Callback URL: {request.url}")

        token = oauth.fetch_token(
            "https://oauth2.googleapis.com/token",
            client_secret=GOOGLE_CLIENT_SECRET,
            authorization_response=str(request.url)
        )
        print(f"✅ Access Token: {token}")

        user_info = oauth.get("https://www.googleapis.com/oauth2/v1/userinfo").json()
        print(f"✅ User Info from Google: {user_info}")

        email = user_info.get("email")
        if not email:
            return RedirectResponse("/users/login?message=Google%20Login%20Failed")

        # ✅ Check if user exists in the database
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalars().first()

        # ✅ Create new user if not found
        if not user:
            new_user = User(
                username=user_info.get("name"),
                email=email,
                hashed_password="",  # No password for Google users
                is_verified=True
            )
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            user = new_user

        # ✅ Generate JWT Token
        access_token = jwt.encode({"sub": user.email, "user_id": user.id}, SECRET_KEY, algorithm=ALGORITHM)

        # ✅ Redirect Only After Setting the Cookie
        response = RedirectResponse(url="/dashboard")
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            samesite="Lax",
            secure=False  # Change to True for HTTPS in production
        )
        print("✅ User logged in with Google successfully.")
        return response

    except Exception as e:
        print(f"❌ Error during Google OAuth: {str(e)}")
        return RedirectResponse("/users/login?message=Google%20Login%20Failed")