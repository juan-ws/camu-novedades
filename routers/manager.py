from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import Optional
from datetime import datetime

from database import get_db
from auth import get_current_user
import models

router = APIRouter(prefix="/manager", tags=["manager"])
templates = Jinja2Templates(directory="templates")


def get_manager_departments(user: models.User, db: Session):
    links = db.query(models.ManagerDepartment).filter(
        models.ManagerDepartment.user_id == user.id
    ).all()
    return [link.department for link in links]


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    departments = get_manager_departments(user, db)
    periods = db.query(models.PayPeriod).filter(
        models.PayPeriod.is_active == True
    ).order_by(models.PayPeriod.year.desc(), models.PayPeriod.month.desc(), models.PayPeriod.period_number.desc()).all()

    dept_summaries = []
    for dept in departments:
        for period in periods:
            sub = db.query(models.DepartmentSubmission).filter(
                models.DepartmentSubmission.department_id == dept.id,
                models.DepartmentSubmission.period_id == period.id,
            ).first()
            emp_count = db.query(func.count(models.Employee.id)).filter(
                models.Employee.department_id == dept.id,
                models.Employee.is_active == True,
            ).scalar()
            novelty_count = db.query(func.count(models.Novelty.id)).filter(
                models.Novelty.period_id == period.id,
                models.Novelty.employee_id.in_(
                    db.query(models.Employee.id).filter(
                        models.Employee.department_id == dept.id,
                        models.Employee.is_active == True,
                    )
                ),
            ).scalar()
            dept_summaries.append({
                "department": dept,
                "period": period,
                "submission": sub,
                "emp_count": emp_count,
                "novelty_count": novelty_count,
            })

    return templates.TemplateResponse("manager/dashboard.html", {
        "request": request,
        "user": user,
        "dept_summaries": dept_summaries,
        "periods": periods,
    })


