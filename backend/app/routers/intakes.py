from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import ProjectIntake, ProjectProfile, IntakeStatus
from ..schemas import (
    IntakeCreate,
    IntakeOut,
    ProjectProfileCreate,
    ProjectProfileOut,
    ProjectProfileUpdate,
)
from ..services.intake_parser import parse_raw_text
from ..services.audit import log_event

router = APIRouter(tags=["intakes"])


def _deserialize_intake(parsed_json: str) -> tuple[dict[str, Any], list[str]]:
    payload = json.loads(parsed_json)
    return payload.get("fields", {}), payload.get("unknown_lines", [])


def _serialize_intake(fields: dict[str, Any], unknown_lines: list[str]) -> str:
    return json.dumps({"fields": fields, "unknown_lines": unknown_lines}, ensure_ascii=False)


@router.post("/api/intakes", response_model=IntakeOut)
def create_intake(
    payload: IntakeCreate,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    fields, unknown_lines = parse_raw_text(payload.raw_text)
    intake = ProjectIntake(
        raw_text=payload.raw_text,
        parsed_json=_serialize_intake(fields, unknown_lines),
        created_by=user.id,
        status=IntakeStatus.pending,
    )
    db.add(intake)
    db.commit()
    db.refresh(intake)

    log_event(
        db,
        action="INTAKE_CREATE",
        entity_type="intake",
        entity_id=intake.id,
        user_id=user.id,
        metadata={"intake_id": intake.id},
        ip=request.client.host if request.client else None,
    )

    parsed_fields, unknown_lines = _deserialize_intake(intake.parsed_json)
    return IntakeOut(
        id=intake.id,
        raw_text=intake.raw_text,
        parsed_fields=parsed_fields,
        unknown_lines=unknown_lines,
        status=intake.status.value,
        created_by=intake.created_by,
        created_at=intake.created_at,
    )


@router.get("/api/intakes", response_model=list[IntakeOut])
def list_intakes(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    items = db.query(ProjectIntake).order_by(ProjectIntake.created_at.desc()).limit(50).all()
    results: list[IntakeOut] = []
    for item in items:
        parsed_fields, unknown_lines = _deserialize_intake(item.parsed_json)
        results.append(
            IntakeOut(
                id=item.id,
                raw_text=item.raw_text,
                parsed_fields=parsed_fields,
                unknown_lines=unknown_lines,
                status=item.status.value,
                created_by=item.created_by,
                created_at=item.created_at,
            )
        )
    return results


@router.get("/api/intakes/{intake_id}", response_model=IntakeOut)
def get_intake(
    intake_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    item = db.query(ProjectIntake).filter(ProjectIntake.id == intake_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Intake not found")
    parsed_fields, unknown_lines = _deserialize_intake(item.parsed_json)
    return IntakeOut(
        id=item.id,
        raw_text=item.raw_text,
        parsed_fields=parsed_fields,
        unknown_lines=unknown_lines,
        status=item.status.value,
        created_by=item.created_by,
        created_at=item.created_at,
    )


@router.post("/api/intakes/{intake_id}/confirm", response_model=ProjectProfileOut)
def confirm_intake(
    intake_id: int,
    payload: ProjectProfileCreate,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    intake = db.query(ProjectIntake).filter(ProjectIntake.id == intake_id).first()
    if not intake:
        raise HTTPException(status_code=404, detail="Intake not found")

    data = payload.model_dump()
    data.pop("intake_id", None)
    profile = ProjectProfile(
        intake_id=intake_id,
        created_by=user.id,
        **data,
    )
    db.add(profile)
    intake.status = IntakeStatus.confirmed
    db.commit()
    db.refresh(profile)

    log_event(
        db,
        action="INTAKE_CONFIRM",
        entity_type="profile",
        entity_id=profile.id,
        user_id=user.id,
        metadata={"intake_id": intake_id, "profile_id": profile.id},
        ip=request.client.host if request.client else None,
    )

    return profile


@router.get("/api/profiles", response_model=list[ProjectProfileOut])
def list_profiles(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return db.query(ProjectProfile).order_by(ProjectProfile.created_at.desc()).limit(50).all()


@router.get("/api/profiles/{profile_id}", response_model=ProjectProfileOut)
def get_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    profile = db.query(ProjectProfile).filter(ProjectProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/api/profiles/{profile_id}", response_model=ProjectProfileOut)
def update_profile(
    profile_id: int,
    payload: ProjectProfileUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    profile = db.query(ProjectProfile).filter(ProjectProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)

    log_event(
        db,
        action="PROFILE_UPDATE",
        entity_type="profile",
        entity_id=profile.id,
        user_id=user.id,
        metadata={"profile_id": profile.id},
        ip=request.client.host if request.client else None,
    )

    return profile
