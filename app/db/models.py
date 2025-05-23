from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from datetime import datetime

from app.db.base_class import Base


class UserRole(str, enum.Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owned_events = relationship("Event", back_populates="owner", cascade="all, delete-orphan")
    event_permissions = relationship("EventPermission", back_populates="user", cascade="all, delete-orphan")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    location = Column(String, nullable=True)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign Keys
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
    # Relationships
    owner = relationship("User", back_populates="owned_events")
    permissions = relationship("EventPermission", back_populates="event", cascade="all, delete-orphan")
    versions = relationship("EventVersion", back_populates="event", cascade="all, delete-orphan")
    changelogs = relationship("EventChangeLog", back_populates="event", cascade="all, delete-orphan")


class EventPermission(Base):
    __tablename__ = "event_permissions"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    role = Column(Enum(UserRole))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    event = relationship("Event", back_populates="permissions")
    user = relationship("User", back_populates="event_permissions")


class EventVersion(Base):
    __tablename__ = "event_versions"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"))
    version_number = Column(Integer)
    data = Column(JSON)  # Stores the complete event data at this version
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    change_description = Column(String, nullable=True)

    # Relationships
    event = relationship("Event", back_populates="versions")
    user = relationship("User")
    changelogs = relationship("EventChangeLog", back_populates="version", cascade="all, delete-orphan")


class EventChangeLog(Base):
    __tablename__ = "event_changelog"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"))
    version_id = Column(Integer, ForeignKey("event_versions.id", ondelete="CASCADE"))
    field_name = Column(String)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

    # Relationships
    event = relationship("Event", back_populates="changelogs")
    version = relationship("EventVersion", back_populates="changelogs")
    user = relationship("User") 