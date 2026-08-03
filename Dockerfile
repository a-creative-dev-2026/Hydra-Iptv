FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN touch cache.json && chmod 666 cache.json
# Create directory for split playlists
RUN mkdir -p data/playlists
# Render default port is often 10000
ENV PORT=10000
EXPOSE 10000
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1 --no-access-log
