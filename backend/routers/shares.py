from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.models import ShareToken, Patient, Result, Report, User
from backend.schemas.share import ShareCreate, ShareResponse, ShareDetail, SharePatientInfo, ShareTrendData, TrendDataPoint
from backend.core.auth import get_current_user
from backend.core.normalization import normalize_metric_name, get_metric_info
from datetime import datetime, timedelta
import secrets

router = APIRouter(prefix="/api/share", tags=["share"])


@router.post("/generate", response_model=ShareResponse)
async def generate_share(
    data: ShareCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    patient_r = await db.execute(
        select(Patient).where(Patient.id == data.patient_id, Patient.user_id == user.id)
    )
    if not patient_r.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="无权访问该患者")

    token_str = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(days=data.expire_days)

    share = ShareToken(
        token=token_str,
        patient_id=data.patient_id,
        metric_names=",".join(data.metric_names) if data.metric_names else None,
        expires_at=expires,
    )
    db.add(share)
    await db.flush()

    return ShareResponse(
        token=token_str,
        expires_at=expires,
        url=f"/share/{token_str}",
    )


@router.get("/{token}", response_model=ShareDetail)
async def access_share(token: str, db: AsyncSession = Depends(get_db)):
    share_r = await db.execute(select(ShareToken).where(ShareToken.token == token))
    share = share_r.scalar_one_or_none()
    if not share:
        raise HTTPException(status_code=404, detail="分享链接不存在")

    if share.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="分享链接已过期")

    patient_r = await db.execute(select(Patient).where(Patient.id == share.patient_id))
    patient = patient_r.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    allowed_metrics = None
    if share.metric_names:
        allowed_metrics = set(share.metric_names.split(","))

    reports_r = await db.execute(
        select(Report).where(Report.patient_id == share.patient_id).order_by(Report.exam_date.asc())
    )
    reports = reports_r.scalars().all()

    trends: dict[str, list] = {}
    for report in reports:
        results_r = await db.execute(
            select(Result).where(Result.report_id == report.id)
        )
        for r in results_r.scalars():
            if allowed_metrics and r.metric_name not in allowed_metrics:
                continue
            if r.metric_name not in trends:
                info = get_metric_info(r.metric_name)
                unit = info.get("unit", "") if info else r.unit
                ref = info.get("ref_range", {}).get("default", {}) if info else {}
                trends[r.metric_name] = {
                    "metric_name": r.metric_name,
                    "unit": unit or r.unit,
                    "ref_min": ref.get("min") if ref.get("min") is not None else r.ref_min,
                    "ref_max": ref.get("max") if ref.get("max") is not None else r.ref_max,
                    "data_points": [],
                }
            trends[r.metric_name]["data_points"].append(TrendDataPoint(
                date=report.exam_date,
                value=r.value,
                unit=r.unit,
                ref_min=r.ref_min,
                ref_max=r.ref_max,
                is_abnormal=r.is_abnormal or False,
                institution=report.institution,
                notes=r.notes,
            ))

    return ShareDetail(
        patient_info=SharePatientInfo(
            name=patient.name,
            gender=patient.gender,
            birth_date=patient.birth_date,
        ),
        trends=[ShareTrendData(**v) for v in trends.values()],
        expires_at=share.expires_at,
    )