@router.get("/novelties/{dept_id}/{period_id}", response_class=HTMLResponse)
async def novelties_form(
    request: Request,
    dept_id: int,
    period_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dept = db.query(models.Department).filter(models.Department.id == dept_id).first()
    if not dept:
        raise HTTPException(404, "Departamento no encontrado")

    # verify manager owns this dept
    link = db.query(models.ManagerDepartment).filter(
        models.ManagerDepartment.user_id == user.id,
        models.ManagerDepartment.department_id == dept_id,
    ).first()
    if not link and user.role == models.UserRole.manager:
        raise HTTPException(403, "No tiene acceso a este departamento")

    period = db.query(models.PayPeriod).filter(models.PayPeriod.id == period_id).first()
    if not period:
        raise HTTPException(404, "Período no encontrado")

    submission = db.query(models.DepartmentSubmission).filter(
        models.DepartmentSubmission.department_id == dept_id,
        models.DepartmentSubmission.period_id == period_id,
    ).first()

    employees = db.query(models.Employee).filter(
        models.Employee.department_id == dept_id,
        models.Employee.is_active == True,
    ).order_by(models.Employee.full_name).all()

    novelties = {
        n.employee_id: n
        for n in db.query(models.Novelty).filter(
            models.Novelty.period_id == period_id,
            models.Novelty.employee_id.in_([e.id for e in employees]),
        ).all()
    }

    readonly = submission and submission.status in (
        models.DepartmentStatus.enviado, models.DepartmentStatus.aprobado
    )

    return templates.TemplateResponse("manager/novelties.html", {
        "request": request,
        "user": user,
        "dept": dept,
        "period": period,
        "employees": employees,
        "novelties": novelties,
        "submission": submission,
        "readonly": readonly,
    })


@router.post("/novelties/{dept_id}/{period_id}/save")
async def save_novelties(
    request: Request,
    dept_id: int,
    period_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    link = db.query(models.ManagerDepartment).filter(
        models.ManagerDepartment.user_id == user.id,
        models.ManagerDepartment.department_id == dept_id,
    ).first()
    if not link and user.role == models.UserRole.manager:
        raise HTTPException(403, "No tiene acceso a este departamento")

    submission = db.query(models.DepartmentSubmission).filter(
        models.DepartmentSubmission.department_id == dept_id,
        models.DepartmentSubmission.period_id == period_id,
    ).first()
    if submission and submission.status in (models.DepartmentStatus.aprobado,):
        raise HTTPException(400, "Este período ya fue aprobado y no puede modificarse")

    form_data = await request.form()
    employees = db.query(models.Employee).filter(
        models.Employee.department_id == dept_id,
        models.Employee.is_active == True,
    ).all()

    for emp in employees:
        prefix = f"emp_{emp.id}_"
        num_dias = form_data.get(f"{prefix}num_dias")
        h_diurnas = form_data.get(f"{prefix}horas_extras_diurnas")
        h_nocturnas = form_data.get(f"{prefix}horas_extras_nocturnas")
        h_dom_fest = form_data.get(f"{prefix}horas_extras_dom_fest")
        h_dom_fest_noct = form_data.get(f"{prefix}horas_extras_dom_fest_noct")
        obs = form_data.get(f"{prefix}observaciones", "")

        def to_float(val):
            if val is None or val == "":
                return None
            try:
                return float(val)
            except ValueError:
                return None

        novelty = db.query(models.Novelty).filter(
            models.Novelty.employee_id == emp.id,
            models.Novelty.period_id == period_id,
        ).first()

        if novelty is None:
            novelty = models.Novelty(employee_id=emp.id, period_id=period_id)
            db.add(novelty)

        novelty.num_dias = to_float(num_dias) if num_dias else 15.0
        novelty.horas_extras_diurnas = to_float(h_diurnas)
        novelty.horas_extras_nocturnas = to_float(h_nocturnas)
        novelty.horas_extras_dom_fest = to_float(h_dom_fest)
        novelty.horas_extras_dom_fest_noct = to_float(h_dom_fest_noct)
        novelty.observaciones = obs.strip() or None

    db.commit()

    if form_data.get("do_submit") == "1":
        submission = db.query(models.DepartmentSubmission).filter(
            models.DepartmentSubmission.department_id == dept_id,
            models.DepartmentSubmission.period_id == period_id,
        ).first()
        if submission is None:
            submission = models.DepartmentSubmission(
                department_id=dept_id, period_id=period_id
            )
            db.add(submission)
        if submission.status != models.DepartmentStatus.aprobado:
            submission.status = models.DepartmentStatus.enviado
            submission.submitted_at = datetime.utcnow()
            submission.submitted_by_id = user.id
            db.commit()
        return RedirectResponse(url="/manager/dashboard?submitted=1", status_code=302)

    return RedirectResponse(
        url=f"/manager/novelties/{dept_id}/{period_id}?saved=1", status_code=302
    )


@router.post("/novelties/{dept_id}/{period_id}/submit")
async def submit_novelties(
    dept_id: int,
    period_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    link = db.query(models.ManagerDepartment).filter(
        models.ManagerDepartment.user_id == user.id,
        models.ManagerDepartment.department_id == dept_id,
    ).first()
    if not link and user.role == models.UserRole.manager:
        raise HTTPException(403, "No tiene acceso a este departamento")

    submission = db.query(models.DepartmentSubmission).filter(
        models.DepartmentSubmission.department_id == dept_id,
        models.DepartmentSubmission.period_id == period_id,
    ).first()

    if submission is None:
        submission = models.DepartmentSubmission(
            department_id=dept_id, period_id=period_id
        )
        db.add(submission)

    if submission.status == models.DepartmentStatus.aprobado:
        raise HTTPException(400, "Este período ya fue aprobado")

    submission.status = models.DepartmentStatus.enviado
    submission.submitted_at = datetime.utcnow()
    submission.submitted_by_id = user.id
    db.commit()
    return RedirectResponse(url="/manager/dashboard?submitted=1", status_code=302)
