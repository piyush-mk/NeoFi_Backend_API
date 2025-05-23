from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi.encoders import jsonable_encoder

from app.api.deps import (
    get_db,
    get_current_active_user,
    get_event_with_permission,
    check_event_permission,
)
from app.db.models import User, Event, EventPermission, EventVersion, EventChangeLog, UserRole
from app.schemas.event import (
    Event as EventSchema,
    EventCreate,
    EventUpdate,
    EventPermission as EventPermissionSchema,
    EventPermissionCreate,
    EventPermissionUpdate,
    EventVersion as EventVersionSchema,
    EventChangeLog as EventChangeLogSchema,
    EventDiff,
)

router = APIRouter()


@router.post("", response_model=EventSchema)
def create_event(*, db: Session = Depends(get_db), event_in: EventCreate, current_user: User = Depends(get_current_active_user)) -> Any:
    conflicting_events = db.query(Event).filter(
        and_(
            or_(
                and_(Event.start_time <= event_in.start_time, Event.end_time > event_in.start_time),
                and_(Event.start_time < event_in.end_time, Event.end_time >= event_in.end_time),
            ),
            Event.owner_id == current_user.id,
        )
    ).all()
    if conflicting_events:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Time conflict with existing events")
    event = Event(**event_in.model_dump(), owner_id=current_user.id)
    db.add(event)
    db.commit()
    db.refresh(event)
    event_dict = jsonable_encoder(event)
    version = EventVersion(
        event_id=event.id,
        version_number=1,
        data=event_dict,
        created_by=current_user.id,
        change_description="Initial version",
    )
    db.add(version)
    db.commit()
    event.version_number = 1
    return event


@router.get("", response_model=List[EventSchema])
def list_events(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user), skip: int = 0, limit: int = 100) -> Any:
    events = (
        db.query(Event)
        .filter(
            or_(
                Event.owner_id == current_user.id,
                Event.id.in_(db.query(EventPermission.event_id).filter(EventPermission.user_id == current_user.id)),
            )
        )
        .offset(skip)
        .limit(limit)
        .all()
    )
    for event in events:
        latest_version = (
            db.query(EventVersion)
            .filter(EventVersion.event_id == event.id)
            .order_by(EventVersion.version_number.desc())
            .first()
        )
        event.version_number = latest_version.version_number if latest_version else 1
    return events


@router.get("/{event_id}", response_model=EventSchema)
def get_event(*, db: Session = Depends(get_db), event_id: int, current_user: User = Depends(get_current_active_user)) -> Any:
    event = get_event_with_permission(db, event_id, current_user)
    latest_version = (
        db.query(EventVersion)
        .filter(EventVersion.event_id == event.id)
        .order_by(EventVersion.version_number.desc())
        .first()
    )
    event.version_number = latest_version.version_number if latest_version else 1
    return event


@router.put("/{event_id}", response_model=EventSchema)
def update_event(*, db: Session = Depends(get_db), event_id: int, event_in: EventUpdate, current_user: User = Depends(get_current_active_user)) -> Any:
    event = get_event_with_permission(db, event_id, current_user, required_role=UserRole.EDITOR)
    if event_in.start_time or event_in.end_time:
        start_time = event_in.start_time or event.start_time
        end_time = event_in.end_time or event.end_time
        conflicting_events = db.query(Event).filter(
            and_(
                or_(
                    and_(Event.start_time <= start_time, Event.end_time > start_time),
                    and_(Event.start_time < end_time, Event.end_time >= end_time),
                ),
                Event.id != event_id,
                Event.owner_id == current_user.id,
            )
        ).all()
        if conflicting_events:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Time conflict with existing events")
    current_version = (
        db.query(EventVersion)
        .filter(EventVersion.event_id == event_id)
        .order_by(EventVersion.version_number.desc())
        .first()
    )
    update_data = event_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)
    db.add(event)
    db.commit()
    db.refresh(event)
    new_version_number = current_version.version_number + 1 if current_version is not None else 1
    new_version = EventVersion(
        event_id=event_id,
        version_number=new_version_number,
        data=jsonable_encoder(event),
        created_by=current_user.id,
        change_description="Event updated",
    )
    db.add(new_version)
    db.flush()  # Ensure new_version.id is available
    for field, value in update_data.items():
        old_value = getattr(current_version.data, field, None) if current_version else None
        if old_value != value:
            changelog = EventChangeLog(
                event_id=event_id,
                version_id=new_version.id,
                field_name=field,
                old_value=jsonable_encoder(old_value),
                new_value=jsonable_encoder(value),
                created_by=current_user.id,
            )
            db.add(changelog)
    db.commit()
    event.version_number = new_version_number
    return event


@router.delete("/{event_id}", response_model=EventSchema)
def delete_event(*, db: Session = Depends(get_db), event_id: int, current_user: User = Depends(get_current_active_user)) -> Any:
    event = get_event_with_permission(db, event_id, current_user, required_role=UserRole.OWNER)
    db.delete(event)
    db.commit()
    return event


