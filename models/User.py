import uuid
from enum import Enum as PyEnum

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

from app import app

db = SQLAlchemy(app)

Base = declarative_base()


class AuthProviders(PyEnum):
    GOOGLE = "GOOGLE"
    FACEBOOK = "FACEBOOK"
    GITHUB = "GITHUB"
    # Add other providers as needed


class RoleEnum(PyEnum):
    USER = "USER"
    ADMIN = "ADMIN"
    # Add other roles as needed


class User(Base):
    __tablename__ = 'user'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(String, unique=True, index=True, nullable=False)
    password = db.Column(String, nullable=False)
    locked = db.Column(Boolean, default=True)
    enabled = db.Column(Boolean, default=False)
    provider = db.Column(Enum(AuthProviders), nullable=False)
    providerId = db.Column(String, nullable=True)
    role = db.Column(Enum(RoleEnum), nullable=False)
    created_at = db.Column(DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(DateTime(timezone=True), onupdate=func.now())
    deleted = db.Column(Boolean, default=False)
    receive_notifications = db.Column(Boolean, default=True)

    attributes = db.Column(db.JSON, nullable=True)

    def __init__(self, username, password, locked=True, enabled=False, provider=None, providerId=None, role=None,
                 attributes=None):
        self.username = username
        self.password = password
        self.locked = locked
        self.enabled = enabled
        self.provider = provider
        self.providerId = providerId
        self.role = role
        self.attributes = attributes

    @property
    def get_name(self):
        return str(self.id)

    @property
    def is_account_non_expired(self):
        return True

    @property
    def is_account_non_locked(self):
        return not self.locked

    @property
    def is_credentials_non_expired(self):
        return True

    @property
    def is_enabled(self):
        return self.enabled


# Example to create all tables
# with app.app_context():
#     db.create_all()
