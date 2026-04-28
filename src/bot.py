import os
import sys
import httpx

token = os.environ.get("TOKEN")
if not token:
    sys.exit("Missing discord TOKEN!")


async def discord_hook(id: str, message: str):
    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://discord.com/api/users/@me/channels",
            headers={"Authorization": f"Bot {token}"},
            json={"recipient_id": id},
        )
        channel = r.json()

        await client.post(
            f"https://discord.com/api/channels/{channel["id"]}/messages",
            headers={"Authorization": f"Bot {token}"},
            json={"content": message},
        )
