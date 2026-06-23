from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Exercise, PlanSession, SessionExercise, User, WorkoutLog, WorkoutPlan

FOCUS_BY_DAYS = {
    2: ["cuerpo completo A", "cuerpo completo B"],
    3: ["empuje y piernas", "tracción y core", "cuerpo completo"],
    4: ["tren superior A", "tren inferior A", "tren superior B", "tren inferior B"],
    5: ["empuje", "piernas", "tracción", "cardio y core", "cuerpo completo"],
    6: ["empuje A", "tracción A", "piernas A", "empuje B", "tracción B", "piernas B"],
    7: ["fuerza total", "cardio", "superior", "inferior", "core", "resistencia", "recuperación activa"],
}


def _parameters(goal: str, level: str, adaptation: float) -> tuple[int, str, int, float]:
    level_sets = {"principiante": 2, "intermedio": 3, "avanzado": 4}
    sets = max(2, min(5, round(level_sets.get(level, 2) * adaptation)))
    if goal == "ganancia_muscular":
        return sets, "8-12", 75, 7.5
    if goal == "resistencia":
        return max(2, sets - 1), "15-20", 35, 6.5
    return max(2, sets - 1), "12-15", 30, 7.0


def _adaptation_factor(db: Session, user_id) -> tuple[float, str]:
    logs = db.scalars(
        select(WorkoutLog).where(WorkoutLog.user_id == user_id).order_by(WorkoutLog.completed_at.desc()).limit(5)
    ).all()
    if not logs:
        return 1.0, "initial"
    avg_difficulty = sum(log.difficulty for log in logs) / len(logs)
    avg_energy = sum(log.energy_level for log in logs) / len(logs)
    pain = any(log.pain_reported for log in logs)
    if pain or avg_difficulty >= 8:
        return 0.8, "adapted: menor volumen por dificultad o molestia"
    if avg_difficulty <= 5 and avg_energy >= 7:
        return 1.2, "adapted: progresión por buen rendimiento"
    return 1.0, "adapted: mantenimiento por respuesta estable"


def generate_plan(db: Session, user: User) -> WorkoutPlan:
    profile = user.profile
    if not profile:
        raise ValueError("Completa tu perfil antes de generar una rutina")

    equipment = {item.equipment.name for item in profile.equipment}
    equipment.add("ninguno")
    restrictions = {item.restriction.name for item in profile.restrictions}
    exercises = db.scalars(select(Exercise).where(Exercise.is_active.is_(True))).all()

    eligible = []
    for exercise in exercises:
        tags = {tag for tag in exercise.goal_tags.split(",") if tag}
        blocked = {tag for tag in exercise.restriction_tags.split(",") if tag}
        if profile.primary_goal not in tags:
            continue
        if exercise.equipment_name not in equipment:
            continue
        if restrictions & blocked:
            continue
        eligible.append(exercise)

    if len(eligible) < 4:
        eligible = [e for e in exercises if e.equipment_name == "ninguno" and not (restrictions & set(e.restriction_tags.split(",")))]
    if not eligible:
        raise ValueError("No hay ejercicios compatibles con tus restricciones actuales")

    previous = db.scalars(select(WorkoutPlan).where(WorkoutPlan.user_id == user.id)).all()
    for plan in previous:
        plan.status = "archived"

    factor, reason = _adaptation_factor(db, user.id)
    version = len(previous) + 1
    start = date.today()
    end = start + timedelta(days=6)
    plan = WorkoutPlan(
        user_id=user.id,
        name=f"Semana {version} · {profile.primary_goal.replace('_', ' ').title()}",
        goal=profile.primary_goal,
        start_date=start,
        end_date=end,
        version=version,
        generation_reason=reason,
    )
    db.add(plan)
    db.flush()

    focuses = FOCUS_BY_DAYS[profile.available_days]
    exercise_count = max(4, min(7, profile.session_minutes // 9))
    sets, reps, rest, rpe = _parameters(profile.primary_goal, profile.experience_level, factor)

    for day_index, focus in enumerate(focuses, start=1):
        scheduled = start + timedelta(days=round((day_index - 1) * 6 / max(1, profile.available_days - 1)))
        session = PlanSession(
            plan_id=plan.id,
            day_number=day_index,
            scheduled_date=scheduled,
            name=f"Día {day_index}: {focus.title()}",
            estimated_minutes=profile.session_minutes,
            focus=focus,
        )
        db.add(session)
        db.flush()

        scored = sorted(
            eligible,
            key=lambda e: (
                0 if e.difficulty_level == profile.experience_level else 1,
                (day_index + len(e.name)) % 5,
                e.name,
            ),
        )
        offset = (day_index - 1) * 2
        selected = [scored[(offset + i) % len(scored)] for i in range(min(exercise_count, len(scored)))]
        for order, exercise in enumerate(selected, start=1):
            db.add(SessionExercise(
                session_id=session.id,
                exercise_id=exercise.id,
                exercise_order=order,
                sets=sets,
                repetitions="30-45 s" if exercise.movement_pattern == "cardio" else reps,
                rest_seconds=rest,
                target_rpe=rpe,
                notes="Reduce el rango si aparece dolor; detén la sesión ante una molestia aguda.",
            ))

    db.commit()
    return get_active_plan(db, user.id)


def get_active_plan(db: Session, user_id) -> WorkoutPlan | None:
    return db.scalar(
        select(WorkoutPlan)
        .where(WorkoutPlan.user_id == user_id, WorkoutPlan.status == "active")
        .options(selectinload(WorkoutPlan.sessions).selectinload(PlanSession.exercises).selectinload(SessionExercise.exercise))
        .order_by(WorkoutPlan.created_at.desc())
    )
