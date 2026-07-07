from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.core.security import get_current_user
from app.db.session import get_db
from app.models import Equipment, Restriction, User, UserEquipment, UserProfile, UserRestriction
from app.schemas.api import CatalogItem, ProfileInput, ProfileOut

router = APIRouter(tags=["profile"])


@router.get("/catalog")
def catalog(db: Session = Depends(get_db)) -> dict[str, list[CatalogItem]]:
    equipment = db.scalars(select(Equipment).where(Equipment.is_active.is_(True)).order_by(Equipment.name)).all()
    restrictions = db.scalars(select(Restriction).order_by(Restriction.name)).all()
    return {
        "equipment": [CatalogItem.model_validate(item) for item in equipment],
        "restrictions": [CatalogItem.model_validate(item) for item in restrictions],
    }


def _load_profile(db: Session, user_id):
    return db.scalar(
        select(UserProfile)
        .where(UserProfile.user_id == user_id)
        .options(
            selectinload(UserProfile.equipment).selectinload(UserEquipment.equipment),
            selectinload(UserProfile.restrictions).selectinload(UserRestriction.restriction),
        )
    )


def _serialize(profile: UserProfile) -> ProfileOut:
    return ProfileOut(
        id=profile.id,
        user_id=profile.user_id,
        age=profile.age,
        gender=profile.gender,
        weight_kg=profile.weight_kg,
        height_cm=profile.height_cm,
        experience_level=profile.experience_level,
        primary_goal=profile.primary_goal,
        training_location=profile.training_location,
        available_days=profile.available_days,
        session_minutes=profile.session_minutes,
        equipment_ids=[x.equipment_id for x in profile.equipment],
        restriction_ids=[x.restriction_id for x in profile.restrictions],
        equipment=[CatalogItem.model_validate(x.equipment) for x in profile.equipment],
        restrictions=[CatalogItem.model_validate(x.restriction) for x in profile.restrictions],
    )


@router.get("/profile", response_model=ProfileOut)
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProfileOut:
    profile = _load_profile(db, user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    return _serialize(profile)


@router.put("/profile", response_model=ProfileOut)
def save_profile(payload: ProfileInput, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProfileOut:
    valid_equipment = set(db.scalars(select(Equipment.id).where(Equipment.id.in_(payload.equipment_ids))).all())
    valid_restrictions = set(db.scalars(select(Restriction.id).where(Restriction.id.in_(payload.restriction_ids))).all())
    if len(valid_equipment) != len(set(payload.equipment_ids)) or len(valid_restrictions) != len(set(payload.restriction_ids)):
        raise HTTPException(status_code=400, detail="Equipo o restricción inválida")

    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == user.id))
    values = payload.model_dump(exclude={"equipment_ids", "restriction_ids"})
    if not profile:
        profile = UserProfile(user_id=user.id, **values)
        db.add(profile)
        db.flush()
    else:
        for key, value in values.items():
            setattr(profile, key, value)
        db.execute(delete(UserEquipment).where(UserEquipment.profile_id == profile.id))
        db.execute(delete(UserRestriction).where(UserRestriction.profile_id == profile.id))

    for equipment_id in valid_equipment:
        db.add(UserEquipment(profile_id=profile.id, equipment_id=equipment_id))
    for restriction_id in valid_restrictions:
        db.add(UserRestriction(profile_id=profile.id, restriction_id=restriction_id))
    db.commit()
    return _serialize(_load_profile(db, user.id))
