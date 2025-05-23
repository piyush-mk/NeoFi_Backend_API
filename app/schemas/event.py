from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.db.models import UserRole


class EventBase(BaseModel):
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    is_recurring: bool = False
    recurrence_pattern: Optional[Dict[str, Any]] = None


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[Dict[str, Any]] = None


class EventInDBBase(EventBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    version_number: Optional[int] = None

    class Config:
        from_attributes = True


class Event(EventInDBBase):
    pass


class EventPermissionBase(BaseModel):
    user_id: int
    role: UserRole


class EventPermissionCreate(EventPermissionBase):
    pass


class EventPermissionUpdate(BaseModel):
    role: UserRole


class EventPermission(EventPermissionBase):
    id: int
    event_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EventVersionBase(BaseModel):
    version_number: int
    data: Dict[str, Any]
    change_description: Optional[str] = None


class EventVersionCreate(EventVersionBase):
    pass


class EventVersion(EventVersionBase):
    id: int
    event_id: int
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class EventChangeLogBase(BaseModel):
    field_name: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None


class EventChangeLog(EventChangeLogBase):
    id: int
    event_id: int
    version_id: int
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class EventDiff(BaseModel):
    field_name: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    change_type: str 