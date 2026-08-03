FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN touch cache.json && chmod 666 cache.json
# Strictly use 5000 as per Render logs
ENV PORT=5000
EXPOSE 5000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000", "--no-access-log", "--workers", "1"]
