# Use Playwright's pre-configured base image
FROM mcr.microsoft.com/playwright/python:v1.21.0-focal

# Set the working directory
WORKDIR /app

# Copy your application code into the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Optional: Install specific Playwright dependencies if needed
# RUN python -m playwright install

ENV PYTHONUNBUFFERED=1


# Expose the default port for Streamlit
EXPOSE 8501

# Command to run your application
CMD python app.py
