from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def now_utc() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    token_version: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    profile: Mapped[UserProfile | None] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    plans: Mapped[list[WorkoutPlan]] = relationship(back_populates="user", cascade="all, delete-orphan")
    logs: Mapped[list[WorkoutLog]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(String(30))
    weight_kg: Mapped[float] = mapped_column(Float)
    height_cm: Mapped[float] = mapped_column(Float)
    experience_level: Mapped[str] = mapped_column(String(30))
    primary_goal: Mapped[str] = mapped_column(String(40))
    training_location: Mapped[str] = mapped_column(String(40), default="casa")
    available_days: Mapped[int] = mapped_column(Integer)
    session_minutes: Mapped[int] = mapped_column(Integer, default=45)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    user: Mapped[User] = relationship(back_populates="profile")
    equipment: Mapped[list[UserEquipment]] = relationship(cascade="all, delete-orphan")
    restrictions: Mapped[list[UserRestriction]] = relationship(cascade="all, delete-orphan")


class Equipment(Base):
    __tablename__ = "equipment"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    category: Mapped[str] = mapped_column(String(60), default="general")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class UserEquipment(Base):
    __tablename__ = "user_equipment"
    __table_args__ = (UniqueConstraint("profile_id", "equipment_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("user_profiles.id", ondelete="CASCADE"))
    equipment_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("equipment.id", ondelete="CASCADE"))
    equipment: Mapped[Equipment] = relationship()


class Restriction(Base):
    __tablename__ = "restrictions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    body_area: Mapped[str] = mapped_column(String(60))
    description: Mapped[str] = mapped_column(Text, default="")


class UserRestriction(Base):
    __tablename__ = "user_restrictions"
    __table_args__ = (UniqueConstraint("profile_id", "restriction_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("user_profiles.id", ondelete="CASCADE"))
    restriction_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("restrictions.id", ondelete="CASCADE"))
    severity: Mapped[str] = mapped_column(String(20), default="moderada")
    notes: Mapped[str] = mapped_column(Text, default="")
    restriction: Mapped[Restriction] = relationship()


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str] = mapped_column(Text)
    primary_muscle: Mapped[str] = mapped_column(String(60))
    movement_pattern: Mapped[str] = mapped_column(String(60))
    difficulty_level: Mapped[str] = mapped_column(String(30))
    goal_tags: Mapped[str] = mapped_column(String(150), default="")
    equipment_name: Mapped[str] = mapped_column(String(100), default="ninguno")
    restriction_tags: Mapped[str] = mapped_column(String(150), default="")
    video_url: Mapped[str] = mapped_column(String(500), default="")
    image_url: Mapped[str] = mapped_column(String(500), default="")
    instructions: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(140))
    goal: Mapped[str] = mapped_column(String(40))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="active")
    version: Mapped[int] = mapped_column(Integer, default=1)
    generation_reason: Mapped[str] = mapped_column(String(200), default="initial")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    user: Mapped[User] = relationship(back_populates="plans")
    sessions: Mapped[list[PlanSession]] = relationship(back_populates="plan", cascade="all, delete-orphan", order_by="PlanSession.day_number")


class PlanSession(Base):
    __tablename__ = "plan_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("workout_plans.id", ondelete="CASCADE"), index=True)
    day_number: Mapped[int] = mapped_column(Integer)
    scheduled_date: Mapped[date] = mapped_column(Date)
    name: Mapped[str] = mapped_column(String(120))
    estimated_minutes: Mapped[int] = mapped_column(Integer)
    focus: Mapped[str] = mapped_column(String(80))

    plan: Mapped[WorkoutPlan] = relationship(back_populates="sessions")
    exercises: Mapped[list[SessionExercise]] = relationship(cascade="all, delete-orphan", order_by="SessionExercise.exercise_order")


class SessionExercise(Base):
    __tablename__ = "session_exercises"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("plan_sessions.id", ondelete="CASCADE"), index=True)
    exercise_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("exercises.id"))
    exercise_order: Mapped[int] = mapped_column(Integer)
    sets: Mapped[int] = mapped_column(Integer)
    repetitions: Mapped[str] = mapped_column(String(30))
    rest_seconds: Mapped[int] = mapped_column(Integer)
    target_rpe: Mapped[float] = mapped_column(Float)
    notes: Mapped[str] = mapped_column(Text, default="")

    exercise: Mapped[Exercise] = relationship()


class WorkoutLog(Base):
    __tablename__ = "workout_logs"
    __table_args__ = (UniqueConstraint("user_id", "session_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("plan_sessions.id"), index=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    actual_minutes: Mapped[int] = mapped_column(Integer)
    difficulty: Mapped[int] = mapped_column(Integer)
    energy_level: Mapped[int] = mapped_column(Integer)
    satisfaction: Mapped[int] = mapped_column(Integer)
    pain_reported: Mapped[bool] = mapped_column(Boolean, default=False)
    pain_area: Mapped[str] = mapped_column(String(80), default="")
    comments: Mapped[str] = mapped_column(Text, default="")

    user: Mapped[User] = relationship(back_populates="logs")
    session: Mapped[PlanSession] = relationship()
