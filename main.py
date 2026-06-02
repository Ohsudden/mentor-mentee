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

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key='dev_secret')

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="static")

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.get("/registration", response_class=HTMLResponse)
def read_register(request: Request):
    return templates.TemplateResponse(request, "registration.html")

@app.get("/settings", response_class=HTMLResponse)
def read_settings(request: Request):
    return templates.TemplateResponse(request, "settings.html")

@app.get("/questionnaire", response_class=HTMLResponse)
def read_questionnaire(request: Request):
    return templates.TemplateResponse(request, "questionnaire.html")