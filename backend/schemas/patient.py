from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class PatientCreate(BaseModel):
    name: str
    gender: Optional[str] = None
    birth_date: Optional[date] = None


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None


class PatientResponse(BaseModel):
    id: int
    name: str
    gender: Optional[str]
    birth_date: Optional[date]
    created_at: datetime

    class Config:
        from_attributes = True
