"""Admin API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.listing import CropListing, ListingStatus
from app.models.offer import Offer, OfferStatus
from app.models.deal_room import DealRoom
from app.models.agreement import Agreement
from app.models.transaction import Transaction
from app.models.support import SupportTicket
from app.models.audit import AuditLog
from app.models.notification import Notification

router = APIRouter()


@router.get("/dashboard")
def admin_dashboard(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Get admin dashboard analytics."""
    return {
        "users": {
            "total": db.query(User).count(),
            "farmers": db.query(User).filter(User.role == UserRole.FARMER).count(),
            "buyers": db.query(User).filter(User.role == UserRole.BUYER).count(),
            "fpo_admins": db.query(User).filter(User.role == UserRole.FPO_ADMIN).count(),
            "active": db.query(User).filter(User.is_active == True).count(),
        },
        "listings": {
            "total": db.query(CropListing).count(),
            "active": db.query(CropListing).filter(CropListing.status == ListingStatus.ACTIVE).count(),
            "sold": db.query(CropListing).filter(CropListing.status == ListingStatus.SOLD).count(),
        },
        "offers": {
            "total": db.query(Offer).count(),
            "pending": db.query(Offer).filter(Offer.status == OfferStatus.PENDING).count(),
            "accepted": db.query(Offer).filter(Offer.status == OfferStatus.ACCEPTED).count(),
        },
        "deal_rooms": db.query(DealRoom).count(),
        "agreements": db.query(Agreement).count(),
        "transactions": db.query(Transaction).count(),
        "support_tickets": {
            "total": db.query(SupportTicket).count(),
            "open": db.query(SupportTicket).filter(SupportTicket.status == "open").count(),
        },
    }


@router.get("/users")
def list_users(
    role: str = Query(None),
    is_active: bool = Query(None),
    q: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """List all users with filters."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == UserRole(role))
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if q:
        search = f"%{q}%"
        query = query.filter(
            (User.full_name.ilike(search)) | (User.email.ilike(search))
        )

    total = query.count()
    users = query.order_by(User.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()

    return {
        "items": [
            {
                "id": u.id, "email": u.email, "full_name": u.full_name,
                "role": u.role.value, "is_active": u.is_active,
                "is_verified": u.is_verified, "created_at": u.created_at.isoformat(),
                "last_login": u.last_login.isoformat() if u.last_login else None,
            }
            for u in users
        ],
        "total": total, "page": page, "page_size": page_size,
    }


@router.patch("/users/{user_id}")
def update_user_admin(
    user_id: int,
    is_active: bool = Query(None),
    is_verified: bool = Query(None),
    role: str = Query(None),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Admin update of user status."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot modify your own admin account this way")

    if is_active is not None:
        user.is_active = is_active
    if is_verified is not None:
        user.is_verified = is_verified
    if role:
        user.role = UserRole(role)

    # Audit log
    log = AuditLog(
        user_id=current_user.id,
        action="admin.user_update",
        resource_type="user",
        resource_id=user_id,
        details=f"Updated: is_active={is_active}, is_verified={is_verified}, role={role}",
    )
    db.add(log)
    db.commit()

    return {"detail": "User updated", "user_id": user_id}


@router.get("/audit-logs")
def get_audit_logs(
    action: str = Query(None),
    user_id: int = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """View audit logs."""
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()

    return {
        "items": [
            {
                "id": l.id, "user_id": l.user_id, "action": l.action,
                "resource_type": l.resource_type, "resource_id": l.resource_id,
                "details": l.details, "created_at": l.created_at.isoformat(),
            }
            for l in logs
        ],
        "total": total,
    }
