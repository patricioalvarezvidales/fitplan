import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models import PlanSession, User, WorkoutLog
from app.schemas.api import CompleteWorkoutRequest, HistoryOut, PlanOut
from app.services.routine_engine import generate_plan, get_active_plan

router = APIRouter(tags=["plans"])


def serialize_plan(db: Session, plan) -> PlanOut:
    completed_ids = set(db.scalars(select(WorkoutLog.session_id).where(WorkoutLog.user_id == plan.user_id)).all())
    result = PlanOut.model_validate(plan)
    for session in result.sessions:
        session.completed = session.id in completed_ids
    return result


@router.post("/plans/generate", response_model=PlanOut)
def create_plan(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PlanOut:
    try:
        plan = generate_plan(db, user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_plan(db, plan)


@router.get("/plans/current", response_model=PlanOut)
def current_plan(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PlanOut:
    plan = get_active_plan(db, user.id)
    if not plan:
        raise HTTPException(status_code=404, detail="Aún no tienes una rutina activa")
    return serialize_plan(db, plan)


@router.post("/sessions/{session_id}/complete", status_code=201)
def complete_session(
    session_id: str,
    payload: CompleteWorkoutRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    session = db.scalar(select(PlanSession).where(PlanSession.id == uuid.UUID(session_id)))
    if not session or session.plan.user_id != user.id:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    if db.scalar(select(WorkoutLog).where(WorkoutLog.user_id == user.id, WorkoutLog.session_id == session.id)):
        raise HTTPException(status_code=409, detail="Esta sesión ya fue completada")
    db.add(WorkoutLog(user_id=user.id, session_id=session.id, **payload.model_dump()))
    db.commit()
    return {"message": "Entrenamiento registrado"}


@router.get("/history", response_model=list[HistoryOut])
def history(
    period: str = Query(default="all", pattern="^(all|week|month)$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[HistoryOut]:
    statement = select(WorkoutLog).where(WorkoutLog.user_id == user.id).order_by(WorkoutLog.completed_at.desc())
    now = datetime.now(UTC)
    if period == "week":
        statement = statement.where(WorkoutLog.completed_at >= now - timedelta(days=7))
    elif period == "month":
        statement = statement.where(WorkoutLog.completed_at >= now - timedelta(days=30))
    logs = db.scalars(statement).all()
    return [
        HistoryOut(
            id=log.id,
            completed_at=log.completed_at,
            actual_minutes=log.actual_minutes,
            difficulty=log.difficulty,
            energy_level=log.energy_level,
            satisfaction=log.satisfaction,
            pain_reported=log.pain_reported,
            pain_area=log.pain_area,
            comments=log.comments,
            session_name=log.session.name,
            plan_name=log.session.plan.name,
        )
        for log in logs
    ]
