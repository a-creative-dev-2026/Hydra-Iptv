FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN touch cache.json && chmod 666 cache.json
# No fixed PORT ENV to let the platform decide
EXPOSE 5000
# Use shell form to allow environment variable expansion for PORT
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-5000} --no-access-log
