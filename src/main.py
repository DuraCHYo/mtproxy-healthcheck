import asyncio
from dotenv import load_dotenv
import urllib3
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from telethon import TelegramClient, connection
import requests
import os

urllib3.disable_warnings()
load_dotenv()
PROXY_SOURCE = "https://raw.githubusercontent.com/SoliSpirit/mtproto/refs/heads/master/all_proxies.txt"


@asynccontextmanager
async def lifespan_context(app: FastAPI):
    worker_task = asyncio.create_task(worker())
    print("Worker started")
    yield
    worker_task.cancel()
    print("Worker stopped")


app = FastAPI(lifespan=lifespan_context)
templates = Jinja2Templates(directory="src/templates")

proxy_results = {}


def parse_mtproto(line: str) -> tuple | None:
    try:
        clean = (
            line.replace("https://t.me/proxy?server=", "")
            .replace("port=", "")
            .replace("secret=", "")
        )
        parts = clean.split("&")

        if len(parts) < 3:
            return None

        return str(parts[0]), int(parts[1]), str(parts[2])
    except Exception:
        return None


async def worker():
    while True:
        try:
            r = requests.get(PROXY_SOURCE, verify=False)
            lines = r.text.strip().split("\n")

            for line in lines:
                params = parse_mtproto(line)
                if not params:
                    continue

                client = TelegramClient(
                    "",
                    int(os.getenv("API_ID")),
                    os.getenv("API_HASH"),
                    connection=connection.ConnectionTcpMTProxyRandomizedIntermediate,
                    proxy=params,
                    connection_retries=1,
                )

                try:
                    await asyncio.wait_for(client.connect(), timeout=5)

                    if client.is_connected():
                        proxy_results[line] = "up"
                    #     print(f"Success: {line}")
                    # else:
                    #     print(f"Down: {line}")

                except Exception as e:
                    print(f"Error connecting to {line}: {e}")

                finally:
                    await client.disconnect()

                await asyncio.sleep(1)

        except Exception as e:
            print(f"Worker error: {e}")

        await asyncio.sleep(60)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"proxies": proxy_results},
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
