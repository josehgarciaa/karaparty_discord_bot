import requests

# URL of your FastAPI server

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
