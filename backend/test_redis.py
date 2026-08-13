import asyncio
import os
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent))

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

from app.config import Settings

settings = Settings()

REDIS_URL = settings.REDIS_URL
REDIS_PASSWORD = settings.REDIS_PASSWORD

if REDIS_PASSWORD and not urlparse(REDIS_URL).password:
    parsed = urlparse(REDIS_URL)
    netloc = f":{REDIS_PASSWORD}@{parsed.hostname}"
    if parsed.port:
        netloc += f":{parsed.port}"
    REDIS_URL = urlunparse(parsed._replace(netloc=netloc))


async def main():
    import redis.asyncio as redis
    from redis.exceptions import AuthenticationError

    print(f"REDIS_URL={REDIS_URL}")

    client = redis.from_url(
        REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
        protocol=2,
    )

    try:
        pong = await client.ping()
        print(f"PING -> {'PONG' if pong else 'FAIL'}")

        info = await client.info("server")
        version = info.get("redis_version", "unknown")
        print(f"Redis version: {version}")
    except AuthenticationError:
        print("Auth failed with current REDIS_URL. Trying docker-compose default password...")
        parsed = urlparse(REDIS_URL)
        netloc = f":redis_password@{parsed.hostname}"
        if parsed.port:
            netloc += f":{parsed.port}"
        auth_url = urlunparse(parsed._replace(netloc=netloc))
        print(f"Retrying with REDIS_URL={auth_url}")
        await client.aclose()
        client = redis.from_url(
            auth_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            protocol=2,
        )
        pong = await client.ping()
        print(f"PING -> {'PONG' if pong else 'FAIL'}")
        info = await client.info("server")
        version = info.get("redis_version", "unknown")
        print(f"Redis version: {version}")
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
