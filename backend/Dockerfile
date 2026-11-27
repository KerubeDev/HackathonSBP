FROM python:3.11-alpine
WORKDIR /app
ENV PYTHONPATH=/app
RUN apk add --no-cache gcc musl-dev libffi-dev postgresql-dev
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=120 --retries=5 -r requirements.txt
COPY app ./app
COPY tests ./tests
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
