from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, links

app = FastAPI(
    title="URL Shortener",
    description="Service for shortening URLs with analytics",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(links.router)

@app.get("/")
async def root():
    return {"message": "Welcome to URL Shortener API"} 