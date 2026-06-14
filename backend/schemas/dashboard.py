from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

class AnomalyItem(BaseModel):
    metric_name: str
    value: float
    unit: str
    exam_date: date
    institution: Optional[str] = None
    ref_min: Optional[float] = None
    ref_max: Optional[float] = None
    is_high: Optional[bool] = None

class AnomalyDetail(BaseModel):
    id: int
    exam_date: date
    institution: str
    metric_name: str
    value: float
    unit: str
    ref_min: Optional[float] = None
    ref_max: Optional[float] = None
    is_high: bool

class WatchItem(BaseModel):
    metric_name: str
    recent_values: List[float]
    recent_dates: List[date]
    direction: str
    warning: str

class LatestReportSummary(BaseModel):
    id: int
    exam_date: date
    institution: str
    metric_count: int
    abnormal_count: int

class MedicationCompareDrug(BaseModel):
    drug_name: str
    dosage: str
    specification: str
    usage_method: str
    status: str  # new / changed / unchanged / removed
    prev_dosage: Optional[str] = None
    prev_specification: Optional[str] = None

class MedicationCompare(BaseModel):
    record_id: int
    doctor: str
    created_at: datetime
    drugs: List[MedicationCompareDrug] = []
    previous_record: Optional[dict] = None  # 包含上一次用药的完整信息

class DashboardResponse(BaseModel):
    patient_id: int
    patient_name: str
    total_reports: int
    total_anomalies: int
    anomalies: List[AnomalyItem] = []
    anomaly_details: List[AnomalyDetail] = []
    latest_report: Optional[LatestReportSummary] = None
    watch_list: List[WatchItem] = []
    recent_reports: List[LatestReportSummary] = []
    medication_compare: Optional[MedicationCompare] = None
