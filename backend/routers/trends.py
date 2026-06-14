from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.models import Result, Report, Patient, User
from backend.schemas.share import TrendResponse, TrendDataPoint, MetricWithAbnormalCount
from backend.core.auth import get_current_user
from backend.core.normalization import normalize_metric_name, get_metric_info
from datetime import date, timedelta
from typing import Optional
import numpy as np

router = APIRouter(prefix="/api/trends", tags=["trends"])


@router.get("/metrics", response_model=list[MetricWithAbnormalCount])
async def list_metrics_with_abnormal_count(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    patient_r = await db.execute(
        select(Patient).where(Patient.id == patient_id, Patient.user_id == user.id)
    )
    if not patient_r.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="无权访问")

    q = (
        select(Result.metric_name, func.sum(Result.is_abnormal.cast(Integer)).label("abnormal_count"))
        .join(Report, Result.report_id == Report.id)
        .join(Patient, Report.patient_id == Patient.id)
        .where(Patient.user_id == user.id, Report.patient_id == patient_id)
        .group_by(Result.metric_name)
        .order_by(func.sum(Result.is_abnormal.cast(Integer)).desc())
    )
    rows = await db.execute(q)
    return [MetricWithAbnormalCount(metric_name=row[0], abnormal_count=row[1] or 0) for row in rows.all()]


def compute_linear_regression(values: list[float]) -> list[float]:
    if len(values) < 2:
        return values
    x = np.arange(len(values))
    y = np.array(values)
    coeffs = np.polyfit(x, y, 1)

    return (coeffs[0] * x + coeffs[1]).tolist()


def get_direction(values: list[float]) -> str:
    if len(values) < 2:
        return "stable"
    recent = values[-min(5, len(values)):]
    diff = recent[-1] - recent[0]
    avg = sum(abs(recent[i+1] - recent[i]) for i in range(len(recent)-1)) / max(len(recent)-1, 1)
    if abs(diff) < avg * 0.5:
        return "stable"
    return "up" if diff > 0 else "down"


@router.get("/", response_model=TrendResponse)
async def get_trend(
    metric_name: str,
    patient_id: int,
    range_months: Optional[int] = Query(None, alias="range"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    std_name = normalize_metric_name(metric_name)
    if not std_name:
        std_name = metric_name

    patient_r = await db.execute(
        select(Patient).where(Patient.id == patient_id, Patient.user_id == user.id)
    )
    if not patient_r.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="无权访问")

    q = (
        select(Result, Report.exam_date, Report.institution)
        .join(Report, Result.report_id == Report.id)
        .join(Patient, Report.patient_id == Patient.id)
        .where(
            Result.metric_name == std_name,
            Patient.user_id == user.id,
            Report.patient_id == patient_id,
        )
        .order_by(Report.exam_date.asc())
    )

    if range_months:
        cutoff = date.today() - timedelta(days=range_months * 30)
        q = q.where(Report.exam_date >= cutoff)

    rows = await db.execute(q)
    rows = rows.all()

    if not rows:
        return TrendResponse(
            metric_name=std_name, unit="", ref_min=None, ref_max=None, data_points=[]
        )

    info = get_metric_info(std_name)
    unit = info.get("unit", "") if info else ""
    dr = info.get("ref_range", {}).get("default", {}) if info else {}
    ref_min = dr.get("min")
    ref_max = dr.get("max")

    data_points = []
    values = []
    for result, exam_date, institution in rows:
        dp = TrendDataPoint(
            date=exam_date,
            value=result.value,
            unit=result.unit or unit,
            ref_min=result.ref_min if result.ref_min is not None else ref_min,
            ref_max=result.ref_max if result.ref_max is not None else ref_max,
            is_abnormal=result.is_abnormal or False,
            institution=institution,
            notes=result.notes,
        )
        data_points.append(dp)
        values.append(result.value)

    trend_line = compute_linear_regression(values)
    direction = get_direction(values)

    return TrendResponse(
        metric_name=std_name,
        unit=unit or data_points[0].unit if data_points else "",
        ref_min=ref_min,
        ref_max=ref_max,
        trend_line=trend_line,
        direction=direction,
        data_points=data_points,
    )
