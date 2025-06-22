# Dockerfile
FROM python:3.10-slim-buster

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your Flask application and templates
COPY . .

# Expose the port your Flask app will run on
EXPOSE 5000

# Command to run your Flask application
CMD ["python", "app.py"]