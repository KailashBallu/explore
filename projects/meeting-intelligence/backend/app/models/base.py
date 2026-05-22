import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def gen_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    default_language: Mapped[str] = mapped_column(String(10), default="en")
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    meetings = relationship("Meeting", back_populates="user")


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    meeting_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en")
    agenda_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    agenda_approval_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="meetings")
    attendees = relationship("MeetingAttendee", back_populates="meeting", cascade="all, delete-orphan")
    files = relationship("MeetingFile", back_populates="meeting", cascade="all, delete-orphan")
    minutes = relationship("Minutes", back_populates="meeting", cascade="all, delete-orphan")
    action_items = relationship("ActionItem", back_populates="meeting", cascade="all, delete-orphan")


class MeetingAttendee(Base):
    __tablename__ = "meeting_attendees"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    meeting_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    present: Mapped[bool] = mapped_column(Boolean, default=True)

    meeting = relationship("Meeting", back_populates="attendees")


class MeetingFile(Base):
    __tablename__ = "meeting_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    meeting_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    has_timestamps: Mapped[bool] = mapped_column(Boolean, default=False)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    meeting = relationship("Meeting", back_populates="files")


class Minutes(Base):
    __tablename__ = "minutes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    meeting_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    content: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    meeting = relationship("Meeting", back_populates="minutes")
    sections = relationship("MinutesSection", back_populates="minutes", cascade="all, delete-orphan")


class MinutesSection(Base):
    __tablename__ = "minutes_sections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    minutes_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("minutes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_type: Mapped[str] = mapped_column(String(50), nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    heading: Mapped[str | None] = mapped_column(String(500), nullable=True)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    source_start_char: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_end_char: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_start_time: Mapped[str | None] = mapped_column(String(20), nullable=True)
    source_end_time: Mapped[str | None] = mapped_column(String(20), nullable=True)
    speaker_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    minutes = relationship("Minutes", back_populates="sections")


class ActionItem(Base):
    __tablename__ = "action_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    meeting_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    meeting_attendee_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("meeting_attendees.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")

    meeting = relationship("Meeting", back_populates="action_items")


class GenerationEval(Base):
    __tablename__ = "generation_evals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    meeting_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False
    )
    minutes_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("minutes.id", ondelete="CASCADE"), nullable=True
    )
    section_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("minutes_sections.id", ondelete="CASCADE"), nullable=True
    )
    eval_method: Mapped[str] = mapped_column(String(20), nullable=False)
    accuracy_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    completeness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    attribution_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    language_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    conciseness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    judge_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    judge_raw_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SectionFeedback(Base):
    __tablename__ = "section_feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    section_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("minutes_sections.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[str | None] = mapped_column(String(20), nullable=True)
    free_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class UserStyleProfile(Base):
    __tablename__ = "user_style_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    style_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    source_minutes_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
