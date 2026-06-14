from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.database import get_db
from backend.models import MedicationRecord, MedicationItem, Patient, User
from backend.schemas.medication import (
    MedicationRecordCreate, MedicationRecordUpdate,
    MedicationRecordResponse, MedicationRecordSummary,
    MedicationCompareResponse, DrugCompareItem,
    MedicationTimelineResponse, DrugTimelineEntry,
)
from backend.core.auth import get_current_user

router = APIRouter(prefix="/api/medications", tags=["medications"])


async def _get_record_or_404(record_id: int, user: User, db: AsyncSession):
    r = await db.execute(
        select(MedicationRecord)
        .join(Patient)
        .where(MedicationRecord.id == record_id, Patient.user_id == user.id)
    )
    record = r.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="用药记录不存在")
    return record


@router.get("/", response_model=list[MedicationRecordSummary])
async def list_records(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    pr = await db.execute(
        select(Patient).where(Patient.id == patient_id, Patient.user_id == user.id)
    )
    if not pr.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="无权访问")

    q = (
        select(
            MedicationRecord.id,
            MedicationRecord.patient_id,
            MedicationRecord.doctor,
            MedicationRecord.start_date,
            MedicationRecord.created_at,
            func.count(MedicationItem.id).label("item_count"),
        )
        .outerjoin(MedicationItem, MedicationItem.record_id == MedicationRecord.id)
        .where(MedicationRecord.patient_id == patient_id)
        .group_by(MedicationRecord.id)
        .order_by(desc(MedicationRecord.created_at))
    )
    rows = await db.execute(q)
    rows = rows.all()

    return [
        MedicationRecordSummary(
            id=r.id,
            patient_id=r.patient_id,
            doctor=r.doctor,
            start_date=r.start_date,
            item_count=r.item_count,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.get("/{record_id}", response_model=MedicationRecordResponse)
async def get_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    r = await db.execute(
        select(MedicationRecord)
        .options(selectinload(MedicationRecord.items))
        .join(Patient)
        .where(MedicationRecord.id == record_id, Patient.user_id == user.id)
    )
    record = r.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="用药记录不存在")
    return record


@router.post("/", response_model=MedicationCompareResponse)
async def create_record(
    data: MedicationRecordCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    pr = await db.execute(
        select(Patient).where(Patient.id == data.patient_id, Patient.user_id == user.id)
    )
    if not pr.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="患者不存在")

    record = MedicationRecord(
        patient_id=data.patient_id,
        doctor=data.doctor,
        start_date=data.start_date,
        notes=data.notes,
    )
    db.add(record)
    await db.flush()

    for idx, item in enumerate(data.items):
        db.add(MedicationItem(
            record_id=record.id,
            drug_name=item.drug_name,
            specification=item.specification,
            dosage=item.dosage,
            usage_method=item.usage_method,
            notes=item.notes,
            sort_order=idx,
        ))

    await db.flush()
    await db.refresh(record)

    rr = await db.execute(
        select(MedicationRecord)
        .options(selectinload(MedicationRecord.items))
        .where(MedicationRecord.id == record.id)
    )
    current = rr.scalar_one()

    prev_r = await db.execute(
        select(MedicationRecord)
        .options(selectinload(MedicationRecord.items))
        .where(
            MedicationRecord.patient_id == data.patient_id,
            MedicationRecord.id != record.id,
        )
        .order_by(desc(MedicationRecord.created_at))
        .limit(1)
    )
    prev = prev_r.scalar_one_or_none()

    compared_items = _build_compare(prev, current)

    return MedicationCompareResponse(
        record=current,
        prev_record=prev,
        compared_items=compared_items,
    )


@router.put("/{record_id}", response_model=MedicationRecordResponse)
async def update_record(
    record_id: int,
    data: MedicationRecordUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    record = await _get_record_or_404(record_id, user, db)

    if data.doctor is not None:
        record.doctor = data.doctor
    if data.start_date is not None:
        record.start_date = data.start_date
    if data.notes is not None:
        record.notes = data.notes

    if data.items is not None:
        await db.execute(delete(MedicationItem).where(MedicationItem.record_id == record_id))
        for idx, item in enumerate(data.items):
            db.add(MedicationItem(
                record_id=record_id,
                drug_name=item.drug_name,
                specification=item.specification,
                dosage=item.dosage,
                usage_method=item.usage_method,
                notes=item.notes,
                sort_order=idx,
            ))

    await db.flush()
    await db.refresh(record)

    rr = await db.execute(
        select(MedicationRecord)
        .options(selectinload(MedicationRecord.items))
        .where(MedicationRecord.id == record_id)
    )
    return rr.scalar_one()


@router.delete("/{record_id}")
async def delete_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    record = await _get_record_or_404(record_id, user, db)
    await db.delete(record)
    await db.flush()
    return {"message": "删除成功"}


def _build_compare(prev: MedicationRecord | None, curr: MedicationRecord) -> list[DrugCompareItem]:
    if prev is None or not prev.items:
        return [
            DrugCompareItem(
                drug_name=item.drug_name,
                dosage=item.dosage,
                status="new",
                curr_dosage=item.dosage,
                curr_specification=item.specification,
            )
            for item in curr.items
        ]

    prev_map: dict[str, tuple[str, str]] = {}
    for item in prev.items:
        key = item.drug_name.strip()
        prev_map[key] = (item.dosage, item.specification)

    result: list[DrugCompareItem] = []
    curr_keys: set[str] = set()

    for item in curr.items:
        key = item.drug_name.strip()
        curr_keys.add(key)
        if key in prev_map:
            prev_dosage, prev_spec = prev_map[key]
            if item.dosage != prev_dosage:
                result.append(DrugCompareItem(
                    drug_name=item.drug_name,
                    dosage=item.dosage,
                    status="changed",
                    prev_dosage=prev_dosage,
                    prev_specification=prev_spec,
                    curr_dosage=item.dosage,
                    curr_specification=item.specification,
                ))
            else:
                result.append(DrugCompareItem(
                    drug_name=item.drug_name,
                    dosage=item.dosage,
                    status="unchanged",
                    prev_dosage=prev_dosage,
                    prev_specification=prev_spec,
                    curr_dosage=item.dosage,
                    curr_specification=item.specification,
                ))
        else:
            result.append(DrugCompareItem(
                drug_name=item.drug_name,
                dosage=item.dosage,
                status="new",
                curr_dosage=item.dosage,
                curr_specification=item.specification,
            ))

    for key, (dosage, spec) in prev_map.items():
        if key not in curr_keys:
            result.append(DrugCompareItem(
                drug_name=key,
                dosage=dosage,
                status="removed",
                prev_dosage=dosage,
                prev_specification=spec,
            ))

    return result


@router.get("/timeline/{patient_id}", response_model=MedicationTimelineResponse)
async def medication_timeline(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    pr = await db.execute(
        select(Patient).where(Patient.id == patient_id, Patient.user_id == user.id)
    )
    if not pr.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="无权访问")

    recs_r = await db.execute(
        select(MedicationRecord)
        .options(selectinload(MedicationRecord.items))
        .where(MedicationRecord.patient_id == patient_id)
        .order_by(desc(MedicationRecord.created_at))
    )
    records = recs_r.scalars().all()

    entries: list[DrugTimelineEntry] = []
    prev_items_map: dict[str, dict] = {}

    for record in reversed(records):
        current_items = {}
        for item in record.items:
            key = item.drug_name.strip()
            current_items[key] = item

            if key in prev_items_map:
                prev = prev_items_map[key]
                status = "changed" if item.dosage != prev["dosage"] else "unchanged"
                entries.append(DrugTimelineEntry(
                    date=str(record.created_at.date()),
                    date_type="change" if status == "changed" else "last",
                    doctor=record.doctor,
                    drug_name=item.drug_name,
                    dosage=item.dosage,
                    specification=item.specification,
                    usage_method=item.usage_method,
                    status=status,
                    prev_dosage=prev["dosage"],
                ))
            else:
                entries.append(DrugTimelineEntry(
                    date=str(record.created_at.date()),
                    date_type="start",
                    doctor=record.doctor,
                    drug_name=item.drug_name,
                    dosage=item.dosage,
                    specification=item.specification,
                    usage_method=item.usage_method,
                    status="new",
                ))

        prev_items_map = {k: {"dosage": v.dosage, "specification": v.specification} for k, v in current_items.items()}

    return MedicationTimelineResponse(patient_id=patient_id, entries=entries)
