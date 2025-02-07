from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.routers import dns_router
from config import Config
import uvicorn

app = FastAPI(
    title="LTM Web Tool API",
    description="API for F5 BIG-IP Local Traffic Manager Web Tool",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(dns_router)

@app.get("/")
async def root():
    return {"message": "LTM Web Tool API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host=Config.HOST, 
        port=Config.PORT,
        reload=Config.DEBUG
    ) 