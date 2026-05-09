from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from datetime import date

from database import get_db
from auth import require_hr
from export_utils.excel import generate_excel
import models

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/excel/{period_id}")
async def export_excel(
    period_id: int,
    user: models.User = Depends(require_hr),
    db: Session = Depends(get_db),
):
    period = db.query(models.PayPeriod).filter(models.PayPeriod.id == period_id).first()
    if not period:
        raise HTTPException(404, "Período no encontrado")

    xlsx_bytes = generate_excel(period, db)
    filename = f"Novedades_{period.month_name}_{period.year}_Q{period.period_number}.xlsx"
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/pdf/{period_id}")
async def export_pdf(
    period_id: int,
    user: models.User = Depends(require_hr),
    db: Session = Depends(get_db),
):
    """
    Returns an HTML page formatted for printing as PDF.
    The user can use their browser's Print → Save as PDF.
    """
    period = db.query(models.PayPeriod).filter(models.PayPeriod.id == period_id).first()
    if not period:
        raise HTTPException(404)

    companies = db.query(models.Company).filter(models.Company.is_active == True).all()
    sections = []
    for company in companies:
        departments = db.query(models.Department).filter(
            models.Department.company_id == company.id,
            models.Department.is_active == True,
        ).all()
        all_employees = db.query(models.Employee).filter(
            models.Employee.company_id == company.id,
            models.Employee.is_active == True,
        ).all()
        if not all_employees:
            continue
        novelty_map = {
            n.employee_id: n
            for n in db.query(models.Novelty).filter(
                models.Novelty.period_id == period.id,
                models.Novelty.employee_id.in_([e.id for e in all_employees]),
            ).all()
        }
        dept_data = []
        for dept in departments:
            emps = sorted(
                [e for e in all_employees if e.department_id == dept.id],
                key=lambda e: e.full_name,
            )
            if emps:
                dept_data.append({"dept": dept, "employees": emps})
        sections.append({
            "company": company,
            "dept_data": dept_data,
            "novelty_map": novelty_map,
            "total": len(all_employees),
        })

    html = _render_pdf_html(period, sections)
    return Response(content=html, media_type="text/html; charset=utf-8")


def _render_pdf_html(period: models.PayPeriod, sections: list) -> str:
    today = date.today().strftime("%d/%m/%Y")
    rows_html = ""
    for sec in sections:
        company = sec["company"]
        seq = 1
        company_rows = ""
        for item in sec["dept_data"]:
            dept = item["dept"]
            company_rows += f"""
            <tr class="dept-header">
                <td colspan="14">{dept.name}</td>
            </tr>"""
            for emp in item["employees"]:
                novelty = sec["novelty_map"].get(emp.id)
                nd = f"{novelty.num_dias:.2f}" if novelty else "15.00"
                hed = _fmt(novelty.horas_extras_diurnas if novelty else None)
                hen = _fmt(novelty.horas_extras_nocturnas if novelty else None)
                hedf = _fmt(novelty.horas_extras_dom_fest if novelty else None)
                hedfn = _fmt(novelty.horas_extras_dom_fest_noct if novelty else None)
                obs = (novelty.observaciones or "") if novelty else ""
                status_label = "Aprobado" if novelty and novelty.status == models.NoveltyStatus.aprobado else "Pendiente"
                company_rows += f"""
            <tr>
                <td class="center">{seq}</td>
                <td>{company.full_name}</td>
                <td class="center">{emp.internal_code or ''}</td>
                <td class="center">{status_label}</td>
                <td class="center">{emp.project_code or ''}</td>
                <td>{emp.full_name}</td>
                <td class="center">{emp.cedula}</td>
                <td class="center">{period.month_name}</td>
                <td class="center">{period.period_label}</td>
                <td class="center">{nd}</td>
                <td class="center">{hed}</td>
                <td class="center">{hen}</td>
                <td class="center">{hedf}</td>
                <td class="center">{hedfn}</td>
                <td>{obs}</td>
            </tr>"""
                seq += 1

        rows_html += f"""
        <div class="company-section page-break">
            <h2>{company.full_name}</h2>
            <p class="meta">Nit. {company.nit or ''} | Fecha: {today} | {period.period_label} {period.month_name} {period.year}</p>
            <table>
                <thead>
                    <tr>
                        <th>#</th><th>Sociedad</th><th>ID</th><th>Estado</th>
                        <th>Proyecto</th><th>Empleado</th><th>Cédula</th>
                        <th>Mes</th><th>Período</th><th>Días</th>
                        <th>H.E. Diurnas</th><th>H.E. Nocturnas</th>
                        <th>H.E. Dom/Fest</th><th>H.E. Dom/Fest/Noct</th>
                        <th>Observaciones</th>
                    </tr>
                </thead>
                <tbody>
                    {company_rows}
                </tbody>
                <tfoot>
                    <tr class="footer-row">
                        <td colspan="14">TOTAL EMPLEADOS {company.full_name.upper()}: {sec['total']}</td>
                    </tr>
                </tfoot>
            </table>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Novedades {period.period_label} {period.month_name} {period.year}</title>
<style>
  body {{ font-family: Arial, sans-serif; font-size: 8pt; margin: 0; }}
  h2 {{ font-size: 11pt; margin: 0 0 4px 0; color: #1F3864; }}
  .meta {{ font-size: 8pt; color: #555; margin-bottom: 6px; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; }}
  th {{ background: #1F3864; color: #fff; padding: 4px 3px; text-align: center; font-size: 7pt; }}
  td {{ border: 1px solid #ccc; padding: 3px; vertical-align: top; }}
  .center {{ text-align: center; }}
  .dept-header td {{ background: #D9E1F2; font-weight: bold; font-size: 9pt; padding: 4px; }}
  .footer-row td {{ background: #1F3864; color: #fff; font-weight: bold; }}
  .company-section {{ margin-bottom: 20px; }}
  .page-break {{ page-break-after: always; }}
  @media print {{
    .page-break {{ page-break-after: always; }}
    @page {{ margin: 1cm; size: A4 landscape; }}
  }}
</style>
</head>
<body>
  <div style="text-align:right; margin-bottom:10px;">
    <button onclick="window.print()" style="padding:6px 16px;background:#1F3864;color:#fff;border:none;cursor:pointer;font-size:10pt;">
      🖨️ Imprimir / Guardar PDF
    </button>
  </div>
  {rows_html}
</body>
</html>"""


def _fmt(val) -> str:
    if val is None:
        return ""
    return f"{val:.2f}"
