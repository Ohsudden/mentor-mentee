from fastapi import FastAPI, Request, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from pwdlib import PasswordHash
import os, time, secrets, ast, json, re
from typing import List, Optional
import requests
from dotenv import load_dotenv
from phoenix.client import Client
from database import Database

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    confirm_password: str
    role: str
    gender: Optional[str] = None
    age: Optional[int] = None
    education_level: Optional[str] = None

db = Database()
app = FastAPI()

db.init_db()
app.add_middleware(SessionMiddleware, secret_key='dev_secret')

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="static")

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.get("/registration", response_class=HTMLResponse)
async def registration(request: Request):
    user_id = request.session.get("user_id")
    if user_id:
        return RedirectResponse(url=f"/settings/{user_id}", status_code=302)
    return templates.TemplateResponse(request, "registration.html")


@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    user_data = db.get_user_by_id(user_id)
    print(user_data)
    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "user": user_data
        }
    )
@app.get("/settings/{userid}", response_class=HTMLResponse)
async def settings(request: Request, userid: int):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    if user_id != userid:
        return RedirectResponse(url=f"/settings/{user_id}", status_code=302)
    user = db.get_user_by_id(userid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    print(user)
    return templates.TemplateResponse(request, "settings.html", {"userid": userid, "user": user})


@app.get("/questionnaire", response_class=HTMLResponse)
def read_questionnaire(request: Request):
    return templates.TemplateResponse(request, "questionnaire.html")

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    user_id = request.session.get("user_id")
    if user_id:
        return RedirectResponse(url=f"/settings/{user_id}", status_code=302)
    return templates.TemplateResponse(request, "login.html")

@app.post("/api/register/")
async def register_user(request: RegisterRequest):
    success, message = db.create_user(request.name, request.email, request.password, request.confirm_password, request.role, request.gender, request.age, request.education_level)
    
    if success:
        return JSONResponse(status_code=200, content={"success": True, "message": message})
    else:
        return JSONResponse(status_code=400, content={"success": False, "message": message})


@app.post("/api/login")
def api_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    success, user_data = db.login_user(email, password)

    if not success:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": user_data}
        )

    request.session["user_email"] = user_data["email"]
    request.session["user_id"] = user_data["id"]
    request.session["user_role"] = user_data.get("role")

    return RedirectResponse(url=f"/settings/{user_data['id']}", status_code=303)

def session_info(request: Request):
    return {
        "user_id": request.session.get("user_id"),
        "user_email": request.session.get("user_email"),
        "user_role": request.session.get("user_role"),
    }
