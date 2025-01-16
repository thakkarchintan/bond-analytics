import subprocess
import threading
import os
import sys

def run_scrap():
    try:
        print("Running scrap.py...")
        process = subprocess.Popen(
            ["python", "scrap.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True  # Decode bytes to strings
        )

        for line in process.stdout:
            print(f"SCRAP LOG: {line.strip()}", flush=True)
        for line in process.stderr:
            print(f"SCRAP ERROR: {line.strip()}", flush=True)

        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, "scrap.py")
        print("scrap.py completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running scrap.py: {e}", flush=True)

def run_streamlit():
    print("Starting Streamlit...")
    port = os.getenv("PORT", "8501")  # Default to 8501 if PORT is not set
    process = subprocess.Popen(
        ["streamlit", "run", "stream.py", "--server.port", port, "--server.address", "0.0.0.0"]
    )
    process.wait()  # Wait for Streamlit to finish before closing the script
    print("Streamlit completed successfully.")

if __name__ == "__main__":
    # Start the scrap process in a separate thread to run independently
    scrap_thread = threading.Thread(target=run_scrap)
    scrap_thread.start()

    # Immediately start Streamlit without blocking the scrap thread
    run_streamlit()

    # Ensure scrap thread has completed before exiting the program
    scrap_thread.join()
