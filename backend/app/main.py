import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.services.query_executor import DatasetFilesMissing

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("querypilot")
settings = get_settings()

app = FastAPI(title="QueryPilot AI")
app.add_middleware(
    CORSMiddleware, allow_origins=[settings.frontend_origin], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)
app.include_router(api)


def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


@app.exception_handler(AppError)
async def app_error(_: Request, e: AppError):
    return _err(e.status, e.code, e.message)


@app.exception_handler(DatasetFilesMissing)
async def files_missing(_: Request, e: DatasetFilesMissing):
    log.error("dataset file missing: %s", e)
    return _err(410, "dataset_files_missing",
                "This dataset's data is no longer available on the server. Delete it and upload the file again.")


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, e: RequestValidationError):
    first = e.errors()[0] if e.errors() else {}
    loc = ".".join(str(p) for p in first.get("loc", []) if p != "body")
    return _err(422, "validation_error", f"{loc}: {first.get('msg', 'invalid input')}")


@app.exception_handler(Exception)
async def unhandled(_: Request, e: Exception):
    log.exception("unhandled error")
    return _err(500, "internal_error", "Something went wrong.")


@app.middleware("http")
async def request_log(request: Request, call_next):
    rid, start = uuid4().hex[:12], time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    log.info("req=%s %s %s -> %s %dms", rid, request.method, request.url.path,
             response.status_code, (time.perf_counter() - start) * 1000)
    return response
