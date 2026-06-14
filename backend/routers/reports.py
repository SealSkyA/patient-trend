from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.database import get_db
from backend.models import Report, Result, Patient, User
from backend.schemas.report import (
    ReportCreate, ReportUpdate, ReportResponse, ReportSummary,
)
from backend.core.auth import get_current_user
from backend.core.normalization import normalize_metric_name, check_is_abnormal, validate_medical_range
from datetime import date
from typing import Optional

router = APIRouter(prefix="/api/reports", tags=["reports"])


async def get_patient_or_404(patient_id: int, user: User, db: AsyncSession):
    result = await db.execute(select(Patient).where(Patient.id == patient_id, Patient.user_id == user.id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在或无权访问")
    return patient


@router.get("/", response_model=list[ReportSummary])
async def list_reports(
    patient_id: int = 0,
    page: int = 1,
    size: int = 20,
    exam_date_start: Optional[date] = Query(None),
    exam_date_end: Optional[date] = Query(None),
    institution: Optional[str] = Query(None, max_length=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if patient_id:
        await get_patient_or_404(patient_id, user, db)

    q = select(Report, Patient).join(Patient, Report.patient_id == Patient.id).where(Patient.user_id == user.id)
    if patient_id:
        q = q.where(Report.patient_id == patient_id)
    if exam_date_start:
        q = q.where(Report.exam_date >= exam_date_start)
    if exam_date_end:
        q = q.where(Report.exam_date <= exam_date_end)
    if institution:
        q = q.where(Report.institution.ilike(f"%{institution}%"))
    q = q.order_by(Report.exam_date.desc())

    if patient_id:
        offset = (page - 1) * size
        q = q.offset(offset).limit(size)

    results = await db.execute(q)
    rows = results.all()

    summaries = []
    for report, patient in rows:
        metric_count = await db.execute(
            select(func.count(Result.id)).where(Result.report_id == report.id)
        )
        abnormal_count = await db.execute(
            select(func.count(Result.id)).where(Result.report_id == report.id, Result.is_abnormal == True)
        )
        summaries.append(ReportSummary(
            id=report.id,
            institution=report.institution,
            exam_date=report.exam_date,
            metric_count=metric_count.scalar_one(),
            abnormal_count=abnormal_count.scalar_one(),
        ))
    return summaries


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    r = await db.execute(
        select(Report)
        .options(selectinload(Report.results))
        .join(Patient)
        .where(Report.id == report_id, Patient.user_id == user.id)
    )
    report = r.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    return report


@router.post("/", response_model=ReportResponse)
async def create_report(
    data: ReportCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await get_patient_or_404(data.patient_id, user, db)

    report = Report(**data.model_dump(exclude={"results"}))
    db.add(report)
    await db.flush()

    for item in data.results:
        std_name = normalize_metric_name(item.metric_name) or item.metric_name
        info = normalize_metric_name(item.metric_name)

        ref_min = item.ref_min
        ref_max = item.ref_max
        if ref_min is None or ref_max is None:
            from backend.core.normalization import get_metric_info
            m_info = get_metric_info(std_name)
            if m_info:
                dr = m_info.get("ref_range", {}).get("default", {})
                if ref_min is None:
                    ref_min = dr.get("min")
                if ref_max is None:
                    ref_max = dr.get("max")

        is_abn = check_is_abnormal(item.value, ref_min, ref_max)

        db.add(Result(
            report_id=report.id,
            metric_name=std_name,
            value=item.value,
            unit=item.unit,
            ref_min=ref_min,
            ref_max=ref_max,
            is_abnormal=is_abn,
            notes=item.notes,
        ))

    await db.flush()
    await db.refresh(report)

    rr = await db.execute(
        select(Report)
        .options(selectinload(Report.results))
        .where(Report.id == report.id)
    )
    return rr.scalar_one()


@router.put("/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: int,
    data: ReportUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    r = await db.execute(
        select(Report).join(Patient).where(Report.id == report_id, Patient.user_id == user.id)
    )
    report = r.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    if data.institution is not None:
        report.institution = data.institution
    if data.exam_date is not None:
        report.exam_date = data.exam_date
    if data.notes is not None:
        report.notes = data.notes

    if data.results is not None:
        await db.execute(delete(Result).where(Result.report_id == report_id))

        for item in data.results:
            std_name = normalize_metric_name(item.metric_name) or item.metric_name
            from backend.core.normalization import get_metric_info
            m_info = get_metric_info(std_name)
            ref_min = item.ref_min
            ref_max = item.ref_max
            if ref_min is None or ref_max is None:
                if m_info:
                    dr = m_info.get("ref_range", {}).get("default", {})
                    if ref_min is None:
                        ref_min = dr.get("min")
                    if ref_max is None:
                        ref_max = dr.get("max")

            db.add(Result(
                report_id=report_id,
                metric_name=std_name,
                value=item.value,
                unit=item.unit,
                ref_min=ref_min,
                ref_max=ref_max,
                is_abnormal=check_is_abnormal(item.value, ref_min, ref_max),
                notes=item.notes,
            ))

    await db.flush()

    rr = await db.execute(
        select(Report)
        .options(selectinload(Report.results))
        .where(Report.id == report_id)
    )
    return rr.scalar_one()


@router.delete("/{report_id}")
async def delete_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(Report).join(Patient).where(Report.id == report_id, Patient.user_id == user.id)
    r = await db.execute(q)
    report = r.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    await db.delete(report)
    await db.flush()
    return {"message": "删除成功"}
