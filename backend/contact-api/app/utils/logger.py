import logging

from contextvars import ContextVar

tenant = ContextVar('tenant_id', default='system')


class LoggerFilter(logging.Filter):
    def filter(self, record):
        record.tenant_id = tenant.get()
        return True


logger = logging.getLogger("UnifiedLogger")
logger.setLevel(logging.INFO)
logger.propagate = False
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(tenant_id)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)
handler.addFilter(LoggerFilter())
logger.addHandler(handler)

for uvicorn_logger_name in ["uvicorn.error", "uvicorn.access"]:
    uvicorn_logger = logging.getLogger(uvicorn_logger_name)
    uvicorn_logger.handlers = []  # Clear out existing handlers
    uvicorn_logger.addHandler(handler)
    uvicorn_logger.setLevel(logging.INFO)
    uvicorn_logger.propagate = False
