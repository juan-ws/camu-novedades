from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import datetime

from database import get_db
from auth import require_hr
import models

router = APIRouter(prefix="/hr", tags=["hr"])
templates = Jinja2Templates(directory="templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def hr_dashboard(
    request: Request,
    user: models.User = Depends(require_hr),
    db: Session = Depends(get_db),
):
    periods = db.query(models.PayPeriod).filter(
        models.PayPeriod.is_active == True
    ).order_by(
        models.PayPeriod.year.desc(),
        models.PayPeriod.month.desc(),
        models.PayPeriod.period_number.desc(),
    ).all()

    companies = db.query(models.Company).filter(models.Company.is_active == True).all()
    active_period = periods[0] if periods else None

    period_stats = []
    for period in periods:
        total_depts = db.query(func.count(models.Department.id)).filter(
            models.Department.is_active == True
        ).scalar()
        submitted = db.query(func.count(models.DepartmentSubmission.id)).filter(
            models.DepartmentSubmission.period_id == period.id,
            models.DepartmentSubmission.status.in_([
                models.DepartmentStatus.enviado, models.DepartmentStatus.aprobado
            ]),
        ).scalar()
        approved = db.query(func.count(models.DepartmentSubmission.id)).filter(
            models.DepartmentSubmission.period_id == period.id,
            models.DepartmentSubmission.status == models.DepartmentStatus.aprobado,
        ).scalar()
        total_employees = db.query(func.count(models.Employee.id)).filter(
            models.Employee.is_active == True
        ).scalar()
        period_stats.append({
            "period": period,
            "total_depts": total_depts,
            "submitted": submitted,
            "approved": approved,
            "pending": total_depts - submitted,
            "total_employees": total_employees,
        })

    return templates.TemplateResponse("hr/dashboard.html", {
        "request": request,
        "user": user,
        "period_stats": period_stats,
        "companies": companies,
    })


@router.get("/review/{period_id}", response_class=HTMLResponse)
async def hr_review(
    request: Request,
    period_id: int,
    company_id: int = None,
    user: models.User = Depends(require_hr),
    db: Session = Depends(get_db),
):
    period = db.query(models.PayPeriod).filter(models.PayPeriod.id == period_id).first()
    if not period:
        raise HTTPException(404, "Período no encontrado")

    companies = db.query(models.Company).filter(models.Company.is_active == True).all()

    dept_query = db.query(models.Department).filter(models.Department.is_active == True)
    if company_id:
        dept_query = dept_query.filter(models.Department.company_id == company_id)
    departments = dept_query.all()

    dept_data = []
    for dept in departments:
        submission = db.query(models.DepartmentSubmission).filter(
            models.DepartmentSubmission.department_id == dept.id,
            models.DepartmentSubmission.period_id == period_id,
        ).first()
        employees = db.query(models.Employee).filter(
            models.Employee.department_id == dept.id,
            models.Employee.is_active == True,
        ).order_by(models.Employee.full_name).all()
        novelties = {
            n.employee_id: n
            for n in db.query(models.Novelty).filter(
                models.Novelty.period_id == period_id,
                models.Novelty.employee_id.in_([e.id for e in employees]),
            ).all()
        }
        dept_data.append({
            "department": dept,
            "submission": submission,
            "employees": employees,
            "novelties": novelties,
        })

    return templates.TemplateResponse("hr/review.html", {
        "request": request,
        "user": user,
        "period": period,
        "dept_data": dept_data,
        "companies": companies,
        "selected_company_id": company_id,
    })


@router.post("/approve/department/{dept_id}/{period_id}")
async def approve_department(
    dept_id: int,
    period_id: int,
    user: models.User = Depends(require_hr),
    db: Session = Depends(get_db),
):
    submission = db.query(models.DepartmentSubmission).filter(
        models.DepartmentSubmission.department_id == dept_id,
        models.DepartmentSubmission.period_id == period_id,
    ).first()
    if not submission:
        submission = models.DepartmentSubmission(
            department_id=dept_id, period_id=period_id
        )
        db.add(submission)

    now = datetime.utcnow()
    employees = db.query(models.Employee).filter(
        models.Employee.department_id == dept_id,
        models.Employee.is_active == True,
    ).all()
    for emp in employees:
        novelty = db.query(models.Novelty).filter(
            models.Novelty.employee_id == emp.id,
            models.Novelty.period_id == period_id,
        ).first()
        if novelty:
            novelty.status = models.NoveltyStatus.aprobado
            novelty.approved_at = now
            novelty.approved_by_id = user.id
            approval_note = f"[{user.full_name} {now.strftime('%d-%m-%Y %I:%M %p')}] Aprobado"
            novelty.observaciones_aprobacion = approval_note

    submission.status = models.DepartmentStatus.aprobado
    submission.approved_at = now
    submission.approved_by_id = user.id
    db.commit()
    return RedirectResponse(url=f"/hr/review/{period_id}?approved=1", status_code=302)


@router.post("/approve/novelty/{novelty_id}")
async def approve_novelty(
    novelty_id: int,
    user: models.User = Depends(require_hr),
    db: Session = Depends(get_db),
):
    novelty = db.query(models.Novelty).filter(models.Novelty.id == novelty_id).first()
    if not novelty:
        raise HTTPException(404)
    now = datetime.utcnow()
    novelty.status = models.NoveltyStatus.aprobado
    novelty.approved_at = now
    novelty.approved_by_id = user.id
    novelty.observaciones_aprobacion = (
        f"[{user.full_name} {now.strftime('%d-%m-%Y %I:%M %p')}] Aprobado"
    )
    db.commit()
    return RedirectResponse(
        url=f"/hr/review/{novelty.period_id}?approved=1", status_code=302
    )


@router.post("/reject/department/{dept_id}/{period_id}")
async def reject_department(
    request: Request,
    dept_id: int,
    period_id: int,
    user: models.User = Depends(require_hr),
    db: Session = Depends(get_db),
):
    submission = db.query(models.DepartmentSubmission).filter(
        models.DepartmentSubmission.department_id == dept_id,
        models.DepartmentSubmission.period_id == period_id,
    ).first()
    if submission:
        submission.status = models.DepartmentStatus.pendiente
        db.commit()
    return RedirectResponse(url=f"/hr/review/{period_id}", status_code=302)
