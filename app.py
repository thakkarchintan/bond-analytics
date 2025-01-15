import subprocess
import streamlit as st

import os
print("Current directory contents:", os.listdir('.'))

def run_check():
    subprocess.run(["python", "scarp.py"], check=True)

if __name__ == "__main__":
    # Run check.py (Playwright) first
    run_check()
    # Now run Streamlit
    subprocess.run(["python", "-m" , "streamlit", "run", "stream.py"], check=True)
