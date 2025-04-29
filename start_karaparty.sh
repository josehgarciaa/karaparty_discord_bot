source  ~/kai_discord_bot/kai_discord_bot_env/bin/activate

python3 -u discord_queue_api.py > _kai_queue_api_log 2>&1 &
echo $! > _kai_queue_api_pid


#uvicorn kai_api:app --reload --host 0.0.0.0 --port 8000 > _server_log 2>&1 &
#echo $! > _server_pid
