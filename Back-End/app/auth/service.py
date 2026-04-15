import logging
from sqlalchemy.orm import Session

from app.models.user import User
from app.auth.utils import get_password_hash

logger = logging.getLogger(__name__)

# Consistent role mapping for Qdrant Collections
ROLE_COLLECTIONS_MAP = {
    "employee":    ["general"],
    "finance":     ["general", "finance"],
    "engineering": ["general", "engineering"],
    "marketing":   ["general", "marketing"],
    "c_level":     ["general", "finance", "engineering", "marketing"],
}

DEMO_USERS = [
    {
        "username": "emp_user",
        "email": "emp@finsolve.com",
        "password": "emp123",
        "role": "employee",
        "department": "General",
    },
    {
        "username": "fin_user",
        "email": "fin@finsolve.com",
        "password": "fin123",
        "role": "finance",
        "department": "Finance",
    },
    {
        "username": "eng_user",
        "email": "eng@finsolve.com",
        "password": "eng123",
        "role": "engineering",
        "department": "Engineering",
    },
    {
        "username": "mkt_user",
        "email": "mkt@finsolve.com",
        "password": "mkt123",
        "role": "marketing",
        "department": "Marketing",
    },
    {
        "username": "ceo_user",
        "email": "ceo@finsolve.com",
        "password": "ceo123",
        "role": "c_level",
        "department": "Executive",
    },
]


def seed_demo_users(db: Session) -> None:
    """Ensure predefined demo users exist in the database."""
    for user_data in DEMO_USERS:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == user_data["username"]).first()
        if not existing_user:
            hashed_pw = get_password_hash(user_data["password"])
            new_user = User(
                username=user_data["username"],
                email=user_data["email"],
                password=hashed_pw,
                role=user_data["role"],
                department=user_data["department"]
            )
            db.add(new_user)
            logger.info("Seeded demo user: %s", user_data["username"])
    
    try:
        db.commit()
    except Exception as e:
        logger.error("Failed to sequence users: %s", str(e))
        db.rollback()
