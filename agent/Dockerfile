# Use a Python base image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the agent code
COPY . .

# Set the entrypoint to run the agent
CMD ["python", "main.py", "dev"]