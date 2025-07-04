#!/usr/bin/env bash

# Optional but recommended: upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# (Optional) Pre-download Playwright dependencies if you're using it
python -m playwright install

# Any other custom setup you need
