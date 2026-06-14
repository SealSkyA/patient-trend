from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.database import get_db
from backend.models import Result, Report, Patient, User, MedicationRecord, MedicationItem
from backend.schemas.dashboard import (
    DashboardResponse, AnomalyItem, AnomalyDetail, WatchItem, LatestReportSummary,
    MedicationCompare, MedicationCompareDrug,
)
from backend.core.auth import get_current_user
from datetime import date, timedelta

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/{patient_id}", response_model=DashboardResponse)
async def dashboard(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    patient_r = await db.execute(
        select(Patient).where(Patient.id == patient_id, Patient.user_id == user.id)
    )
    patient = patient_r.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    total_reports_r = await db.execute(
        select(func.count()).select_from(Report).where(Report.patient_id == patient_id)
    )
    total_reports = total_reports_r.scalar() or 0

    # 总异常指标数
    total_anomalies_r = await db.execute(
        select(func.count()).select_from(Result)
        .join(Report, Result.report_id == Report.id)
        .where(Report.patient_id == patient_id, Result.is_abnormal == True)
    )
    total_anomalies = total_anomalies_r.scalar() or 0

    anomalies: list[AnomalyItem] = []
    anomaly_details: list[AnomalyDetail] = []
    report_summaries = []
    
    # 查询近 1 年的报告
    one_year_ago = date.today() - timedelta(days=365)
    reports_r = await db.execute(
        select(Report)
        .where(
            Report.patient_id == patient_id,
            Report.exam_date >= one_year_ago
        )
        .order_by(Report.exam_date.desc())
    )
    reports = reports_r.scalars().all()

    for report in reports:
        results_r = await db.execute(
            select(Result).where(Result.report_id == report.id)
        )
        results = results_r.scalars().all()

        abnormal_count = sum(1 for r in results if r.is_abnormal)
        report_summaries.append(LatestReportSummary(
            id=report.id,
            exam_date=report.exam_date,
            institution=report.institution,
            metric_count=len(results),
            abnormal_count=abnormal_count,
        ))

        for r in results:
            if r.is_abnormal:
                if len(anomalies) < 10:
                    is_high = r.value > (r.ref_max or 0) if r.ref_max else False
                    anomalies.append(AnomalyItem(
                        metric_name=r.metric_name,
                        value=r.value,
                        unit=r.unit,
                        exam_date=report.exam_date,
                        institution=report.institution,
                        ref_min=r.ref_min,
                        ref_max=r.ref_max,
                        is_high=is_high,
                    ))
                
                anomaly_details.append(AnomalyDetail(
                    id=report.id,
                    exam_date=report.exam_date,
                    institution=report.institution,
                    metric_name=r.metric_name,
                    value=r.value,
                    unit=r.unit,
                    ref_min=r.ref_min,
                    ref_max=r.ref_max,
                    is_high=r.ref_max and r.value > r.ref_max if r.ref_max else (r.ref_min and r.value < r.ref_min if r.ref_min else False),
                ))

    anomaly_details.sort(key=lambda x: x.exam_date, reverse=True)

    watch_list: list[WatchItem] = []
    abnormal_metrics_q = (
        select(Result.metric_name)
        .join(Report, Result.report_id == Report.id)
        .where(
            Report.patient_id == patient_id,
            Result.is_abnormal == True,
        )
        .group_by(Result.metric_name)
    )
    abnormal_metrics = await db.execute(abnormal_metrics_q)
    abnormal_metrics = abnormal_metrics.scalars().all()
    
    for metric_name in abnormal_metrics:
        ts_r = await db.execute(
            select(Result.value, Report.exam_date)
            .join(Report, Result.report_id == Report.id)
            .where(
                Result.metric_name == metric_name,
                Report.patient_id == patient_id,
            )
            .order_by(desc(Report.exam_date))
            .limit(2)
        )
        records = ts_r.all()
        if len(records) >= 2:
            vals = [r[0] for r in records]
            dates = [r[1] for r in records]
            if vals[0] > vals[1]:
                watch_list.append(WatchItem(
                    metric_name=metric_name,
                    recent_values=list(reversed(vals)),
                    recent_dates=list(reversed(dates)),
                    direction="up",
                    warning="近期上升",
                ))
            elif vals[0] < vals[1]:
                watch_list.append(WatchItem(
                    metric_name=metric_name,
                    recent_values=list(reversed(vals)),
                    recent_dates=list(reversed(dates)),
                    direction="down",
                    warning="近期下降",
                ))

    medication_compare = None
    med_r = await db.execute(
        select(MedicationRecord)
        .options(selectinload(MedicationRecord.items))
        .where(MedicationRecord.patient_id == patient_id)
        .order_by(desc(MedicationRecord.created_at))
        .limit(2)
    )
    med_records = med_r.scalars().all()

    if med_records:
        latest = med_records[0]
        prev = med_records[1] if len(med_records) > 1 else None

        prev_map: dict[str, dict] = {}
        if prev and prev.items:
            for item in prev.items:
                prev_map[item.drug_name.strip()] = {"dosage": item.dosage, "specification": item.specification}

        # 构建上一次用药的完整信息
        previous_record = None
        if prev:
            previous_record = {
                "id": prev.id,
                "doctor": prev.doctor,
                "created_at": prev.created_at.isoformat() if prev.created_at else None,
                "drugs": [
                    {
                        "drug_name": item.drug_name,
                        "specification": item.specification,
                        "dosage": item.dosage,
                        "usage_method": item.usage_method,
                        "notes": item.notes,
                    }
                    for item in prev.items
                ]
            }

        drugs = []
        current_keys = set()
        for item in latest.items:
            key = item.drug_name.strip()
            current_keys.add(key)
            if key in prev_map:
                p = prev_map[key]
                dosage_changed = item.dosage != p["dosage"]
                drugs.append(MedicationCompareDrug(
                    drug_name=item.drug_name,
                    dosage=item.dosage,
                    specification=item.specification,
                    usage_method=item.usage_method,
                    status="changed" if dosage_changed else "unchanged",
                    prev_dosage=p["dosage"],
                    prev_specification=p["specification"],
                ))
            else:
                drugs.append(MedicationCompareDrug(
                    drug_name=item.drug_name, dosage=item.dosage,
                    specification=item.specification, usage_method=item.usage_method,
                    status="new",
                ))

        if prev_map:
            for key, p in prev_map.items():
                if key not in current_keys:
                    drugs.append(MedicationCompareDrug(
                        drug_name=key, dosage=p["dosage"],
                        specification=p["specification"], usage_method="",
                        status="removed", prev_dosage=p["dosage"],
                        prev_specification=p["specification"],
                    ))

        medication_compare = MedicationCompare(
            record_id=latest.id, doctor=latest.doctor,
            created_at=latest.created_at, drugs=drugs,
            previous_record=previous_record,
        )

    return DashboardResponse(
        patient_id=patient_id,
        patient_name=patient.name,
        total_reports=total_reports,
        total_anomalies=total_anomalies,
        anomalies=anomalies[:10],
        anomaly_details=anomaly_details[:100],
        latest_report=report_summaries[0] if report_summaries else None,
        watch_list=watch_list,
        recent_reports=report_summaries[:5],
        medication_compare=medication_compare,
    )
