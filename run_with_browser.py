import webbrowser
import subprocess
import time

# Start the FastAPI server
process = subprocess.Popen(["uvicorn", "main:app", "--reload"])

# Wait a second for the server to start
time.sleep(2)

# Open the browser
webbrowser.open("http://127.0.0.1:8000/docs")

