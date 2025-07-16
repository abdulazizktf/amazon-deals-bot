# Dockerfile لنظام Amazon Deals Bot
# تاريخ الإنشاء: 11 يوليو 2025

FROM python:3.11-slim

# تعيين متغيرات البيئة
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TZ=Asia/Riyadh

# تثبيت المتطلبات النظام
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    wget \
    cron \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# إعداد المنطقة الزمنية
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# إنشاء مستخدم غير root
RUN useradd --create-home --shell /bin/bash botuser

# إنشاء مجلد العمل
WORKDIR /app

# نسخ ملف المتطلبات
COPY requirements.txt .

# تثبيت المتطلبات Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# نسخ الكود
COPY . .

# إنشاء المجلدات المطلوبة
RUN mkdir -p logs data config tests && \
    chown -R botuser:botuser /app

# التبديل للمستخدم غير root
USER botuser

# إعداد متغيرات البيئة للتطبيق
ENV PYTHONPATH=/app/src
ENV CONFIG_PATH=/app/config/config.yaml

# فحص صحة التطبيق
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# المنفذ المكشوف (للمراقبة)
EXPOSE 8000

# الأمر الافتراضي
CMD ["python", "run.py", "start"]

# Labels للتوثيق
LABEL maintainer="Amazon Deals Bot Team"
LABEL version="1.0.0"
LABEL description="AI-powered Amazon deals scraper and Telegram bot"
LABEL org.opencontainers.image.source="https://github.com/your-repo/amazon-deals-bot"

