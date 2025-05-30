# app/main.py
from fastapi import FastAPI
from .routes import user
from .routes import file_upload,file_download,file_validation,superadmin_routes
# Add this temporarily to main.py
from .database import Base, engine
from . import models

#now we will setup cors
from fastapi.middleware.cors import CORSMiddleware


# CORS setup
origins = [
    "http://localhost:5173",  # React app

]

models.Base.metadata.create_all(bind=engine)


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(user.router)
app.include_router(file_upload.router)
app.include_router(file_download.router)
app.include_router(file_validation.router)
app.include_router(superadmin_routes.router)



@app.get("/")
def root():
    return {"message": "Secure File Storage API"}
