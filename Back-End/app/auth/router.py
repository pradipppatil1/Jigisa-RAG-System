from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from app.core.database import get_db
from app.models.user import User
from app.auth.schemas import LoginRequest, TokenResponse, RegisterRequest, CurrentUser
from app.auth.utils import verify_password, create_access_token, get_password_hash
from app.auth.service import ROLE_COLLECTIONS_MAP
from app.auth.dependencies import get_current_user, require_role

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return a JWT containing RBAC payload."""
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
    
    logger.info(f"Successful login for user: {user.username} (Role: {user.role})")
    
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
