from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.models import Patient, User
from backend.schemas.patient import PatientCreate, PatientUpdate, PatientResponse
from backend.core.auth import get_current_user

router = APIRouter(prefix="/api/patients", tags=["patients"])


async def verify_patient_owner(patient: Patient, user: User):
    if patient.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权访问该患者")
    return patient


@router.get("/", response_model=list[PatientResponse])
async def list_patients(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Patient).where(Patient.user_id == user.id).order_by(Patient.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=PatientResponse)
async def create_patient(
    data: PatientCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    patient = Patient(user_id=user.id, **data.model_dump())
    db.add(patient)
    await db.flush()
    await db.refresh(patient)
    return patient


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    data: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    await verify_patient_owner(patient, user)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)
    await db.flush()
    await db.refresh(patient)
    return patient


@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")
    await verify_patient_owner(patient, user)

    await db.delete(patient)
    await db.flush()
    return {"message": "删除成功"}
