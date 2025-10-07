from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="Test Deploy API", version="1.0.0")

@app.get("/health-check")
async def health_check():
    """Simple health check endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "test-deploy-api",
            "version": "1.0.0"
        },
        status_code=200
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")