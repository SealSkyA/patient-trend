from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class MedicationItemData(BaseModel):
    drug_name: str
    specification: str = ""
    dosage: str = ""
    usage_method: str = ""
    notes: Optional[str] = None


class MedicationRecordCreate(BaseModel):
    patient_id: int
    doctor: str
    start_date: Optional[date] = None
    notes: Optional[str] = None
    items: List[MedicationItemData] = []


class MedicationRecordUpdate(BaseModel):
    doctor: Optional[str] = None
    start_date: Optional[date] = None
    notes: Optional[str] = None
    items: Optional[List[MedicationItemData]] = None


class MedicationItemResponse(BaseModel):
    id: int
    drug_name: str
    specification: str
    dosage: str
    usage_method: str
    notes: Optional[str]
    sort_order: int

    class Config:
        from_attributes = True


class MedicationRecordResponse(BaseModel):
    id: int
    patient_id: int
    doctor: str
    start_date: Optional[date]
    notes: Optional[str]
    created_at: datetime
    items: List[MedicationItemResponse] = []

    class Config:
        from_attributes = True


class MedicationRecordSummary(BaseModel):
    id: int
    patient_id: int
    doctor: str
    start_date: Optional[date]
    item_count: int
    created_at: datetime


class DrugCompareItem(BaseModel):
    drug_name: str
    dosage: str
    status: str  # "new" | "changed" | "unchanged" | "removed"
    prev_dosage: Optional[str] = None
    prev_specification: Optional[str] = None
    curr_dosage: Optional[str] = None
    curr_specification: Optional[str] = None


class MedicationCompareResponse(BaseModel):
    record: MedicationRecordResponse
    prev_record: Optional[MedicationRecordResponse] = None
    compared_items: List[DrugCompareItem] = []


class DrugTimelineEntry(BaseModel):
    date: str
    date_type: str  # "start" | "change" | "last"
    doctor: str
    drug_name: str
    dosage: str
    specification: str
    usage_method: str
    status: str  # "new" | "changed" | "unchanged" | "removed"
    prev_dosage: Optional[str] = None


class MedicationTimelineResponse(BaseModel):
    patient_id: int
    entries: List[DrugTimelineEntry] = []
