# Deployment Guide

This document describes how to deploy, monitor, and run the FastAPI server and Streamlit dashboard.

## 1. Local Serving

To run the API locally:
```bash
# Activate virtual environment
source venv/bin/activate

# Start uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Uvicorn will automatically reload when code changes are saved. Swagger docs will be hosted at `http://localhost:8000/docs`.

To run the Streamlit portal locally:
```bash
streamlit run dashboard/streamlit_app.py --server.port 8501
```

## 2. Docker Container Deployment

The system is fully containerized. A single Dockerfile handles both the API and Streamlit.

### Build and Run with Docker Compose
```bash
# Build the images and run the services in the background
docker-compose up --build -d
```
Docker Compose launches:
* **`churn_api`** container on port `8000`
* **`churn_dashboard`** container on port `8501`

### Verify Health Status
Check container status:
```bash
docker-compose ps
```
Or query the API health check endpoint:
```bash
curl http://localhost:8000/health
```

### Stop Services
```bash
docker-compose down
```

## 3. Production Considerations
* **Model Registry:** For production, model weights (`model.pkl` and `pipeline.pkl`) should be versioned in a central registry (e.g. AWS S3 or MLflow Model Registry) rather than stored locally inside the container folder.
* **Gunicorn/Uvicorn workers:** In production Docker containers, wrap Uvicorn in a Gunicorn manager to handle multi-process worker pools:
  ```bash
  gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
  ```
