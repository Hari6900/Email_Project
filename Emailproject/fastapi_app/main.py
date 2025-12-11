from fastapi import FastAPI
from .django_setup import setup_django
setup_django()
from fastapi_app.routers import auth, users, email, chat, analytics, notes

from fastapi_app.routers import task  
from fastapi_app.routers import profile


app = FastAPI()
app.include_router(email.router, prefix="/email", tags=["Emails"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(task.router)                                                
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(profile.router)
app.include_router(notes.router)


@app.get("/")
def read_root():
    return {"message": "Django and FastAPI are linked!"}