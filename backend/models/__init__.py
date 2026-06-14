from __future__ import annotations
from typing import List, Optional
from sqlalchemy import String, Integer, BigInteger, Boolean, Date, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column, DeclarativeBase
from datetime import datetime
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    patients: Mapped[List["Patient"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    templates: Mapped[List["Template"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    gender: Mapped[Optional[str]] = mapped_column(String(10))
    birth_date: Mapped[Optional[datetime]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="patients")
    reports: Mapped[List["Report"]] = relationship(back_populates="patient", cascade="all, delete-orphan")
    medication_records: Mapped[List["MedicationRecord"]] = relationship(back_populates="patient", cascade="all, delete-orphan")
    share_tokens: Mapped[List["ShareToken"]] = relationship(back_populates="patient", cascade="all, delete-orphan")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("patients.id"), nullable=False)
    institution: Mapped[str] = mapped_column(String(100), nullable=False)
    exam_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String(255))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    patient: Mapped["Patient"] = relationship(back_populates="reports")
    results: Mapped[List["Result"]] = relationship(back_populates="report", cascade="all, delete-orphan")


class Result(Base):
    __tablename__ = "results"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    report_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("reports.id"), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    ref_min: Mapped[Optional[float]] = mapped_column(Float)
    ref_max: Mapped[Optional[float]] = mapped_column(Float)
    is_abnormal: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    report: Mapped["Report"] = relationship(back_populates="results")


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_preset: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="templates")
    items: Mapped[List["TemplateItem"]] = relationship(back_populates="template", cascade="all, delete-orphan")


class TemplateItem(Base):
    __tablename__ = "template_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("templates.id"), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(50), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    ref_min: Mapped[Optional[float]] = mapped_column(Float)
    ref_max: Mapped[Optional[float]] = mapped_column(Float)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    template: Mapped["Template"] = relationship(back_populates="items")


class ShareToken(Base):
    __tablename__ = "share_tokens"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    patient_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("patients.id"), nullable=False)
    metric_names: Mapped[Optional[str]] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    patient: Mapped["Patient"] = relationship(back_populates="share_tokens")


class MedicationRecord(Base):
    __tablename__ = "medication_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("patients.id"), nullable=False)
    doctor: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[Optional[datetime]] = mapped_column(Date)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    patient: Mapped["Patient"] = relationship(back_populates="medication_records")
    items: Mapped[List["MedicationItem"]] = relationship(back_populates="record", cascade="all, delete-orphan")


class MedicationItem(Base):
    __tablename__ = "medication_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("medication_records.id"), nullable=False)
    drug_name: Mapped[str] = mapped_column(String(100), nullable=False)
    specification: Mapped[str] = mapped_column(String(100), default="")
    dosage: Mapped[str] = mapped_column(String(50), default="")
    usage_method: Mapped[str] = mapped_column(String(200), default="")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    record: Mapped["MedicationRecord"] = relationship(back_populates="items")
