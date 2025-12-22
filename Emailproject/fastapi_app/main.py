from fastapi import FastAPI
from .django_setup import setup_django
setup_django()
from fastapi_app.routers import auth, users, email, chat, analytics,  meet, calendar, notes
from fastapi_app.routers import auth, users, email, chat, analytics, meet, notifications

from fastapi.staticfiles import StaticFiles
from pathlib import Path
# from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # React (Vite)
        "http://127.0.0.1:5173",
    ],
    # allow_origins=["*"],  # TEMP for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from fastapi_app.routers import task  
from fastapi_app.routers import profile

# app = FastAPI()
app.include_router(email.router, prefix="/email", tags=["Emails"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(task.router)                                                
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(profile.router)
app.include_router(meet.router, prefix="/meet", tags=["Meetings"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
app.include_router(notes.router)
app.include_router(calendar.router)


@app.get("/")
def read_root():
    return {"message": "Django and FastAPI are linked!"}