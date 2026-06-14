from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class ResultItem(BaseModel):
    metric_name: str
    value: float
    unit: str = ""
    ref_min: Optional[float] = None
    ref_max: Optional[float] = None
    notes: Optional[str] = None


class ReportCreate(BaseModel):
    patient_id: int
    institution: str
    exam_date: date
    results: List[ResultItem] = []
    notes: Optional[str] = None


class ReportUpdate(BaseModel):
    institution: Optional[str] = None
    exam_date: Optional[date] = None
    results: Optional[List[ResultItem]] = None
    notes: Optional[str] = None


class ResultResponse(BaseModel):
    id: int
    metric_name: str
    value: float
    unit: str
    ref_min: Optional[float]
    ref_max: Optional[float]
    is_abnormal: Optional[bool]
    notes: Optional[str]

    class Config:
        from_attributes = True


class ReportResponse(BaseModel):
    id: int
    patient_id: int
    institution: str
    exam_date: date
    file_path: Optional[str]
    notes: Optional[str]
    created_at: datetime
    results: Optional[List[ResultResponse]] = []

    class Config:
        from_attributes = True


class ReportSummary(BaseModel):
    id: int
    institution: str
    exam_date: date
    metric_count: int
    abnormal_count: int
