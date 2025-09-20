import time
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, Request, responses
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers.routes import api
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logger import logger, user_id

app = FastAPI(default_response_class=responses.ORJSONResponse)


class ProcessTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = f"UID-{uuid4()}"
        logger.info(f"rid={rid} start request path={request.url.path}")
        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time
        formatted_process_time = f"{process_time:.2f}"
        logger.info(f"rid={rid} completed_in={formatted_process_time}ms status_code={response.status_code}")
        response.headers["X-Process-Time"] = str(process_time)
        return response


class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            logger.exception("Unhandled exception")
            return JSONResponse(content={"detail": "Internal server error"}, status_code=500)


class ContextualLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract user_id from Authorization header for logging
        auth_header = request.headers.get('Authorization', '')
        user_id_value = auth_header.replace("Bearer ", "").strip() if auth_header else 'anonymous'
        user_token = user_id.set(user_id_value)
        try:
            return await call_next(request)
        finally:
            user_id.reset(user_token)


app.add_middleware(ContextualLoggingMiddleware)
app.add_middleware(ExceptionHandlingMiddleware)
app.add_middleware(ProcessTimeMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api, prefix="")

if __name__ == "__main__":
    uvicorn.run(app, port=8081, log_level="info", reload=True)  # pragma: no cover
