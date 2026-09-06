"""Excel 导入中心：上传校验(dry-run) → 结果 → 确认入库 → 回滚。"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import openpyxl
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..deps import get_current_user, require_perm
from ..models import ImportBatch, User
from ..schemas import ImportBatchOut
from ..services import importer
from ..services.audit import record

router = APIRouter(prefix="/api/v1/import", tags=["导入中心"])
_STORE = Path("data/imports")


def _batch_no() -> str:
    return "IMP-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S%f")[:-3]


@router.post("/batches", response_model=ImportBatchOut, status_code=201)
def upload(file: UploadFile = File(...), db: Session = Depends(get_db),
           user: User = Depends(require_perm("import:run"))):
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(400, "请上传 .xlsx 文件")
    _STORE.mkdir(parents=True, exist_ok=True)
    batch_no = _batch_no()
    path = _STORE / f"{batch_no}.xlsx"
    path.write_bytes(file.file.read())

    try:
        wb = openpyxl.load_workbook(path, data_only=True)
    except Exception:
        raise HTTPException(400, "无法解析 Excel 文件")
    report, _ = importer.validate(wb, db)

    total = sum(r.total for r in report.summary.values())
    valid = sum(r.valid for r in report.summary.values())
    err = sum(r.error for r in report.summary.values())
    d = report.as_dict()
    batch = ImportBatch(
        batch_no=batch_no, file_name=file.filename, status="待确认", dry_run=True,
        total_rows=total, valid_rows=valid, error_rows=err,
        result_summary=d["summary"], error_detail=d["errors"],
        geocode_failed=d["geocode_failed"], operator_id=user.id,
    )
    db.add(batch)
    record(db, user, "import_validate", "import_batch", batch_no, {"total": total, "error": err})
    db.commit()
    db.refresh(batch)
    return batch


@router.get("/batches/{batch_id}", response_model=ImportBatchOut)
def get_batch(batch_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    b = db.get(ImportBatch, batch_id)
    if not b:
        raise HTTPException(404, "批次不存在")
    return b


@router.post("/batches/{batch_id}/commit", response_model=ImportBatchOut)
def commit_batch(batch_id: int, db: Session = Depends(get_db),
                 user: User = Depends(require_perm("import:run"))):
    b = db.get(ImportBatch, batch_id)
    if not b:
        raise HTTPException(404, "批次不存在")
    if b.status == "已导入":
        raise HTTPException(409, "该批次已导入")
    path = _STORE / f"{b.batch_no}.xlsx"
    if not path.exists():
        raise HTTPException(410, "上传文件已不存在，请重新上传")

    wb = openpyxl.load_workbook(path, data_only=True)
    report, parsed = importer.validate(wb, db)
    try:
        importer.commit(parsed, db, report)   # 事务内；异常整体回滚
        b.status = "已导入"
        b.dry_run = False
        b.committed_at = datetime.now(timezone.utc)
        b.geocode_failed = report.as_dict()["geocode_failed"]
        record(db, user, "import_commit", "import_batch", b.batch_no,
               {"valid": b.valid_rows})
        db.commit()
    except Exception as e:  # noqa: BLE001 —— 任一失败整体回滚，不留半成品
        db.rollback()
        b.status = "失败"
        db.commit()
        raise HTTPException(500, f"导入失败已回滚：{e}")
    db.refresh(b)
    return b


@router.post("/batches/{batch_id}/rollback", response_model=ImportBatchOut)
def rollback_batch(batch_id: int, db: Session = Depends(get_db),
                   user: User = Depends(require_perm("import:run"))):
    b = db.get(ImportBatch, batch_id)
    if not b:
        raise HTTPException(404, "批次不存在")
    if b.status == "已导入":
        # 已入库的真实数据回滚需按 batch 标记行，属后续能力
        raise HTTPException(400, "已导入批次的数据回滚暂未支持；请人工处理或走后续版本")
    b.status = "已回滚"
    record(db, user, "import_rollback", "import_batch", b.batch_no)
    db.commit()
    db.refresh(b)
    return b
