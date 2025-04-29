from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os
import json

app = FastAPI()

# Path to the JSON file
json_file_path = os.path.join(os.path.dirname(__file__), "dispatched_songs.json")

@app.get("/songs")
async def get_dispatched_songs():
    if os.path.isfile(json_file_path):
        try:
            with open(json_file_path, "r", encoding="utf-8") as f:
                dispatched_songs = json.load(f)
        except json.JSONDecodeError:
            # If the file is corrupted or not proper JSON
            dispatched_songs = []
    else:
        dispatched_songs = []
    
    return JSONResponse(content=dispatched_songs)
