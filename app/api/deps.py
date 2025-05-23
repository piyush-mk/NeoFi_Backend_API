from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_password
from app.db.session import SessionLocal
from app.db.models import User, Event, EventPermission, UserRole
from app.schemas.user import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = db.query(User).filter(User.id == token_data.sub).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def check_event_permission(
    db: Session,
    event_id: int,
    user_id: int,
    required_role: UserRole = UserRole.VIEWER,
) -> bool:
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Owner has all permissions
    if event.owner_id == user_id:
        return True
    
    # Check user's permission
    permission = (
        db.query(EventPermission)
        .filter(
            EventPermission.event_id == event_id,
            EventPermission.user_id == user_id,
        )
        .first()
    )
    
    if not permission:
        return False
    
    # Role hierarchy: OWNER > EDITOR > VIEWER
    role_hierarchy = {
        UserRole.OWNER: 3,
        UserRole.EDITOR: 2,
        UserRole.VIEWER: 1,
    }
    
    return role_hierarchy[permission.role] >= role_hierarchy[required_role]


def get_event_with_permission(
    db: Session = Depends(get_db),
    event_id: int = None,
    current_user: User = Depends(get_current_active_user),
    required_role: UserRole = UserRole.VIEWER,
) -> Event:
    if not check_event_permission(db, event_id, current_user.id, required_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event 