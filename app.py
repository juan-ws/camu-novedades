from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database import engine, Base
import models  # ensure all models are registered

from routers import auth_router, manager, hr, admin, export

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CAMU Novedades", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router.router)
app.include_router(manager.router)
app.include_router(hr.router)
app.include_router(admin.router)
app.include_router(export.router)


@app.get("/")
async def root():
    return RedirectResponse(url="/login")


@app.exception_handler(303)
async def redirect_handler(request: Request, exc):
    return RedirectResponse(url=exc.headers["Location"])
