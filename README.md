# nyanify

A lightweight FastAPI webhook that forwards messages to Discord DMs via the Discord REST API. Requests are authenticated using HMAC-SHA256.

## How it works

Send a signed `POST /webhook` request with a recipient Discord user ID and a message. If the signature is valid, the message is delivered as a Discord DM.

## Setup

**Environment variables** (put these in a `.env` file):

`HMAC_KEY` - Shared secret used to sign and verify requests
`TOKEN` - Discord bot token

## Running

**With Docker Compose (dev):**

```bash
docker compose up --watch
```

Hot-reloads on changes to `src/`. Runs on port `8000`.

**Locally:**

```bash
pip install -r requirements.txt
fastapi dev src/main.py --host 0.0.0.0
```

**Production:**

```bash
docker build -t nyanify .
docker run -e TOKEN=... -e HMAC_KEY=... -p 8000:8000 nyanify
```

## Sending a request

```python
import hmac
import hashlib
import requests

HMAC_KEY = "your_hmac_key"
payload = {"receiver_id": 123456789, "message": "Hello!"}

body = payload.model_dump_json()
sig = hmac.new(HMAC_KEY.encode(), body.encode(), hashlib.sha256).hexdigest()

requests.post(
    "http://localhost:8000/webhook",
    headers={"X-Nyanify-Signature": sig},
    json=payload,
)
```

Where `receiver_id` is a Discord user ID.

## Endpoints

`POST /webhook` - Send a Discord DM
`GET /healthcheck` - Health check

## Notes

- The target user must share a server with the bot, otherwise Discord will reject the DM.
- The HMAC signature is computed over the raw JSON body using SHA-256.
