# دليل الصيانة والتشغيل - Amazon Deals Bot

## 📋 المحتويات

1. [مهام الصيانة اليومية](#مهام-الصيانة-اليومية)
2. [مهام الصيانة الأسبوعية](#مهام-الصيانة-الأسبوعية)
3. [مهام الصيانة الشهرية](#مهام-الصيانة-الشهرية)
4. [مراقبة النظام](#مراقبة-النظام)
5. [النسخ الاحتياطي](#النسخ-الاحتياطي)
6. [استكشاف الأخطاء](#استكشاف-الأخطاء)
7. [تحسين الأداء](#تحسين-الأداء)
8. [الأمان](#الأمان)

## 📅 مهام الصيانة اليومية

### 1. فحص حالة النظام

```bash
#!/bin/bash
# daily_check.sh

echo "=== فحص يومي للنظام - $(date) ==="

# فحص حالة العمليات
echo "1. فحص العمليات النشطة:"
ps aux | grep -E "(python.*run.py|amazon.*bot)" | grep -v grep

# فحص استخدام الموارد
echo -e "\n2. استخدام الموارد:"
echo "الذاكرة:"
free -h
echo "المعالج:"
top -bn1 | grep "Cpu(s)"
echo "المساحة:"
df -h | grep -E "(/$|/var|/home)"

# فحص قاعدة البيانات
echo -e "\n3. حالة قاعدة البيانات:"
mysql -u amazon_bot -p"$DB_PASSWORD" -e "
SELECT 
    'العروض النشطة' as metric, 
    COUNT(*) as value 
FROM amazon_deals_bot.deals 
WHERE deal_status = 'active'
UNION ALL
SELECT 
    'العروض اليوم' as metric, 
    COUNT(*) as value 
FROM amazon_deals_bot.deals 
WHERE DATE(created_at) = CURDATE()
UNION ALL
SELECT 
    'المستخدمين النشطين' as metric, 
    COUNT(*) as value 
FROM amazon_deals_bot.telegram_users 
WHERE is_active = 1;
"

# فحص السجلات
echo -e "\n4. آخر الأخطاء:"
tail -n 10 logs/errors.log | grep "$(date +%Y-%m-%d)"

echo "=== انتهى الفحص اليومي ==="
```

### 2. مراجعة السجلات

```bash
# فحص السجلات اليومية
tail -f logs/amazon_bot.log | grep "$(date +%Y-%m-%d)"

# فحص أخطاء اليوم
grep "ERROR\|CRITICAL" logs/amazon_bot.log | grep "$(date +%Y-%m-%d)"

# إحصائيات سريعة
echo "إحصائيات اليوم:"
echo "العروض المكتشفة: $(grep 'deal_found' logs/amazon_bot.log | grep "$(date +%Y-%m-%d)" | wc -l)"
echo "الرسائل المرسلة: $(grep 'message_sent' logs/telegram.log | grep "$(date +%Y-%m-%d)" | wc -l)"
echo "الأخطاء: $(grep 'ERROR' logs/errors.log | grep "$(date +%Y-%m-%d)" | wc -l)"
```

### 3. فحص الاتصالات

```bash
# فحص الاتصال بأمازون
curl -I https://www.amazon.sa --connect-timeout 10

# فحص الاتصال بتليجرام
curl -I https://api.telegram.org --connect-timeout 10

# فحص قاعدة البيانات
mysql -u amazon_bot -p"$DB_PASSWORD" -e "SELECT 1;" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ قاعدة البيانات متصلة"
else
    echo "❌ مشكلة في قاعدة البيانات"
fi
```

## 📊 مهام الصيانة الأسبوعية

### 1. تنظيف السجلات

```bash
#!/bin/bash
# weekly_cleanup.sh

echo "=== تنظيف أسبوعي - $(date) ==="

# تنظيف السجلات القديمة (أكثر من 7 أيام)
find logs/ -name "*.log" -mtime +7 -exec rm {} \;
echo "✅ تم تنظيف السجلات القديمة"

# ضغط السجلات الكبيرة
find logs/ -name "*.log" -size +100M -exec gzip {} \;
echo "✅ تم ضغط السجلات الكبيرة"

# تنظيف ملفات HTML المؤقتة
find data/temp/ -name "*.html" -mtime +1 -delete 2>/dev/null
echo "✅ تم تنظيف الملفات المؤقتة"
```

### 2. تحديث الإحصائيات

```bash
# تحديث إحصائيات الأسبوع
python3 -c "
from src.database import DatabaseManager
import datetime

db = DatabaseManager()

# حساب إحصائيات الأسبوع الماضي
end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=7)

stats = db.get_weekly_stats(start_date, end_date)
print(f'إحصائيات الأسبوع ({start_date} - {end_date}):')
print(f'العروض المكتشفة: {stats[\"deals_found\"]}')
print(f'الرسائل المرسلة: {stats[\"messages_sent\"]}')
print(f'المستخدمين الجدد: {stats[\"new_users\"]}')
print(f'معدل النجاح: {stats[\"success_rate\"]:.2f}%')
"
```

### 3. فحص الأداء

```bash
# تحليل أداء قاعدة البيانات
mysql -u amazon_bot -p"$DB_PASSWORD" amazon_deals_bot -e "
-- الاستعلامات البطيئة
SELECT 
    ROUND(AVG(query_time), 2) as avg_query_time,
    COUNT(*) as query_count
FROM mysql.slow_log 
WHERE start_time >= DATE_SUB(NOW(), INTERVAL 7 DAY);

-- حجم الجداول
SELECT 
    table_name,
    ROUND(((data_length + index_length) / 1024 / 1024), 2) as size_mb
FROM information_schema.tables 
WHERE table_schema = 'amazon_deals_bot'
ORDER BY size_mb DESC;
"
```

## 🗓️ مهام الصيانة الشهرية

### 1. تحديث النظام

```bash
#!/bin/bash
# monthly_update.sh

echo "=== تحديث شهري - $(date) ==="

# نسخ احتياطي قبل التحديث
./backup.sh

# تحديث المتطلبات
pip install --upgrade -r requirements.txt
echo "✅ تم تحديث مكتبات Python"

# تحديث قاعدة البيانات
mysql -u amazon_bot -p"$DB_PASSWORD" amazon_deals_bot < updates/monthly_update.sql
echo "✅ تم تحديث قاعدة البيانات"

# تحديث الإعدادات إذا لزم الأمر
if [ -f updates/config_update.yaml ]; then
    echo "⚠️ يوجد تحديث للإعدادات - يرجى المراجعة اليدوية"
fi
```

### 2. تنظيف البيانات القديمة

```sql
-- monthly_cleanup.sql

-- حذف العروض المنتهية الصلاحية (أكثر من 30 يوم)
DELETE FROM deals 
WHERE deal_status = 'expired' 
AND updated_at < DATE_SUB(NOW(), INTERVAL 30 DAY);

-- حذف سجلات الأسعار القديمة (الاحتفاظ بسجل واحد يومياً)
DELETE ph1 FROM price_history ph1
INNER JOIN price_history ph2 
WHERE ph1.product_id = ph2.product_id
AND ph1.recorded_at < DATE_SUB(NOW(), INTERVAL 90 DAY)
AND DATE(ph1.recorded_at) = DATE(ph2.recorded_at)
AND ph1.id < ph2.id;

-- حذف سجلات النشاط القديمة
DELETE FROM activity_log 
WHERE created_at < DATE_SUB(NOW(), INTERVAL 60 DAY);

-- تحديث إحصائيات الجداول
ANALYZE TABLE products, deals, price_history, telegram_users;
```

### 3. مراجعة الأمان

```bash
# فحص الصلاحيات
ls -la config/
ls -la logs/

# فحص كلمات المرور
echo "⚠️ تذكير: مراجعة كلمات المرور وتحديثها إذا لزم الأمر"

# فحص الشهادات (إذا كانت مستخدمة)
if [ -f ssl/cert.pem ]; then
    openssl x509 -in ssl/cert.pem -text -noout | grep "Not After"
fi
```

## 📈 مراقبة النظام

### 1. مؤشرات الأداء الرئيسية (KPIs)

```python
# monitoring/kpi_monitor.py

import time
from datetime import datetime, timedelta
from src.database import DatabaseManager

class KPIMonitor:
    def __init__(self):
        self.db = DatabaseManager()
    
    def get_daily_kpis(self):
        """الحصول على مؤشرات الأداء اليومية"""
        today = datetime.now().date()
        
        kpis = {
            'deals_discovered': self.db.count_deals_by_date(today),
            'messages_sent': self.db.count_messages_by_date(today),
            'active_users': self.db.count_active_users(),
            'error_rate': self.db.calculate_error_rate(today),
            'avg_response_time': self.db.get_avg_response_time(today),
            'system_uptime': self.get_system_uptime()
        }
        
        return kpis
    
    def check_thresholds(self, kpis):
        """فحص العتبات والتنبيهات"""
        alerts = []
        
        if kpis['deals_discovered'] < 10:
            alerts.append("⚠️ عدد العروض المكتشفة أقل من المتوقع")
        
        if kpis['error_rate'] > 5:
            alerts.append("🚨 معدل الأخطاء مرتفع")
        
        if kpis['avg_response_time'] > 30:
            alerts.append("⏰ زمن الاستجابة بطيء")
        
        return alerts

# استخدام المراقب
monitor = KPIMonitor()
kpis = monitor.get_daily_kpis()
alerts = monitor.check_thresholds(kpis)

print("مؤشرات الأداء اليومية:")
for key, value in kpis.items():
    print(f"{key}: {value}")

if alerts:
    print("\nتنبيهات:")
    for alert in alerts:
        print(alert)
```

### 2. مراقبة الموارد

```bash
#!/bin/bash
# resource_monitor.sh

# مراقبة استخدام الذاكرة
MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.2f", $3/$2 * 100.0)}')
if (( $(echo "$MEMORY_USAGE > 80" | bc -l) )); then
    echo "⚠️ استخدام الذاكرة مرتفع: ${MEMORY_USAGE}%"
fi

# مراقبة استخدام المعالج
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
    echo "⚠️ استخدام المعالج مرتفع: ${CPU_USAGE}%"
fi

# مراقبة مساحة القرص
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | cut -d'%' -f1)
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "⚠️ مساحة القرص منخفضة: ${DISK_USAGE}%"
fi

# مراقبة الاتصالات
CONNECTIONS=$(netstat -an | grep :3306 | wc -l)
if [ "$CONNECTIONS" -gt 100 ]; then
    echo "⚠️ عدد اتصالات قاعدة البيانات مرتفع: $CONNECTIONS"
fi
```

### 3. تنبيهات تلقائية

```python
# monitoring/alerting.py

import smtplib
import requests
from email.mime.text import MIMEText
from datetime import datetime

class AlertManager:
    def __init__(self, config):
        self.config = config
    
    def send_email_alert(self, subject, message):
        """إرسال تنبيه عبر البريد الإلكتروني"""
        try:
            msg = MIMEText(message, 'plain', 'utf-8')
            msg['Subject'] = subject
            msg['From'] = self.config['email']['from']
            msg['To'] = self.config['email']['to']
            
            server = smtplib.SMTP(self.config['email']['smtp_server'])
            server.starttls()
            server.login(self.config['email']['username'], 
                        self.config['email']['password'])
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            print(f"خطأ في إرسال البريد: {e}")
            return False
    
    def send_telegram_alert(self, message):
        """إرسال تنبيه عبر التليجرام"""
        try:
            url = f"https://api.telegram.org/bot{self.config['telegram']['bot_token']}/sendMessage"
            data = {
                'chat_id': self.config['telegram']['admin_chat_id'],
                'text': f"🚨 تنبيه النظام\n\n{message}",
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, data=data)
            return response.status_code == 200
        except Exception as e:
            print(f"خطأ في إرسال تنبيه التليجرام: {e}")
            return False
    
    def check_and_alert(self):
        """فحص النظام وإرسال التنبيهات"""
        # فحص العمليات
        if not self.is_process_running():
            self.send_telegram_alert("❌ النظام متوقف!")
        
        # فحص قاعدة البيانات
        if not self.is_database_responsive():
            self.send_telegram_alert("❌ قاعدة البيانات لا تستجيب!")
        
        # فحص معدل الأخطاء
        error_rate = self.get_error_rate()
        if error_rate > 10:
            self.send_telegram_alert(f"⚠️ معدل الأخطاء مرتفع: {error_rate}%")
```

## 💾 النسخ الاحتياطي

### 1. نسخ احتياطي يومي

```bash
#!/bin/bash
# daily_backup.sh

BACKUP_DIR="/backup/amazon_deals_bot"
DATE=$(date +%Y%m%d_%H%M%S)

# إنشاء مجلد النسخ الاحتياطي
mkdir -p "$BACKUP_DIR/daily"

# نسخ احتياطي لقاعدة البيانات
mysqldump -u amazon_bot -p"$DB_PASSWORD" amazon_deals_bot > "$BACKUP_DIR/daily/db_$DATE.sql"

# نسخ احتياطي للإعدادات
cp -r config/ "$BACKUP_DIR/daily/config_$DATE/"

# نسخ احتياطي للسجلات المهمة
cp logs/amazon_bot.log "$BACKUP_DIR/daily/log_$DATE.log"

# ضغط النسخة الاحتياطية
tar -czf "$BACKUP_DIR/daily/backup_$DATE.tar.gz" -C "$BACKUP_DIR/daily" db_$DATE.sql config_$DATE/ log_$DATE.log

# حذف الملفات المؤقتة
rm "$BACKUP_DIR/daily/db_$DATE.sql" "$BACKUP_DIR/daily/log_$DATE.log"
rm -rf "$BACKUP_DIR/daily/config_$DATE/"

# حذف النسخ القديمة (أكثر من 7 أيام)
find "$BACKUP_DIR/daily" -name "backup_*.tar.gz" -mtime +7 -delete

echo "✅ تم إنشاء النسخة الاحتياطية: backup_$DATE.tar.gz"
```

### 2. نسخ احتياطي أسبوعي

```bash
#!/bin/bash
# weekly_backup.sh

BACKUP_DIR="/backup/amazon_deals_bot"
DATE=$(date +%Y%m%d)

mkdir -p "$BACKUP_DIR/weekly"

# نسخة احتياطية كاملة
mysqldump -u amazon_bot -p"$DB_PASSWORD" --single-transaction --routines --triggers amazon_deals_bot > "$BACKUP_DIR/weekly/full_db_$DATE.sql"

# نسخ احتياطي للكود
tar -czf "$BACKUP_DIR/weekly/code_$DATE.tar.gz" --exclude='logs/*' --exclude='data/temp/*' .

# رفع النسخة الاحتياطية للسحابة (اختياري)
if command -v aws &> /dev/null; then
    aws s3 cp "$BACKUP_DIR/weekly/full_db_$DATE.sql" s3://your-backup-bucket/amazon-deals-bot/
    aws s3 cp "$BACKUP_DIR/weekly/code_$DATE.tar.gz" s3://your-backup-bucket/amazon-deals-bot/
fi

echo "✅ تم إنشاء النسخة الاحتياطية الأسبوعية"
```

### 3. استعادة النسخة الاحتياطية

```bash
#!/bin/bash
# restore_backup.sh

if [ $# -ne 1 ]; then
    echo "الاستخدام: $0 <backup_file.sql>"
    exit 1
fi

BACKUP_FILE=$1

echo "⚠️ تحذير: سيتم استبدال البيانات الحالية!"
read -p "هل تريد المتابعة؟ (y/N): " confirm

if [[ $confirm == [yY] ]]; then
    # إيقاف النظام
    python run.py stop
    
    # استعادة قاعدة البيانات
    mysql -u amazon_bot -p"$DB_PASSWORD" amazon_deals_bot < "$BACKUP_FILE"
    
    # إعادة تشغيل النظام
    python run.py start
    
    echo "✅ تم استعادة النسخة الاحتياطية بنجاح"
else
    echo "تم إلغاء العملية"
fi
```

## 🔧 تحسين الأداء

### 1. تحسين قاعدة البيانات

```sql
-- database_optimization.sql

-- تحسين الفهارس
ANALYZE TABLE products, deals, price_history, telegram_users;

-- إضافة فهارس مفيدة
CREATE INDEX idx_deals_quality_date ON deals(quality_score DESC, created_at DESC);
CREATE INDEX idx_products_category_rating ON products(category_id, rating DESC);
CREATE INDEX idx_price_history_product_date ON price_history(product_id, recorded_at DESC);

-- تحسين إعدادات MySQL
SET GLOBAL innodb_buffer_pool_size = 1073741824; -- 1GB
SET GLOBAL query_cache_size = 268435456; -- 256MB
SET GLOBAL query_cache_type = 1;
SET GLOBAL max_connections = 200;

-- تنظيف الجداول
OPTIMIZE TABLE products, deals, price_history, telegram_users;
```

### 2. تحسين الكود

```python
# performance_optimization.py

import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

class PerformanceOptimizer:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)
    
    async def scrape_concurrent(self, urls):
        """استخراج متوازي للصفحات"""
        async with aiohttp.ClientSession() as session:
            tasks = [self.scrape_url(session, url) for url in urls]
            return await asyncio.gather(*tasks, return_exceptions=True)
    
    def optimize_database_queries(self):
        """تحسين استعلامات قاعدة البيانات"""
        # استخدام connection pooling
        # تجميع الاستعلامات
        # استخدام prepared statements
        pass
    
    def implement_caching(self):
        """تنفيذ نظام التخزين المؤقت"""
        # Redis للتخزين المؤقت
        # Cache للاستعلامات المتكررة
        # Cache للصفحات المستخرجة
        pass
```

### 3. مراقبة الأداء

```python
# performance_monitor.py

import time
import psutil
from functools import wraps

def monitor_performance(func):
    """مراقب أداء للدوال"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        execution_time = end_time - start_time
        memory_used = end_memory - start_memory
        
        print(f"{func.__name__}: {execution_time:.2f}s, {memory_used/1024/1024:.2f}MB")
        
        return result
    return wrapper

# استخدام المراقب
@monitor_performance
def scrape_products():
    # كود الاستخراج
    pass
```

## 🔒 الأمان

### 1. تأمين قاعدة البيانات

```sql
-- security_setup.sql

-- إنشاء مستخدم محدود الصلاحيات
CREATE USER 'amazon_bot_readonly'@'localhost' IDENTIFIED BY 'readonly_password';
GRANT SELECT ON amazon_deals_bot.* TO 'amazon_bot_readonly'@'localhost';

-- تقييد الوصول
REVOKE ALL PRIVILEGES ON *.* FROM 'amazon_bot'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON amazon_deals_bot.* TO 'amazon_bot'@'localhost';

-- تفعيل SSL
-- ALTER USER 'amazon_bot'@'localhost' REQUIRE SSL;

FLUSH PRIVILEGES;
```

### 2. تأمين الملفات

```bash
#!/bin/bash
# security_setup.sh

# تعيين صلاحيات آمنة للملفات
chmod 600 config/config.yaml
chmod 600 .env
chmod 700 logs/
chmod 755 src/

# إنشاء مستخدم مخصص للنظام
sudo useradd -r -s /bin/false amazon-bot
sudo chown -R amazon-bot:amazon-bot /opt/amazon-deals-bot

# تشفير كلمات المرور الحساسة
echo "تذكير: استخدم متغيرات البيئة لكلمات المرور"
```

### 3. مراقبة الأمان

```python
# security_monitor.py

import hashlib
import os
from datetime import datetime

class SecurityMonitor:
    def __init__(self):
        self.config_hash = self.get_file_hash('config/config.yaml')
    
    def get_file_hash(self, filepath):
        """حساب hash للملف"""
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    def check_file_integrity(self):
        """فحص سلامة الملفات"""
        current_hash = self.get_file_hash('config/config.yaml')
        if current_hash != self.config_hash:
            self.log_security_event("تم تعديل ملف الإعدادات")
            return False
        return True
    
    def log_security_event(self, event):
        """تسجيل أحداث الأمان"""
        timestamp = datetime.now().isoformat()
        with open('logs/security.log', 'a') as f:
            f.write(f"{timestamp} - {event}\n")
    
    def check_failed_logins(self):
        """فحص محاولات تسجيل الدخول الفاشلة"""
        # فحص سجلات MySQL
        # فحص سجلات النظام
        pass
```

---

## 📞 الدعم الفني

للحصول على المساعدة في الصيانة:

- **البريد الإلكتروني**: maintenance@amazon-deals-bot.com
- **التليجرام**: [@AmazonDealsSupport](https://t.me/AmazonDealsSupport)
- **GitHub Issues**: [رابط المشاكل](https://github.com/your-repo/amazon-deals-bot/issues)

---

<div align="center">

**دليل الصيانة - Amazon Deals Bot**

[⬆️ العودة للأعلى](#دليل-الصيانة-والتشغيل---amazon-deals-bot)

</div>

