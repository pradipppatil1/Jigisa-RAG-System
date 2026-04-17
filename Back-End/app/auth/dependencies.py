from fastapi import Depends, HTTPException, status, Request
import jwt

from app.config.settings import settings
from app.auth.schemas import CurrentUser
from app.auth.utils import ALGORITHM


def get_current_user(request: Request) -> CurrentUser:
    """
    Dependency that extracts access_token from HttpOnly cookies.
    Enforces strict anti-CSRF matching on mutation HTTP methods.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    
    token = request.cookies.get("access_token")
    if not token:
        raise credentials_exception
        
    # Enforce CSRF validation for any state-changing HTTP request
    if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
        header_csrf = request.headers.get("X-CSRF-Token")
        cookie_csrf = request.cookies.get("csrf_token")
        if not header_csrf or not cookie_csrf or header_csrf != cookie_csrf:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token validation failed, potential attack mitigated.")

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
            detail="Token has expired"
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
