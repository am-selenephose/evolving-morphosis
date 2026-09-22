"""Production ASGI surface for Morphosis Evolution OS."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
import time
from pathlib import Path
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from threading import Lock
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
import uvicorn

from .application import MorphosisApplication
from .config import ServiceSettings
from .logging import configure_logging
from .transports import HostTransportExecutor, load_transport_bindings
from .schemas import WorkloadContract
from .deployment import TrafficPolicy

LOGGER = logging.getLogger("morphosis.service")
_REQUEST_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class CommandEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=100)
    payload: dict
    command_id: str | None = Field(default=None, min_length=1, max_length=200)


@dataclass
class ServiceMetrics:
    _lock: Lock = field(default_factory=Lock)
    requests: int = 0
    errors: int = 0
    command_requests: int = 0
    total_duration_ms: float = 0.0

    def observe(self, *, status: int, duration_ms: float, command: bool = False) -> None:
        with self._lock:
            self.requests += 1
            self.total_duration_ms += duration_ms
            if status >= 400:
                self.errors += 1
            if command:
                self.command_requests += 1

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "requests": self.requests,
                "errors": self.errors,
                "command_requests": self.command_requests,
                "total_duration_ms": self.total_duration_ms,
            }


def _request_id(request: Request) -> str:
    supplied = request.headers.get("x-request-id", "")
    return supplied if _REQUEST_ID.fullmatch(supplied) else str(uuid4())


def _error(code: str, message: str, request_id: str, status: int) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "request_id": request_id}},
    )


def _projection(snapshot: dict, key: str):
    routes = {
        "system": snapshot,
        "models": snapshot["models"],
        "capabilities": snapshot["capabilities"],
        "evidence": snapshot["evidence"],
        "evolution/bundles": snapshot["bundles"],
        "evolution/ledger": snapshot["events"],
        "deployments": snapshot["deployment"],
    }
    if key not in routes:
        raise KeyError(key)
    return routes[key]


def create_app(
    settings: ServiceSettings | None = None,
    application: MorphosisApplication | None = None,
) -> FastAPI:
    settings = (settings or ServiceSettings.from_env()).validate()
    owned_application = application is None
    if application is None:
        bindings = (
            load_transport_bindings(settings.transport_config)
            if settings.transport_config
            else {}
        )
        executor = HostTransportExecutor() if bindings else None
        discoverers = {}
        if settings.bedrock_discovery:
            from .discovery import BedrockDiscoverer
            discoverers["bedrock"] = BedrockDiscoverer(region_name=settings.aws_region)
        contract = None
        if settings.contract_file:
            contract_payload = json.loads(
                Path(settings.contract_file).expanduser().read_text()
            )
            contract = WorkloadContract.model_validate(contract_payload)
        traffic_policy = TrafficPolicy(
            enabled=settings.live_traffic,
            production=settings.live_traffic_production,
            canary_fraction=settings.canary_fraction,
            ramp_fraction=settings.ramp_fraction,
            min_shadow_samples=settings.min_shadow_samples,
            min_canary_samples=settings.min_canary_samples,
            min_ramp_samples=settings.min_ramp_samples,
            max_mismatch_rate=settings.max_traffic_mismatch_rate,
        )
        app_state = MorphosisApplication(
            settings.db_path,
            contract=contract,
            transports=bindings,
            executor=executor,
            discoverers=discoverers,
            traffic_policy=traffic_policy,
        )
    else:
        app_state = application
    metrics = ServiceMetrics()

    if settings.seed_reference and not app_state.snapshot()["models"]:
        from morphosis.export_demo import seed
        seed(app_state)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        LOGGER.info("service_started")
        try:
            yield
        finally:
            if owned_application:
                app_state.close()
            LOGGER.info("service_stopped")

    docs_url = "/docs" if settings.expose_docs else None
    openapi_url = "/openapi.json" if settings.expose_docs else None
    app = FastAPI(
        title="Morphosis Evolution OS",
        version="0.3.0",
        docs_url=docs_url,
        redoc_url=None,
        openapi_url=openapi_url,
        lifespan=lifespan,
    )
    app.state.morphosis = app_state
    app.state.settings = settings
    app.state.metrics = metrics

    if settings.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.allowed_origins),
            allow_credentials=False,
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type", "Last-Event-ID", "X-Request-ID"],
        )

    @app.middleware("http")
    async def operational_boundary(request: Request, call_next):
        started = time.perf_counter()
        rid = _request_id(request)
        request.state.request_id = rid
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > settings.request_max_bytes:
                    response = _error(
                        "REQUEST_TOO_LARGE",
                        "request body exceeds configured limit",
                        rid,
                        413,
                    )
                    response.headers["X-Request-ID"] = rid
                    return response
            except ValueError:
                response = _error(
                    "INVALID_CONTENT_LENGTH",
                    "invalid content-length header",
                    rid,
                    400,
                )
                response.headers["X-Request-ID"] = rid
                return response
        try:
            response = await call_next(request)
        except Exception:
            LOGGER.exception(
                "unhandled_request_error",
                extra={"request_id": rid, "method": request.method, "path": request.url.path},
            )
            response = _error("INTERNAL_ERROR", "unexpected service error", rid, 500)
        duration = (time.perf_counter() - started) * 1000
        metrics.observe(
            status=response.status_code,
            duration_ms=duration,
            command=request.url.path == "/api/v1/commands",
        )
        response.headers["X-Request-ID"] = rid
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        LOGGER.info(
            "request_complete",
            extra={
                "request_id": rid,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round(duration, 3),
            },
        )
        return response

    @app.get("/healthz", include_in_schema=False)
    async def healthz():
        return {"status": "ok", "service": "morphosis", "version": "0.3.0"}

    @app.get("/readyz", include_in_schema=False)
    async def readyz(request: Request):
        health = await asyncio.to_thread(app_state.ledger.health)
        if not health["ready"]:
            return _error(
                "NOT_READY",
                health.get("error", "ledger readiness check failed"),
                request.state.request_id,
                503,
            )
        return {"status": "ready", "ledger": health}

    @app.get("/metrics", response_class=PlainTextResponse, include_in_schema=False)
    async def prometheus_metrics():
        process = metrics.snapshot()
        ledger = await asyncio.to_thread(app_state.ledger.health)
        values = {
            "morphosis_http_requests_total": process["requests"],
            "morphosis_http_errors_total": process["errors"],
            "morphosis_command_requests_total": process["command_requests"],
            "morphosis_http_request_duration_milliseconds_total": round(
                process["total_duration_ms"], 3
            ),
            "morphosis_ledger_events": ledger.get("events", 0),
            "morphosis_ledger_artifacts": ledger.get("artifacts", 0),
            "morphosis_ledger_commands": ledger.get("commands", 0),
        }
        return "\n".join(f"{key} {value}" for key, value in values.items()) + "\n"

    @app.post("/api/v1/commands")
    async def commands(envelope: CommandEnvelope, request: Request):
        if len(envelope.model_dump_json().encode()) > settings.request_max_bytes:
            return _error(
                "REQUEST_TOO_LARGE",
                "command envelope exceeds configured limit",
                request.state.request_id,
                413,
            )
        try:
            return await asyncio.to_thread(
                app_state.command,
                envelope.name,
                envelope.payload,
                envelope.command_id,
            )
        except (ValueError, KeyError, TypeError) as exc:
            return _error("COMMAND_REJECTED", str(exc), request.state.request_id, 400)

    @app.get("/api/v1/events")
    async def events(request: Request, after: int = 0):
        cursor = request.headers.get("last-event-id")
        if cursor:
            try:
                after = max(after, int(cursor))
            except ValueError:
                return _error(
                    "INVALID_EVENT_CURSOR",
                    "last-event-id must be an integer",
                    request.state.request_id,
                    400,
                )
        if after < 0:
            return _error(
                "INVALID_EVENT_CURSOR",
                "event cursor must be non-negative",
                request.state.request_id,
                400,
            )

        async def stream():
            current = after
            while True:
                if await request.is_disconnected():
                    return
                records = await asyncio.to_thread(app_state.events, current)
                if records:
                    for event in records:
                        yield (
                            f"id: {event['sequence']}\n"
                            "event: domain\n"
                            f"data: {json.dumps(event, separators=(',', ':'))}\n\n"
                        )
                    current = records[-1]["sequence"]
                else:
                    yield ": heartbeat\n\n"
                await asyncio.sleep(settings.sse_heartbeat_seconds)

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
        )

    @app.get("/api/v1/{projection:path}")
    async def projections(projection: str, request: Request):
        try:
            snapshot = await asyncio.to_thread(app_state.snapshot)
            return _projection(snapshot, projection)
        except KeyError:
            return _error(
                "PROJECTION_NOT_FOUND",
                "unknown projection",
                request.state.request_id,
                404,
            )
        except ValueError as exc:
            return _error("STATE_CONFLICT", str(exc), request.state.request_id, 409)

    site = settings.resolved_site_dir()
    if site.exists():
        app.mount("/", StaticFiles(directory=str(site), html=True), name="site")

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Morphosis Evolution OS service")
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--db")
    parser.add_argument("--site")
    parser.add_argument("--contract-file")
    parser.add_argument("--seed-reference", action="store_true")
    parser.add_argument("--bedrock-discovery", action="store_true")
    parser.add_argument("--aws-region")
    parser.add_argument("--live-traffic", action="store_true")
    parser.add_argument("--live-traffic-production", action="store_true")
    parser.add_argument("--canary-fraction", type=float)
    parser.add_argument("--ramp-fraction", type=float)
    parser.add_argument("--min-shadow-samples", type=int)
    parser.add_argument("--min-canary-samples", type=int)
    parser.add_argument("--min-ramp-samples", type=int)
    parser.add_argument("--max-traffic-mismatch-rate", type=float)
    parser.add_argument("--log-level")
    args = parser.parse_args()

    base = ServiceSettings.from_env()
    settings = base.with_overrides(
        host=args.host,
        port=args.port,
        db_path=args.db,
        site_dir=args.site,
        contract_file=args.contract_file,
        bedrock_discovery=True if args.bedrock_discovery else None,
        aws_region=args.aws_region,
        live_traffic=True if args.live_traffic else None,
        live_traffic_production=True if args.live_traffic_production else None,
        canary_fraction=args.canary_fraction,
        ramp_fraction=args.ramp_fraction,
        min_shadow_samples=args.min_shadow_samples,
        min_canary_samples=args.min_canary_samples,
        min_ramp_samples=args.min_ramp_samples,
        max_traffic_mismatch_rate=args.max_traffic_mismatch_rate,
        seed_reference=True if args.seed_reference else None,
        log_level=args.log_level,
    )
    configure_logging(settings.log_level)
    uvicorn.run(
        create_app(settings),
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        access_log=False,
        server_header=False,
    )


if __name__ == "__main__":
    main()
