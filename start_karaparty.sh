#!/bin/bash

# Activate the virtual environment
source ~/kai_discord_bot/kai_discord_bot_env/bin/activate

# Start the bot
echo "Starting the Discord bot..."
nohup python3 -u discord_queue.py > _kai_queue_log 2>&1 &
echo $! > _kai_queue_pid

# Start the FastAPI server (no --reload)
echo "Starting the FastAPI server..."
nohup uvicorn kai_api:app --host 0.0.0.0 --port 8000 > _server_log 2>&1 &
echo $! > _server_pid
