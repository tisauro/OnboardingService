import datetime

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String

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

    group = Column(String, index=True, nullable=True)

    created_date = Column(
        DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc)
    )

    expiration_date = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index("ix_bootstrap_keys_group", "group"),
        Index("ix_bootstrap_keys_is_active", "is_active"),
    )
