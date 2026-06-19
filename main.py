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
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login", status_code=303)
    
    elif request.session.get("user_role") == "mentee":
        return templates.TemplateResponse(request, "questionnaire.html")
    
@app.get("/current_availability", response_class=JSONResponse)
async def get_current_availability(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"message": "Unauthorized"})

    try:
        availability = db.get_availability(user_id)
        return JSONResponse(status_code=200, content={"availability": availability})
    except Exception as e:
        print(f"[ERROR] fetching availability failed: {e}")
        return JSONResponse(status_code=500, content={"message": "Internal server error"})

@app.delete("/api/delete_availability")
async def delete_availability(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"message": "Unauthorized"})
    try:
        body = await request.json()
        success, message = db.remove_availability(
            user_id,
            body.get("day_of_the_week"),
            body.get("start_time"),
            body.get("end_time"),
            body.get("timezone")
        )
        status = 200 if success else 500
        return JSONResponse(status_code=status, content={"message": message})
    except Exception as e:
        print(f"[ERROR] removing availability failed: {e}")
        return JSONResponse(status_code=500, content={"message": "Internal server error"})
          
@app.post("/api/availability")
async def save_availability(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"message": "Unauthorized"})

    try:
        body = await request.json()
        slots = body.get("slots", [])

        existing = db.get_availability(user_id)
        existing_keys = {
            (a["day_of_the_week"], a["start_time"], a["end_time"], a["timezone"])
            for a in existing
        }

        for slot in slots:
            key = (
                slot.get("day_of_the_week"),
                slot.get("start_time"),
                slot.get("end_time"),
                slot.get("timezone")
            )

            if key in existing_keys:
                print(f"Slot already exists: {key}")
                continue

            success, message = db.change_availability(
                user_id,
                slot.get("day_of_the_week"),
                slot.get("start_time"),
                slot.get("end_time"),
                slot.get("timezone")
            )
            if not success:
                return JSONResponse(status_code=500, content={"message": message})

        return JSONResponse(status_code=200, content={"message": "Availability saved successfully"})
    except Exception as e:
        print(f"[ERROR] availability save failed: {e}")
        return JSONResponse(status_code=500, content={"message": "Internal server error"})
    
@app.post("/api/questionnaire")
async def submit_questionnaire(request: Request):
    if request.session.get("user_role") == "mentee":
        body = await request.json()           
        user_id = request.session.get("user_id")
        db.questionnaire_submission(
    user_id,
    body.get("papers_read_plan"),
    body.get("lit_review_confidence"),
    body.get("meeting_frequency"),
    body.get("communication_abilities"),
    body.get("research_tool_skill"),
    body.get("deadline_management"),
    body.get("domain_knowledge")
)
    return JSONResponse(status_code=200, content={"message": "Questionnaire submitted successfully"})

@app.get("/profile", response_class=HTMLResponse)
def profile(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    
    user_data = db.get_user_by_id(user_id)
    return templates.TemplateResponse(request, "profile.html", {"user": user_data})

@app.post("/api/profile")
async def update_profile(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"message": "Unauthorized"})
    
    body = await request.json()
    if request.session.get("user_role") == "mentor":
        db.fill_mentor_profile(
        user_id,
        body.get("expertise"),
        body.get("experience"),
        body.get("max_groups"),
        body.get("university")
    )

    elif request.session.get("user_role") == "curator":
        db.fill_curator_profile(
            user_id,
            body.get("department"),
            body.get("university")
        )
    elif request.session.get("user_role") == "mentee":
        db.fill_mentee_profile(user_id, body.get("skills"), body.get("domain_of_knowledge"), body.get("favourable_program_type"), body.get("experience_level"), body.get("research_goals"), body.get("short_term_goals"), body.get("long_term_goals"), body.get("mentor_expectations"), body.get("university"))

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


@app.get("/matching_formation")
def matching_formation(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"message": "Unauthorized"})
    
    user_data = db.get_user_by_id(user_id)
    role = user_data.get("role")

    if role == "curator":
        return templates.TemplateResponse(request, "group_formation.html")
    elif role == "mentee" or role == "mentee":
        return RedirectResponse(url=f"/profile", status_code=303)
    
@app.post("/api/matching_formation")
async def api_group_formation(
    request: Request,
    mentor: int = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    program_type: str = Form(...),
    max_size: int = Form(...),
    experience_level: str = Form(...)
):
    user_id = request.session.get("user_id")

    if not user_id:
        return JSONResponse(
            status_code=401,
            content={"message": "Unauthorized"}
        )
    curator_data = db.get_current_curator(user_id)
    success, message = db.create_group(
        curator_id=curator_data,
        mentor_id=mentor,
        name=name,
        description=description,
        program_type=program_type,
        max_size=max_size,
        experience_level=experience_level
    )

    return JSONResponse(
        status_code=200 if success else 500,
        content={"message": message}
    )

@app.post("/api/assign_mentor")
async def api_assign_mentor(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"message": "Unauthorized"})
    
    body = await request.json()
    db.assign_mentor_to_group(body.get("group_id"), body.get("mentor_id"))
    return JSONResponse(status_code=200, content={"message": "Mentor assigned successfully"})

@app.get("/api/mentors")
async def api_get_mentors(request: Request):
    mentors = db.get_mentors()
    return JSONResponse(status_code=200, content={"mentors": mentors})

@app.get("/current_groups", response_class=HTMLResponse)
def current_groups(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    user_data = db.get_user_by_id(user_id)
    return templates.TemplateResponse(request, "current_groups.html", {"user": user_data})

@app.get("/api/current_groups")
async def get_current_groups(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"message": "Unauthorized"})
    curator_data = db.get_current_curator(user_id)

    groups = db.get_current_groups(curator_data)
    return JSONResponse(status_code=200, content={"groups": groups})

@app.delete("/api/remove_group")
async def remove_group(request: Request):
    try:
        user_id = request.session.get("user_id")
        if not user_id:
            return JSONResponse(status_code=401, content={"message": "Unauthorized"})

        body = await request.json()
        group_id = body.get("group_id")

        if not group_id:
            return JSONResponse(status_code=400, content={"message": "group_id missing"})

        group_id = int(group_id)  

        success, msg = db.delete_group(group_id)
        if not success:
            return JSONResponse(status_code=500, content={"message": msg})

        return JSONResponse(status_code=200, content={"message": "Group removed successfully"})

    except (ValueError, TypeError):
        return JSONResponse(status_code=400, content={"message": "Invalid group_id"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})
    
@app.post("/api/change_group")
async def change_group(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=401, content={"message": "Unauthorized"})

    body = await request.json()
    group_id = body.get("group_id")
    if not group_id:
        return JSONResponse(status_code=400, content={"message": "group_id missing"})

    group_id = int(group_id) 

    success, msg = db.change_group(
        group_id=group_id,
        name=body.get("name"),
        description=body.get("description"),
        program_type=body.get("program_type"),
        max_size=body.get("max_size"),
        experience_level=body.get("experience_level")
    )

    if not success:
        return JSONResponse(status_code=500, content={"message": msg})
    return {"message": "Group updated successfully"}