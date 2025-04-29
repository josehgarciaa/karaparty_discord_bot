import asyncio
import uvicorn
from multiprocessing import Process

from bot.core import KarapartyBot
from myapi import app  # <-- wherever your FastAPI app is defined


def start_bot():
    bot = KarapartyBot(config_file="configs/config.yaml")
    bot.run_bot()  # This is blocking, that's fine

async def start_api():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, reload=False)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    # Start the bot in a different process
    bot_process = Process(target=start_bot)
    bot_process.start()

    # Now run FastAPI
    asyncio.run(start_api())

    # (optional) Wait for bot process to finish if you want
    bot_process.join()
