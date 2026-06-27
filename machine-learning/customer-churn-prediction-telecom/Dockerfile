FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# Install system dependencies (build-essential for compiling packages if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY config/ /app/config/
COPY src/ /app/src/
COPY app/ /app/app/
COPY dashboard/ /app/dashboard/
COPY scripts/ /app/scripts/

# Create folders for data, models, reports, figures, logs
RUN mkdir -p /app/data/raw /app/data/processed /app/data/external /app/models /app/reports /app/figures /app/logs

# Expose ports for both FastAPI (8000) and Streamlit (8501)
EXPOSE 8000
EXPOSE 8501

# The default command will run the health check, but docker-compose will override this
CMD ["python", "-c", "print('Telecom Churn Prediction Container Started')"]
