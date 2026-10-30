"""Authentication and user management service."""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status

from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User, UserRole
from app.models.profile import FarmerProfile, BuyerProfile, FPOProfile, TraderProfile
from app.schemas.user import UserRegister, UserLogin


class AuthService:
    """Service for authentication and user management."""

    @staticmethod
    def register(db: Session, data: UserRegister) -> User:
        """Register a new user."""
        # Check for existing email or phone
        existing = db.query(User).filter(
            or_(
                User.email == data.email,
                (User.phone == data.phone) if data.phone else False,
            )
        ).first()

        if existing:
            if existing.email == data.email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this email already exists",
                )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this phone number already exists",
            )

        # Create user
        user = User(
            email=data.email,
            phone=data.phone,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            role=UserRole(data.role),
            language_pref=data.language_pref,
        )
        db.add(user)
        db.flush()

        # Create role-specific profile
        if data.role == "farmer":
            profile = FarmerProfile(user_id=user.id)
            db.add(profile)
        elif data.role == "buyer":
            profile = BuyerProfile(user_id=user.id)
            db.add(profile)
        elif data.role == "fpo_admin":
            profile = FPOProfile(user_id=user.id, org_name=data.full_name + " FPO")
            db.add(profile)
        elif data.role == "trader":
            profile = TraderProfile(user_id=user.id)
            db.add(profile)

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate(db: Session, data: UserLogin) -> tuple[User, str]:
        """Authenticate a user and return user + access token."""
        user = db.query(User).filter(User.email == data.email).first()

        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )

        # Update last login
        user.last_login = datetime.now(timezone.utc)
        db.commit()

        # Create token
        token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
        return user, token

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def update_user(db: Session, user: User, updates: dict) -> User:
        """Update user fields."""
        for key, value in updates.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def change_password(db: Session, user: User, current_password: str, new_password: str) -> bool:
        """Change user's password."""
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )
        user.password_hash = hash_password(new_password)
        db.commit()
        return True