@router.post("/{event_id}/share", response_model=EventPermissionSchema)
def share_event(*, db: Session = Depends(get_db), event_id: int, permission_in: EventPermissionCreate, current_user: User = Depends(get_current_active_user)) -> Any:
    event = get_event_with_permission(db, event_id, current_user, required_role=UserRole.OWNER)
    user = db.query(User).filter(User.id == permission_in.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    existing_permission = (
        db.query(EventPermission)
        .filter(EventPermission.event_id == event_id, EventPermission.user_id == permission_in.user_id)
        .first()
    )
    if existing_permission:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already has permission for this event")
    permission = EventPermission(event_id=event_id, user_id=permission_in.user_id, role=permission_in.role)
    db.add(permission)
    db.commit()
    db.refresh(permission)
    return permission


@router.get("/{event_id}/permissions", response_model=List[EventPermissionSchema])
def list_event_permissions(*, db: Session = Depends(get_db), event_id: int, current_user: User = Depends(get_current_active_user)) -> Any:
    event = get_event_with_permission(db, event_id, current_user)
    permissions = db.query(EventPermission).filter(EventPermission.event_id == event_id).all()
    return permissions


@router.put("/{event_id}/permissions/{user_id}", response_model=EventPermissionSchema)
def update_event_permission(*, db: Session = Depends(get_db), event_id: int, user_id: int, permission_in: EventPermissionUpdate, current_user: User = Depends(get_current_active_user)) -> Any:
    event = get_event_with_permission(db, event_id, current_user, required_role=UserRole.OWNER)
    permission = db.query(EventPermission).filter(EventPermission.event_id == event_id, EventPermission.user_id == user_id).first()
    if not permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    permission.role = permission_in.role
    db.add(permission)
    db.commit()
    db.refresh(permission)
    return permission


@router.delete("/{event_id}/permissions/{user_id}", response_model=EventPermissionSchema)
def delete_event_permission(*, db: Session = Depends(get_db), event_id: int, user_id: int, current_user: User = Depends(get_current_active_user)) -> Any:
    event = get_event_with_permission(db, event_id, current_user, required_role=UserRole.OWNER)
    permission = db.query(EventPermission).filter(EventPermission.event_id == event_id, EventPermission.user_id == user_id).first()
    if not permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    db.delete(permission)
    db.commit()
    return permission


@router.get("/{event_id}/history/{version_number}", response_model=EventVersionSchema)
def get_event_version(*, db: Session = Depends(get_db), event_id: int, version_number: int, current_user: User = Depends(get_current_active_user)) -> Any:
    event = get_event_with_permission(db, event_id, current_user)
    version = db.query(EventVersion).filter(EventVersion.event_id == event_id, EventVersion.version_number == version_number).first()
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    return version


@router.post("/{event_id}/rollback/{version_number}", response_model=EventSchema)
def rollback_event(*, db: Session = Depends(get_db), event_id: int, version_number: int, current_user: User = Depends(get_current_active_user)) -> Any:
    event = get_event_with_permission(db, event_id, current_user, required_role=UserRole.EDITOR)
    version = db.query(EventVersion).filter(EventVersion.event_id == event_id, EventVersion.version_number == version_number).first()
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    for field, value in version.data.items():
        if field != "id" and field != "owner_id":
            setattr(event, field, value)
    db.add(event)
    current_version = db.query(EventVersion).filter(EventVersion.event_id == event_id).order_by(EventVersion.version_number.desc()).first()
    new_version = EventVersion(
        event_id=event_id,
        version_number=current_version.version_number + 1,
        data=jsonable_encoder(event),
        created_by=current_user.id,
        change_description=f"Rolled back to version {version.version_number}",
    )
    db.add(new_version)
    db.flush()
    for field, value in version.data.items():
        if field != "id" and field != "owner_id":
            old_value = getattr(current_version.data, field, None)
            if old_value != value:
                changelog = EventChangeLog(
                    event_id=event_id,
                    version_id=new_version.id,
                    field_name=field,
                    old_value=jsonable_encoder(old_value),
                    new_value=jsonable_encoder(value),
                    created_by=current_user.id,
                )
                db.add(changelog)
    db.commit()
    db.refresh(event)
    return event


@router.get("/{event_id}/changelog", response_model=List[EventChangeLogSchema])
def get_event_changelog(*, db: Session = Depends(get_db), event_id: int, current_user: User = Depends(get_current_active_user)) -> Any:
    event = get_event_with_permission(db, event_id, current_user)
    changelog = (
        db.query(EventChangeLog)
        .join(EventVersion, EventChangeLog.version_id == EventVersion.id)
        .filter(EventChangeLog.event_id == event_id)
        .order_by(EventChangeLog.created_at.desc())
        .all()
    )
    return changelog


@router.get("/{event_id}/diff/{version_number1}/{version_number2}", response_model=List[EventDiff])
def get_event_diff(*, db: Session = Depends(get_db), event_id: int, version_number1: int, version_number2: int, current_user: User = Depends(get_current_active_user)) -> Any:
    event = get_event_with_permission(db, event_id, current_user)
    version1 = db.query(EventVersion).filter(EventVersion.event_id == event_id, EventVersion.version_number == version_number1).first()
    version2 = db.query(EventVersion).filter(EventVersion.event_id == event_id, EventVersion.version_number == version_number2).first()
    if not version1 or not version2:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or both versions not found")
    diffs = []
    for field, value2 in version2.data.items():
        if field not in ["id", "owner_id"]:
            value1 = version1.data.get(field)
            if value1 != value2:
                diff = EventDiff(
                    field_name=field,
                    old_value=value1,
                    new_value=value2,
                    change_type="modified" if value1 is not None else "added",
                )
                diffs.append(diff)
    for field, value1 in version1.data.items():
        if field not in ["id", "owner_id"] and field not in version2.data:
            diff = EventDiff(
                field_name=field,
                old_value=value1,
                new_value=None,
                change_type="removed",
            )
            diffs.append(diff)
    return diffs 