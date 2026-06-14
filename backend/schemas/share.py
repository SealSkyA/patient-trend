from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class TrendDataPoint(BaseModel):
    date: date
    value: float
    unit: str
    ref_min: Optional[float]
    ref_max: Optional[float]
    is_abnormal: bool
    institution: Optional[str]
    notes: Optional[str]


class MetricWithAbnormalCount(BaseModel):
    metric_name: str
    abnormal_count: int


class TrendResponse(BaseModel):
    metric_name: str
    unit: str
    ref_min: Optional[float]
    ref_max: Optional[float]
    trend_line: Optional[List[float]] = None
    direction: str = "stable"
    data_points: List[TrendDataPoint]


class ShareCreate(BaseModel):
    patient_id: int
    metric_names: Optional[List[str]] = None
    expire_days: int = 7


class ShareResponse(BaseModel):
    token: str
    expires_at: datetime
    url: str


class SharePatientInfo(BaseModel):
    name: str
    gender: Optional[str]
    birth_date: Optional[date]


class ShareTrendData(BaseModel):
    metric_name: str
    unit: str
    ref_min: Optional[float]
    ref_max: Optional[float]
    data_points: List[TrendDataPoint]


class ShareDetail(BaseModel):
    patient_info: SharePatientInfo
    trends: List[ShareTrendData]
    expires_at: datetime
