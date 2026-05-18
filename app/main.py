import json
import logging
from datetime import datetime, timezone
from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings




class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        event = getattr(record, "event", None)
        if event is not None:
            payload["event"] = event

        skip = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "message",
        }
        for key, value in record.__dict__.items():
            if key in skip or key in payload:
                continue
            payload[key] = value

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(level: str) -> None:
    level_name = (level or "INFO").upper()
    if level_name not in logging._nameToLevel:
        level_name = "INFO"

    root = logging.getLogger()
    root.setLevel(level_name)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root.handlers = [handler]


configure_logging(settings.log_level)

app = FastAPI(title=settings.app_name)
app.include_router(api_router)



@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
