FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt requirements-semantic.txt ./
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements-semantic.txt
COPY . .
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8010"]
