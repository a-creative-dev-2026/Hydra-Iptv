FROM python:3.9-slim

WORKDIR /app

# نسخ ملف المتطلبات أولاً (للاستفادة من التخزين المؤقت)
COPY requirements.txt .

# تثبيت المتطلبات
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي الملفات
COPY . .

# تشغيل السيرفر
CMD ["python", "app.py"]
