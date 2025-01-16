# import subprocess
# import streamlit as st

# import os
# print("Current directory contents:", os.listdir('.'))

# def run_check():
#     subprocess.run(["python", "scrap.py"], check=True)

# if __name__ == "__main__":
#     # Run check.py (Playwright) first
#     run_check()
#     # Now run Streamlit
#     subprocess.run(["python", "-m" , "streamlit", "run", "stream.py"], check=True)


import subprocess
import threading
import os
from flask import Flask

# Create a dummy Flask app to keep a port open
app = Flask(__name__)

@app.route("/")
def health_check():
    return "Service is running!"

def start_dummy_server():
    port = int(os.getenv("PORT", 10000))  # Use Render's PORT environment variable
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

    # Start a dummy server in a separate thread
    threading.Thread(target=start_dummy_server, daemon=True).start()

    # Run scrap.py
    run_scrap()

    # Start Streamlit after scrap.py completes
    print("Starting Streamlit...")
    port = os.getenv("PORT", "8501")  # Default to 8501 if PORT is not set
    subprocess.run(["streamlit", "run", "stream.py", "--server.port", port, "--server.address", "0.0.0.0"], check=True)
