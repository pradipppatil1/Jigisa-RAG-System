from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt

from app.config.settings import settings
from app.auth.schemas import CurrentUser
from app.auth.utils import ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    """
    Dependency that decodes the JWT token and returns the CurrentUser.
    Raises HTTPException 401 if invalid/expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        username: str = payload.get("sub")
        role: str = payload.get("role")
        collections: list[str] = payload.get("collections", [])
        department: str = payload.get("department")

        if username is None or role is None or user_id is None:
            raise credentials_exception

        return CurrentUser(
            user_id=user_id,
            username=username,
            role=role,
            collections=collections,
            department=department
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError: # Catch all PyJWT decoding errors
        raise credentials_exception


def require_role(allowed_roles: list[str]):
    """
    Dependency factory to enforce RBAC based on the user's role from JWT.
    Usage: Depends(require_role(["c_level", "finance"]))
    """
    def role_checker(current_user: CurrentUser = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {allowed_roles}"
            )
        return current_user

    return role_checker
