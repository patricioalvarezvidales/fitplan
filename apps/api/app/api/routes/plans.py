import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models import ExerciseLog, PlanSession, SessionExercise, User, WorkoutLog
from app.schemas.api import CompleteWorkoutRequest, ExerciseHistoryOut, HistoryOut, PlanOut
from app.services.routine_engine import generate_plan, get_active_plan, get_all_plans, get_plan

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


@router.get("/plans", response_model=list[PlanOut])
def list_plans(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[PlanOut]:
    return [serialize_plan(db, plan) for plan in get_all_plans(db, user.id)]


@router.get("/plans/current", response_model=PlanOut)
def current_plan(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PlanOut:
    plan = get_active_plan(db, user.id)
    if not plan:
        raise HTTPException(status_code=404, detail="Aún no tienes una rutina activa")
    return serialize_plan(db, plan)


@router.get("/plans/{plan_id}", response_model=PlanOut)
def plan_detail(plan_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PlanOut:
    plan = get_plan(db, user.id, uuid.UUID(plan_id))
    if not plan:
        raise HTTPException(status_code=404, detail="Semana no encontrada")
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

    expected = {
        item.id: item
        for item in db.scalars(select(SessionExercise).where(SessionExercise.session_id == session.id)).all()
    }
    if {item.session_exercise_id for item in payload.exercises} != set(expected):
        raise HTTPException(status_code=400, detail="Debes registrar todos los ejercicios de la sesión")

    workout_payload = payload.model_dump(exclude={"exercises"})
    workout_log = WorkoutLog(user_id=user.id, session_id=session.id, **workout_payload)
    db.add(workout_log)
    db.flush()

    for item in payload.exercises:
        assigned = expected[item.session_exercise_id]
        db.add(ExerciseLog(
            workout_log_id=workout_log.id,
            session_exercise_id=assigned.id,
            exercise_id=assigned.exercise_id,
            recommended_weight_kg=assigned.recommended_weight_kg,
            actual_weight_kg=item.actual_weight_kg,
            completed_sets=item.completed_sets,
            completed_repetitions=item.completed_repetitions,
        ))
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
            exercises=[
                ExerciseHistoryOut(
                    exercise_name=item.exercise.name,
                    recommended_weight_kg=item.recommended_weight_kg,
                    actual_weight_kg=item.actual_weight_kg,
                    completed_sets=item.completed_sets,
                    completed_repetitions=item.completed_repetitions,
                )
                for item in log.exercise_logs
            ],
        )
        for log in logs
    ]
