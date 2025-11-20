from fastapi import FastAPI
from .django_setup import setup_django

setup_django()


from fastapi_app.routers import auth, users, message



# 1. Run the setup first!

# 2. Now you can import things that use the DB
# from .Routers import auth_router (example)

app = FastAPI()

app.include_router(message.router, prefix="/message", tags=["Messages"])
app.include_router(auth.router, tags=["Authentication"])

app.include_router(users.router, prefix="/users", tags=["Users"])
@app.get("/")
def read_root():
    return {"message": "Django and FastAPI are linked!"}