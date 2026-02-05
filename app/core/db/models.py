
from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from app.core.db.database import Base


class BootstrapKey(Base):
    """
    SQLAlchemy model for storing bootstrap keys.
    We store a hash of the key for security, not the raw key.
    """

    __tablename__ = "bootstrap_keys"

    id = Column(Integer, primary_key=True, index=True)

    # We store a secure hash of the key, not the key itself.
    key_hash = Column(String, unique=True, index=True, nullable=False)

    # Store the last 4 chars for easy identification in admin UIs
    key_hint = Column(String(4), nullable=False)

    key_group = Column(String, index=True, nullable=True)

    created_date = Column(DateTime(timezone=True), server_default=func.now())

    expiration_date = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False, index=True)
