from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

dispatched_songs = [
    {
        "team": "🎤equipo⁕⁕",
        "link": "https://youtu.be/m16O0gnNOLQ",
        "timestamp": "2025-04-24 18:30"
    }
]

@app.get("/songs")
async def get_dispatched_songs():
    return JSONResponse(content=dispatched_songs)
