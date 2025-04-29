import requests

# URL of your FastAPI server
import os
import yaml
from utils.error_reporter import report_error

# Path to the YAML file
config_path = "configs/config.yaml"
try:
    print(config_path)
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
except Exception as e:
    report_error(e, context="Please, remember to fill your configs/config.yaml file. Template is at config.yaml.template")
    raise e  # Stop startup if config cannot be loadedp startup if config cannot be loaded

url = config["kai_api"]["song_endpoint"]

print(url)


try:
    response = requests.get(url)
    if response.status_code == 200:
        print("Server is UP and responding!")
        print("Data received:")
        print(response.json())
    else:
        print(f"Server responded with status code: {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"Error connecting to the server: {e}")
