from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    ForeignKey, Enum, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from database import Base


class UserRole(str, enum.Enum):
    manager = "manager"
    hr = "hr"
    admin = "admin"


class NoveltyStatus(str, enum.Enum):
    pendiente = "pendiente"
    aprobado = "aprobado"


class DepartmentStatus(str, enum.Enum):
    pendiente = "pendiente"
    enviado = "enviado"
    aprobado = "aprobado"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.manager)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    managed_departments = relationship("ManagerDepartment", back_populates="user")


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    short_name = Column(String, nullable=False)   # e.g. "CAMU"
    full_name = Column(String, nullable=False)    # e.g. "Constructora y Comercializadora CAMU S.A.S"
    nit = Column(String)                          # e.g. "900.062.553-1"
    sheet_name = Column(String)                   # Excel sheet name: "CAMU", "ALICANTE", etc.
    is_active = Column(Boolean, default=True)

    departments = relationship("Department", back_populates="company")
    employees = relationship("Employee", back_populates="company")


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)         # e.g. "PRESIDENCIA"
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    is_active = Column(Boolean, default=True)

    company = relationship("Company", back_populates="departments")
    employees = relationship("Employee", back_populates="department")
    managers = relationship("ManagerDepartment", back_populates="department")
    submission_statuses = relationship("DepartmentSubmission", back_populates="department")


class ManagerDepartment(Base):
    __tablename__ = "manager_departments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

    user = relationship("User", back_populates="managed_departments")
    department = relationship("Department", back_populates="managers")

    __table_args__ = (UniqueConstraint("user_id", "department_id"),)


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    cedula = Column(String, nullable=False)          # Empleado: ID
    internal_code = Column(String)                   # ID (e.g. 00.316.976)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    project_code = Column(String)                    # Código proyecto
    cargo = Column(String)
    is_active = Column(Boolean, default=True)

    department = relationship("Department", back_populates="employees")
    company = relationship("Company", back_populates="employees")
    novelties = relationship("Novelty", back_populates="employee")


class PayPeriod(Base):
    __tablename__ = "pay_periods"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)          # 1-12
    month_name = Column(String, nullable=False)      # e.g. "Febrero"
    period_number = Column(Integer, nullable=False)  # 1 or 2
    period_label = Column(String, nullable=False)    # "Primera Quincena" / "Segunda Quincena"
    is_active = Column(Boolean, default=True)

    novelties = relationship("Novelty", back_populates="period")
    submissions = relationship("DepartmentSubmission", back_populates="period")

    __table_args__ = (UniqueConstraint("year", "month", "period_number"),)


class DepartmentSubmission(Base):
    """Tracks whether a department has submitted novelties for a period."""
    __tablename__ = "department_submissions"

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    period_id = Column(Integer, ForeignKey("pay_periods.id"), nullable=False)
    status = Column(Enum(DepartmentStatus), default=DepartmentStatus.pendiente)
    submitted_at = Column(DateTime(timezone=True))
    submitted_by_id = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    approved_by_id = Column(Integer, ForeignKey("users.id"))

    department = relationship("Department", back_populates="submission_statuses")
    period = relationship("PayPeriod", back_populates="submissions")
    submitted_by = relationship("User", foreign_keys=[submitted_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])

    __table_args__ = (UniqueConstraint("department_id", "period_id"),)


class Novelty(Base):
    __tablename__ = "novelties"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    period_id = Column(Integer, ForeignKey("pay_periods.id"), nullable=False)
    num_dias = Column(Float, default=15.0)
    horas_extras_diurnas = Column(Float, nullable=True)
    horas_extras_nocturnas = Column(Float, nullable=True)
    horas_extras_dom_fest = Column(Float, nullable=True)
    horas_extras_dom_fest_noct = Column(Float, nullable=True)
    observaciones = Column(Text, nullable=True)
    observaciones_aprobacion = Column(Text, nullable=True)
    status = Column(Enum(NoveltyStatus), default=NoveltyStatus.pendiente)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True))
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    employee = relationship("Employee", back_populates="novelties")
    period = relationship("PayPeriod", back_populates="novelties")
    approved_by = relationship("User", foreign_keys=[approved_by_id])

    __table_args__ = (UniqueConstraint("employee_id", "period_id"),)
