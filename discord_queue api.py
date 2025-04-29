# launcher_async.py
import asyncio
import uvicorn
from fastapi import FastAPI
from bot.core import KarapartyBot

# import your FastAPI app  
from api import app

async def main():
    # 1) Set up Uvicorn server but don’t block
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)

    # 2) Instantiate your bot
    bot = KarapartyBot(config_file="configs/config.yaml")

    # 3) Run both concurrently
    await asyncio.gather(
        server.serve(),       # FastAPI
        bot.start_bot(),      # <-- assuming you have an async entrypoint for your bot
    )

if __name__ == "__main__":
    asyncio.run(main())
