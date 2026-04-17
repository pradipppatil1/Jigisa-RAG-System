from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
import logging

from app.core.database import get_db
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.config.settings import settings
from app.auth.schemas import LoginRequest, TokenResponse, RegisterRequest, CurrentUser
from app.auth.utils import verify_password, create_access_token, get_password_hash, create_refresh_token, create_csrf_token
from app.auth.service import ROLE_COLLECTIONS_MAP
from app.auth.dependencies import get_current_user, require_role

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """Authenticate user and return a JWT containing RBAC payload via Cookies."""
    user = db.query(User).filter(User.username == request.username).first()
    
    if not user or not verify_password(request.password, user.password):
        logger.warning(f"Failed login attempt for username: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password."
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is disabled."
        )

    # Resolve allowed collections from role
    collections = ROLE_COLLECTIONS_MAP.get(user.role, [])

    # JWT Payload
    token_data = {
        "sub": user.username,
        "user_id": user.id,
        "role": user.role,
        "department": user.department,
        "collections": collections
    }

    access_token = create_access_token(data=token_data)
    
    # Generate Refresh & CSRF Tokens
    refresh_token = create_refresh_token()
    csrf_token = create_csrf_token()
    
    # Save Refresh Token to Database
    family = str(user.id) + "-" + refresh_token[:8] # Simple family correlation
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRY_DAYS)
    
    db_token = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        family=family,
        expires_at=expires_at
    )
    db.add(db_token)
    db.commit()

    # Set Strict Cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.JWT_EXPIRY_MINUTES * 60
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRY_DAYS * 24 * 3600
    )
    
    # Set CSRF Token cookie (NOT HttpOnly so JS can read it for headers)
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=True,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRY_DAYS * 24 * 3600
    )
    
    logger.info(f"Successful login and cookie provisioning for user: {user.username} (Role: {user.role})")
    
    return TokenResponse(
        access_token=access_token,
        user=CurrentUser(
            user_id=user.id,
            username=user.username,
            role=user.role,
            collections=collections,
            department=user.department
        )
    )

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    """Validates HTTP-only refresh cookie to issue new access & refresh tokens."""
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
        
    db_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
    
    if not db_token:
        # Token not found: potential tampering, force clean.
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        response.delete_cookie("csrf_token")
        raise HTTPException(status_code=401, detail="Invalid refresh token")
        
    if db_token.is_revoked:
        # Token Reuse Detected: Alert! Revoke all family tokens.
        db.query(RefreshToken).filter(RefreshToken.family == db_token.family).update({"is_revoked": True})
        db.commit()
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        response.delete_cookie("csrf_token")
        raise HTTPException(status_code=401, detail="Compromised refresh token.")
        
    if db_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        response.delete_cookie("csrf_token")
        raise HTTPException(status_code=401, detail="Refresh token expired")

    user = db_token.user

    # Token Rotation: Revoke old token
    db_token.is_revoked = True
    
    # Issue New Tokens
    new_refresh = create_refresh_token()
    new_expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRY_DAYS)
    
    new_db_token = RefreshToken(
        user_id=user.id,
        token=new_refresh,
        family=db_token.family,
        expires_at=new_expires_at
    )
    db.add(new_db_token)
    db.commit()

    collections = ROLE_COLLECTIONS_MAP.get(user.role, [])
    token_data = {
        "sub": user.username,
        "user_id": user.id,
        "role": user.role,
        "department": user.department,
        "collections": collections
    }

    new_access = create_access_token(data=token_data)

    response.set_cookie(key="access_token", value=new_access, httponly=True, secure=True, samesite="lax", max_age=settings.JWT_EXPIRY_MINUTES * 60)
    response.set_cookie(key="refresh_token", value=new_refresh, httponly=True, secure=True, samesite="lax", max_age=settings.REFRESH_TOKEN_EXPIRY_DAYS * 24 * 3600)

    return TokenResponse(
        access_token=new_access,
        user=CurrentUser(
            user_id=user.id,
            username=user.username,
            role=user.role,
            collections=collections,
            department=user.department
        )
    )

@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    """Clears HTTP-only cookies and revokes refresh token."""
    token = request.cookies.get("refresh_token")
    if token:
        db_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
        if db_token:
            db_token.is_revoked = True
            db.commit()
            
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    response.delete_cookie("csrf_token")
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=CurrentUser)
def get_me(current_user: CurrentUser = Depends(get_current_user)):
    """Returns the current user profile from the JWT."""
    return current_user


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(
    request: RegisterRequest, 
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(require_role(["c_level"]))  # MUST BE C-LEVEL TO REGISTER OTHERS
):
    """Admin-only endpoint to register a new user."""
    # Ensure username / email is unique
    if db.query(User).filter(User.username == request.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
        
    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = get_password_hash(request.password)
    
    new_user = User(
        username=request.username,
        email=request.email,
        password=hashed_pw,
        role=request.role,
        department=request.department
    )
    
    try:
        db.add(new_user)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database Error")
    
    logger.info(f"Admin {admin.username} successfully registered new user {request.username}")
    
    return {"message": "User successfully registered", "username": request.username}
