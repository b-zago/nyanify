import os
import sys
import hmac
import hashlib
from contextlib import asynccontextmanager

from httpx import RequestError
from fastapi import FastAPI, Response, status, Header
from pydantic import BaseModel
from typing import Annotated
from prometheus_client import start_http_server
from prometheus_fastapi_instrumentator import Instrumentator
from .bot import discord_hook


class Payload(BaseModel):
    receiver_id: int
    message: str


hmac_key = os.environ.get("HMAC_KEY")
if not hmac_key:
    sys.exit("Missing HMAC_KEY!")

# Metrics are served on their own port so they are never routed through the
# public Gateway. Prometheus scrapes this port directly, in-cluster.
METRICS_PORT = int(os.environ.get("METRICS_PORT", "9000"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Starts a small, dedicated HTTP server (daemon thread) that serves
    # /metrics from the default Prometheus registry on METRICS_PORT, while
    # uvicorn keeps serving the app on the main port.
    start_http_server(METRICS_PORT)
    yield


app = FastAPI(lifespan=lifespan)

# instrument() installs the middleware that records HTTP metrics for every
# request. No .expose() here, so /metrics is NOT mounted on the main app port.
Instrumentator().instrument(app)


@app.post("/webhook", status_code=200)
async def hook(
    x_nyanify_signature: Annotated[str, Header()], payload: Payload, res: Response
):

    signature = hmac.new(
        hmac_key.encode(), payload.model_dump_json().encode(), hashlib.sha256
    ).hexdigest()

    if hmac.compare_digest(signature, x_nyanify_signature):
        try:
            await discord_hook(payload.receiver_id, payload.message)
            return {"message": "Message sent!"}
        except RequestError as e:
            res.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return {"message": f"Error occured while sending a message: {e}"}
    else:
        res.status_code = status.HTTP_403_FORBIDDEN
        return {"message": "Nope"}


@app.get("/healthz")
async def healthz():
    """Liveness: process is up and able to serve. Keep this cheap and
    dependency-free so a flaky Discord API never restarts the pod."""
    return {"status": "ok"}


@app.get("/ready")
async def ready(res: Response):
    """Readiness/startup: only report ready once required config is present."""
    if not hmac_key or not os.environ.get("TOKEN"):
        res.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not ready"}
    return {"status": "ready"}
