FROM python:3.9-slim

WORKDIR /app

# نسخ ملف المتطلبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ جميع الملفات
COPY . .

# إنشاء ملف الكاش
RUN touch cache.json

# تشغيل السيرفر
CMD ["python", "app.py"]
