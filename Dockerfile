FROM python:3.13-slim

WORKDIR /app

# Copy requirements first to leverage Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create data directory for storage
RUN mkdir -p /app/data /app/logs /app/backups

# Make the shell scripts executable
RUN chmod +x manage.sh maintenance.sh monitor.sh

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default command to run the application
CMD ["python", "-m", "src.main"] 