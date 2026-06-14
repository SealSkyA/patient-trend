from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TemplateItemData(BaseModel):
    metric_name: str
    unit: str = ""
    ref_min: Optional[float] = None
    ref_max: Optional[float] = None
    notes: Optional[str] = None
    sort_order: int = 0


class TemplateCreate(BaseModel):
    name: str
    items: List[TemplateItemData]


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    items: Optional[List[TemplateItemData]] = None


class TemplateItemResponse(BaseModel):
    id: int
    metric_name: str
    unit: str
    ref_min: Optional[float]
    ref_max: Optional[float]
    notes: Optional[str]
    sort_order: int

    class Config:
        from_attributes = True


class TemplateResponse(BaseModel):
    id: int
    name: str
    is_preset: bool
    created_at: datetime
    items: List[TemplateItemResponse] = []

    class Config:
        from_attributes = True


class PresetResponse(BaseModel):
    name: str
    metrics: List[str]
