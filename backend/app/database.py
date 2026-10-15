from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from .config import get_settings


def now():
    return datetime.now(timezone.utc)


def uid():
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    name: Mapped[str] = mapped_column(String(80))
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)


class Record(Base):
    """Private history, vocabulary, tutor turns, jobs and usage metadata."""
    __tablename__ = 'records'
    __table_args__ = (Index('ix_records_user_kind_created', 'user_id', 'kind', 'created_at'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    kind: Mapped[str] = mapped_column(String(24), index=True)
    data: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)


def make_engine(url):
    return create_engine(url, pool_pre_ping=True,
                         connect_args={'check_same_thread': False} if url.startswith('sqlite') else {})


engine = make_engine(get_settings().database_url)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def get_db():
    with SessionLocal() as session:
        yield session
