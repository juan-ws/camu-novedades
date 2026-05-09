from fastapi import APIRouter, Depends, Request, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import csv
import io

from database import get_db
from auth import get_current_user, require_admin, hash_password
import models

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def admin_home(
    request: Request,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role not in (models.UserRole.admin, models.UserRole.hr):
        raise HTTPException(403)
    companies = db.query(models.Company).all()
    departments = db.query(models.Department).all()
    employees = db.query(models.Employee).filter(models.Employee.is_active == True).all()
    users = db.query(models.User).all()
    periods = db.query(models.PayPeriod).order_by(
        models.PayPeriod.year.desc(), models.PayPeriod.month.desc(), models.PayPeriod.period_number.desc()
    ).all()
    return templates.TemplateResponse("admin/index.html", {
        "request": request,
        "user": user,
        "companies": companies,
        "departments": departments,
        "employees": employees,
        "users": users,
        "periods": periods,
    })


# ── Pay Periods ──────────────────────────────────────────────

MONTH_NAMES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


@router.post("/periods/create")
async def create_period(
    year: int = Form(...),
    month: int = Form(...),
    period_number: int = Form(...),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role not in (models.UserRole.admin, models.UserRole.hr):
        raise HTTPException(403)
    existing = db.query(models.PayPeriod).filter(
        models.PayPeriod.year == year,
        models.PayPeriod.month == month,
        models.PayPeriod.period_number == period_number,
    ).first()
    if existing:
        return RedirectResponse(url="/admin/?error=period_exists", status_code=302)
    period = models.PayPeriod(
        year=year,
        month=month,
        month_name=MONTH_NAMES.get(month, str(month)),
        period_number=period_number,
        period_label="Primera Quincena" if period_number == 1 else "Segunda Quincena",
    )
    db.add(period)
    db.commit()
    return RedirectResponse(url="/admin/", status_code=302)


# ── Users ─────────────────────────────────────────────────────

@router.post("/users/create")
async def create_user(
    username: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if db.query(models.User).filter(models.User.username == username).first():
        return RedirectResponse(url="/admin/?error=user_exists", status_code=302)
    new_user = models.User(
        username=username,
        full_name=full_name,
        password_hash=hash_password(password),
        role=models.UserRole(role),
    )
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/admin/", status_code=302)


@router.post("/users/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    new_password: str = Form(...),
    user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    target = db.query(models.User).filter(models.User.id == user_id).first()
    if not target:
        raise HTTPException(404)
    target.password_hash = hash_password(new_password)
    db.commit()
    return RedirectResponse(url="/admin/", status_code=302)


@router.post("/users/{user_id}/departments")
async def assign_departments(
    user_id: int,
    request: Request,
    user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    form = await request.form()
    dept_ids = [int(v) for k, v in form.multi_items() if k == "dept_ids"]
    db.query(models.ManagerDepartment).filter(
        models.ManagerDepartment.user_id == user_id
    ).delete()
    for dept_id in dept_ids:
        db.add(models.ManagerDepartment(user_id=user_id, department_id=dept_id))
    db.commit()
    return RedirectResponse(url="/admin/", status_code=302)


# ── Departments ───────────────────────────────────────────────

@router.post("/departments/create")
async def create_department(
    name: str = Form(...),
    company_id: int = Form(...),
    user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    dept = models.Department(name=name.upper(), company_id=company_id)
    db.add(dept)
    db.commit()
    return RedirectResponse(url="/admin/", status_code=302)


# ── Employees ─────────────────────────────────────────────────

@router.post("/employees/create")
async def create_employee(
    full_name: str = Form(...),
    cedula: str = Form(...),
    internal_code: str = Form(""),
    department_id: int = Form(...),
    company_id: int = Form(...),
    project_code: str = Form(""),
    cargo: str = Form(""),
    user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    emp = models.Employee(
        full_name=full_name,
        cedula=cedula,
        internal_code=internal_code or None,
        department_id=department_id,
        company_id=company_id,
        project_code=project_code or None,
        cargo=cargo or None,
    )
    db.add(emp)
    db.commit()
    return RedirectResponse(url="/admin/", status_code=302)


@router.post("/employees/{emp_id}/toggle")
async def toggle_employee(
    emp_id: int,
    user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    emp = db.query(models.Employee).filter(models.Employee.id == emp_id).first()
    if emp:
        emp.is_active = not emp.is_active
        db.commit()
    return RedirectResponse(url="/admin/", status_code=302)


@router.post("/employees/import")
async def import_employees(
    file: UploadFile = File(...),
    user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Import employees from CSV. Expected columns:
    full_name, cedula, internal_code, department_name, company_short_name, project_code, cargo
    """
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    imported = 0
    for row in reader:
        company = db.query(models.Company).filter(
            models.Company.short_name == row.get("company_short_name", "").strip()
        ).first()
        if not company:
            continue
        dept = db.query(models.Department).filter(
            models.Department.name == row.get("department_name", "").strip().upper(),
            models.Department.company_id == company.id,
        ).first()
        if not dept:
            dept = models.Department(
                name=row.get("department_name", "").strip().upper(),
                company_id=company.id,
            )
            db.add(dept)
            db.flush()

        cedula = str(row.get("cedula", "")).strip()
        existing = db.query(models.Employee).filter(
            models.Employee.cedula == cedula,
            models.Employee.company_id == company.id,
        ).first()
        if existing:
            continue

        emp = models.Employee(
            full_name=row.get("full_name", "").strip(),
            cedula=cedula,
            internal_code=row.get("internal_code", "").strip() or None,
            department_id=dept.id,
            company_id=company.id,
            project_code=row.get("project_code", "").strip() or None,
            cargo=row.get("cargo", "").strip() or None,
        )
        db.add(emp)
        imported += 1

    db.commit()
    return RedirectResponse(url=f"/admin/?imported={imported}", status_code=302)
