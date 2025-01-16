import subprocess
import threading
import os
import sys
from flask import Flask
import time
import requests

# Create a dummy Flask app to keep a port open
app = Flask(__name__)

@app.route("/")
def health_check():
    return "Service is running!"

# Define a route to stop the Flask app
@app.route("/shutdown", methods=["POST"])
def shutdown():
    print("Shutting down Flask server...")
    sys.exit()  # This will stop the Flask server by raising a SystemExit

# Function to start Flask server in a separate thread
def start_dummy_server(port):
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def run_scrap():
    try:
        print("Running scrap.py...")
        # Stream real-time logs of scrap.py
        process = subprocess.Popen(
            ["python", "scrap.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True  # Decode bytes to strings
        )
        # Print output and errors line-by-line in real-time
        for line in process.stdout:
            print(f"SCRAP LOG: {line.strip()}", flush=True)
        for line in process.stderr:
            print(f"SCRAP ERROR: {line.strip()}", flush=True)

        # Wait for the process to complete
        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, "scrap.py")
        print("scrap.py completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running scrap.py: {e}", flush=True)
        exit(1)

if __name__ == "__main__":
    # Log the current directory for debugging
    print("Current directory contents:", os.listdir('.'))

    # Define the port for Flask and Streamlit
    flask_port = int(os.getenv("PORT", 10000))  # Default port for Flask

    # Start the Flask server in a separate thread
    flask_thread = threading.Thread(target=start_dummy_server, args=(flask_port,), daemon=True)
    flask_thread.start()
    
    # Give Flask a moment to start
    time.sleep(2)

    # Run the scrap.py script
    run_scrap()

    # Stop Flask by triggering the shutdown route
    print("Stopping Flask server...")
    try:
        # Trigger the shutdown route
        requests.post(f"http://127.0.0.1:{flask_port}/shutdown")
    except requests.exceptions.RequestException as e:
        print(f"Error stopping Flask server: {e}")

    # Start Streamlit after scrap.py completes and Flask is stopped
    print("Starting Streamlit...")
    streamlit_port = os.getenv("PORT", "8051")  # Default to 8051 if PORT is not set
    subprocess.run(["python", "-m", "streamlit", "run", "stream.py", "--server.port", streamlit_port, "--server.address", "0.0.0.0"], check=True)
