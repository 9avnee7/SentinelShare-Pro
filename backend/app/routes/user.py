# app/routes/user.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Form, Request, Response
from sqlalchemy.orm import Session
from .. import models, schemas, database, auth
from fastapi.security import OAuth2PasswordRequestForm
import os
from jose import JWTError, jwt
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/user", tags=["Users"])
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "defaultsecret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
environment=os.getenv("environment","development")


secureCheck=environment=="production"
flexibility="Strict"


# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=schemas.RegisterResponse)
def register(response: Response, user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        logger.info(f"Attempting registration for email: {user.email}")
        existing = db.query(models.User).filter(models.User.email == user.email).first()
        if existing:
            logger.warning(f"Registration failed: Email {user.email} already registered")
            raise HTTPException(status_code=400, detail="Email already registered")

        secret = auth.generate_2fa_secret()
        new_user = models.User(
            email=user.email,
            hashed_password=auth.hash_password(user.password),
            twofa_secret=secret,
            role=user.role
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        totp_uri = auth.get_totp_uri(user.email, secret)
        access_token = auth.create_access_token(data={"sub": user.email})
        refresh_token = auth.create_refresh_token(data={"sub": user.email})

        response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=secureCheck,samesite=flexibility)
        response.set_cookie(key="access_token", value=access_token, httponly=True, secure=secureCheck,samesite=flexibility)

        logger.info(f"User registered successfully: {user.email}")
        return {
            "refresh_token": refresh_token,
            "access_token": access_token,
            "totp_uri": totp_uri,
            "user_info": {
                "email": new_user.email,
                "role": new_user.role
            }
        }

    except Exception as e:
        logger.exception(f"Error during registration: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/login", response_model=schemas.LoginResponse)
def login(response: Response, username: str = Form(...), password: str = Form(...), twofa_code: str = Form(...), db: Session = Depends(get_db)):
    try:
        logger.info(f"Login attempt: {username}")
        user = db.query(models.User).filter(models.User.email == username).first()
        if not user or not auth.verify_password(password, user.hashed_password):
            logger.warning(f"Login failed for {username}: Invalid credentials")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not auth.verify_totp(user.twofa_secret, twofa_code):
            logger.warning(f"Login failed for {username}: Invalid 2FA code")
            raise HTTPException(status_code=401, detail="Invalid 2FA code")

        access_token = auth.create_access_token(data={"sub": user.email})
        refresh_token = auth.create_refresh_token(data={"sub": user.email})

        response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=secureCheck,samesite=flexibility)
        response.set_cookie(key="access_token", value=access_token, httponly=True, secure=secureCheck,samesite=flexibility)

        logger.info(f"User logged in: {username}")
        return {
            "refresh_token": refresh_token,
            "access_token": access_token,
            "user_info": {
                "email": user.email,
                "role": user.role
            }
        }

    except Exception as e:
        logger.exception(f"Error during login: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/logout")
async def logout(response: Response):
    try:
        response.delete_cookie(key="access_token", path="/")
        response.delete_cookie(key="refresh_token", path="/")
        logger.info("User logged out successfully")
        return {"message": "Successfully logged out"}
    except Exception as e:
        logger.exception(f"Error during logout: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/refresh")
def refresh_token(response: Response, request: Request, db: Session = Depends(get_db)):
    try:
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            logger.warning("Refresh token not found in cookies")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token found")

        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        if not user_email:
            logger.warning("Refresh token payload missing 'sub'")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

        user = db.query(models.User).filter(models.User.email == user_email).first()
        if not user:
            logger.warning(f"User not found for refresh token email: {user_email}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        new_access_token = auth.create_access_token(data={"sub": user.email})
        new_refresh_token = auth.create_refresh_token(data={"sub": user.email})

        response.set_cookie(key="refresh_token", value=new_refresh_token, httponly=True, secure=secureCheck,samesite=flexibility)
        response.set_cookie(key="access_token", value=new_access_token, httponly=True, secure=secureCheck,samesite=flexibility)

        logger.info(f"Token refreshed for user: {user.email}")
        return {
            "access_token": new_access_token,
            "user_info": {
                "email": user.email,
                "role": user.role
            }
        }

    except JWTError as e:
        logger.warning(f"JWT decode error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    except Exception as e:
        logger.exception(f"Error during token refresh: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/login/google")
async def login_with_google(data: dict, response: Response, db: Session = Depends(get_db)):
    try:
        logger.info("Google login attempt")
        token = data.get("token")
        if not token:
            logger.warning("Google login failed: Token not provided")
            raise HTTPException(status_code=400, detail="Token is required")

        idinfo = id_token.verify_oauth2_token(token, google_requests.Request())
        email = idinfo.get('email')
        if not email:
            logger.warning("Google login failed: Email not found in token")
            raise HTTPException(status_code=400, detail="Email not found in token")

        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            user = models.User(
                email=email,
                hashed_password="",
                twofa_secret=None,
                role="user"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"New user created via Google login: {email}")
        else:
            logger.info(f"Existing Google user logged in: {email}")

        access_token = auth.create_access_token(data={"sub": email})
        refresh_token = auth.create_refresh_token(data={"sub": email})

        response.set_cookie("access_token", access_token, httponly=True,secure=secureCheck,samesite=flexibility)
        response.set_cookie("refresh_token", refresh_token, httponly=True,secure=secureCheck,samesite=flexibility)

        return {
            "access_token": access_token,
            "user_info": {
                "email": user.email,
                "role": user.role
            }
        }

    except ValueError:
        logger.warning("Invalid Google OAuth2 token")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.exception(f"Error during Google login: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


