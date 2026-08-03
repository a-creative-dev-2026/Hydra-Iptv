FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN touch cache.json

# ✅ استخدام المنفذ المتغير
EXPOSE 10000

# ✅ استخدم PORT من Render أو 10000 كقيمة افتراضية
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:${PORT:-10000}"]
