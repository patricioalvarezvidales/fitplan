from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RegisterResponse(BaseModel):
    message: str
    confirmation_token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CatalogItem(BaseModel):
    id: uuid.UUID
    name: str
    category: str | None = None
    body_area: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ProfileInput(BaseModel):
    age: int = Field(ge=16, le=90)
    gender: str = Field(min_length=1, max_length=30)
    weight_kg: float = Field(ge=30, le=250)
    height_cm: float = Field(ge=120, le=230)
    experience_level: str
    primary_goal: str
    training_location: str = "casa"
    available_days: int = Field(ge=2, le=7)
    session_minutes: int = Field(ge=20, le=120)
    equipment_ids: list[uuid.UUID] = []
    restriction_ids: list[uuid.UUID] = []

    @model_validator(mode="after")
    def validate_choices(self) -> ProfileInput:
        if self.experience_level not in {"principiante", "intermedio", "avanzado"}:
            raise ValueError("Nivel de experiencia inválido")
        if self.primary_goal not in {"perdida_peso", "ganancia_muscular", "resistencia"}:
            raise ValueError("Objetivo inválido")
        return self


class ProfileOut(ProfileInput):
    id: uuid.UUID
    user_id: uuid.UUID
    equipment: list[CatalogItem]
    restrictions: list[CatalogItem]


class ExerciseOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    primary_muscle: str
    movement_pattern: str
    difficulty_level: str
    video_url: str
    image_url: str
    instructions: str

    model_config = ConfigDict(from_attributes=True)


class SessionExerciseOut(BaseModel):
    id: uuid.UUID
    exercise_order: int
    sets: int
    repetitions: str
    rest_seconds: int
    target_rpe: float
    notes: str
    exercise: ExerciseOut

    model_config = ConfigDict(from_attributes=True)


class SessionOut(BaseModel):
    id: uuid.UUID
    day_number: int
    scheduled_date: date
    name: str
    estimated_minutes: int
    focus: str
    completed: bool = False
    exercises: list[SessionExerciseOut]

    model_config = ConfigDict(from_attributes=True)


class PlanOut(BaseModel):
    id: uuid.UUID
    name: str
    goal: str
    start_date: date
    end_date: date
    status: str
    version: int
    generation_reason: str
    sessions: list[SessionOut]

    model_config = ConfigDict(from_attributes=True)


class CompleteWorkoutRequest(BaseModel):
    actual_minutes: int = Field(ge=5, le=240)
    difficulty: int = Field(ge=1, le=10)
    energy_level: int = Field(ge=1, le=10)
    satisfaction: int = Field(ge=1, le=10)
    pain_reported: bool = False
    pain_area: str = Field(default="", max_length=80)
    comments: str = Field(default="", max_length=1000)


class HistoryOut(BaseModel):
    id: uuid.UUID
    completed_at: datetime
    actual_minutes: int
    difficulty: int
    energy_level: int
    satisfaction: int
    pain_reported: bool
    pain_area: str
    comments: str
    session_name: str
    plan_name: str


class MeOut(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    email_confirmed: bool
    profile_complete: bool
