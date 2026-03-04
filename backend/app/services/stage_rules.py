from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml
from sqlalchemy.orm import Session

from ..config import BASE_DIR
from ..models import Deliverable, Project, Stage

STAGE_ORDER = [
    Stage.evaluation.value,
    Stage.estimation.value,
    Stage.initiation.value,
    Stage.planning.value,
    Stage.bidding.value,
    Stage.contracting.value,
    Stage.preopen.value,
    Stage.operation.value,
    Stage.review.value,
]

_RULES_CACHE: Dict[str, Any] | None = None


def _rules_path() -> Path:
    return BASE_DIR / "app" / "rules" / "stage_requirements.yaml"


def load_rules() -> Dict[str, Any]:
    global _RULES_CACHE
    if _RULES_CACHE is None:
        with _rules_path().open("r", encoding="utf-8") as fh:
            _RULES_CACHE = yaml.safe_load(fh) or {}
    return _RULES_CACHE


def get_next_stage(current_stage: str) -> str | None:
    if current_stage not in STAGE_ORDER:
        return None
    idx = STAGE_ORDER.index(current_stage)
    if idx + 1 >= len(STAGE_ORDER):
        return None
    return STAGE_ORDER[idx + 1]


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def check_requirements(
    project: Project,
    target_stage: str,
    db: Session,
) -> Tuple[List[str], List[str]]:
    rules = load_rules().get("stages", {})
    stage_rule = rules.get(target_stage, {})
    required_fields = stage_rule.get("required_fields", [])
    required_deliverables = stage_rule.get("required_deliverables", [])

    missing_fields = [
        field for field in required_fields if _is_missing(getattr(project, field, None))
    ]

    missing_deliverables = []
    for dtype in required_deliverables:
        found = (
            db.query(Deliverable)
            .filter(Deliverable.project_id == project.id)
            .filter(Deliverable.type == dtype)
            .first()
        )
        if not found:
            missing_deliverables.append(dtype)

    return missing_fields, missing_deliverables


def validate_transition(project: Project, to_stage: str, db: Session) -> Dict[str, Any]:
    next_stage = get_next_stage(project.current_stage)
    if next_stage is None:
        return {
            "ok": False,
            "reason": "Project already at final stage",
            "missing_fields": [],
            "missing_deliverables": [],
        }
    if to_stage != next_stage:
        return {
            "ok": False,
            "reason": f"Next stage must be {next_stage}",
            "missing_fields": [],
            "missing_deliverables": [],
        }

    missing_fields, missing_deliverables = check_requirements(project, to_stage, db)
    ok = not missing_fields and not missing_deliverables
    return {
        "ok": ok,
        "missing_fields": missing_fields,
        "missing_deliverables": missing_deliverables,
        "required_fields": load_rules().get("stages", {}).get(to_stage, {}).get(
            "required_fields", []
        ),
        "required_deliverables": load_rules().get("stages", {}).get(to_stage, {}).get(
            "required_deliverables", []
        ),
        "target_stage": to_stage,
    }
