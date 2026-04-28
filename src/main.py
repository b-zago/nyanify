import os
import sys
import hmac
import hashlib

from httpx import RequestError
from fastapi import FastAPI, Response, status, Header
from pydantic import BaseModel
from typing import Annotated
from .bot import discord_hook


class Payload(BaseModel):
    receiver_id: int
    message: str


app = FastAPI()
hmac_key = os.environ.get("HMAC_KEY")
if not hmac_key:
    sys.exit("Missing HMAC_KEY!")


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


@app.get("/health")
async def health():
    return {"message": "yes"}


@app.get("/test")
async def health():
    return {"message": "epic"}
