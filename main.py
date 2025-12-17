from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router
import logging
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

logger = logging.getLogger("tracking-service")
logger.info("Starting User Tracking Service...")

app = FastAPI(
    title="User Tracking Service",
    description="""
## EduConnect Tracking Service

Simple service to track user's current lesson for AI Chatbot context.

### Features
- 📍 Track current lesson user is studying
- 🤖 Enable chatbot to answer questions about current lesson
- 🚀 Fast O(1) lookup with unique index
- ✅ Simple: Just 3 endpoints (enter, exit, current)

### Use Cases
1. **User enters lesson** → Call `/lesson/enter` → Set current lesson
2. **Chatbot needs context** → Call `/user/{id}/current` → Get current lesson
3. **User exits lesson** → Call `/lesson/exit` → Clear tracking

### Integration
- Frontend: Call enter/exit on lesson page mount/unmount
- Chatbot: Call current to check if user is in a lesson
- Backend: Provide lesson details via `/api/v1/lessons/{id}`
    """,
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # Alternative docs
)

# CORS middleware - configure from environment
cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router
app.include_router(router)


# Top-level health check endpoint for Docker health check
@app.get("/health")
async def health():
    """Health check endpoint for Docker"""
    return {
        "status": "healthy",
        "service": "tracking-service",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

# uvicorn main:app --reload --host 0.0.0.0 --port 8002 --log-level info
