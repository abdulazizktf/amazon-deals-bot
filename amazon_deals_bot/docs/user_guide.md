# دليل المستخدم - Amazon Deals Bot

## 📚 المحتويات

1. [البدء السريع](#البدء-السريع)
2. [إعداد بوت التليجرام](#إعداد-بوت-التليجرام)
3. [إعداد قاعدة البيانات](#إعداد-قاعدة-البيانات)
4. [تخصيص الإعدادات](#تخصيص-الإعدادات)
5. [استخدام النظام](#استخدام-النظام)
6. [إدارة القنوات والمستخدمين](#إدارة-القنوات-والمستخدمين)
7. [مراقبة الأداء](#مراقبة-الأداء)
8. [الأسئلة الشائعة](#الأسئلة-الشائعة)

## 🚀 البدء السريع

### الخطوة 1: تحضير البيئة

```bash
# تحميل المشروع
git clone https://github.com/your-repo/amazon-deals-bot.git
cd amazon-deals-bot

# إنشاء بيئة Python
python3 -m venv venv
source venv/bin/activate

# تثبيت المتطلبات
pip install -r requirements.txt
```

### الخطوة 2: الإعداد الأساسي

```bash
# نسخ ملفات الإعداد
cp config/config.yaml.example config/config.yaml
cp .env.example .env

# تعديل الإعدادات الأساسية
nano config/config.yaml
nano .env
```

### الخطوة 3: إعداد قاعدة البيانات

```bash
# تسجيل الدخول إلى MySQL
mysql -u root -p

# تنفيذ ملف الإعداد
source setup_database.sql;
```

### الخطوة 4: تشغيل النظام

```bash
# التشغيل العادي
python run.py start

# أو استخدام التشغيل السريع
./quick_start.sh start
```

## 🤖 إعداد بوت التليجرام

### إنشاء البوت

1. **تحدث مع BotFather**:
   - افتح التليجرام وابحث عن `@BotFather`
   - أرسل `/start` ثم `/newbot`
   - اختر اسماً للبوت (مثل: Amazon Deals Bot)
   - اختر معرفاً للبوت (مثل: `@your_amazon_deals_bot`)

2. **احفظ التوكن**:
   ```
   Use this token to access the HTTP API:
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

3. **إعداد أوامر البوت**:
   ```
   /setcommands
   start - بدء التفاعل مع البوت
   help - عرض المساعدة
   subscribe - الاشتراك في العروض
   unsubscribe - إلغاء الاشتراك
   settings - إعدادات المستخدم
   stats - إحصائيات العروض
   ```

### إعداد القنوات

#### إنشاء قناة عامة

1. **إنشاء القناة**:
   - افتح التليجرام
   - اضغط على "قناة جديدة"
   - اختر اسماً للقناة (مثل: "عروض أمازون السعودية")
   - اختر معرفاً للقناة (مثل: `@amazon_deals_sa`)

2. **إضافة البوت كمشرف**:
   - ادخل إعدادات القناة
   - اضغط على "المشرفون"
   - اضغط على "إضافة مشرف"
   - ابحث عن البوت وأضفه
   - امنحه صلاحية "نشر الرسائل"

#### إنشاء مجموعة خاصة

1. **إنشاء المجموعة**:
   - اضغط على "مجموعة جديدة"
   - أضف البوت إلى المجموعة
   - اجعل المجموعة "سوبر جروب"

2. **الحصول على معرف المجموعة**:
   ```bash
   # أرسل رسالة في المجموعة ثم استخدم:
   curl "https://api.telegram.org/bot<TOKEN>/getUpdates"
   ```

### تحديث الإعدادات

```yaml
# config/config.yaml
telegram:
  bot_token: "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
  channels:
    - id: "@amazon_deals_sa"
      name: "عروض أمازون السعودية"
      type: "channel"
      active: true
    - id: "-1001234567890"
      name: "مجموعة العروض الخاصة"
      type: "group"
      active: true
```

## 🗄️ إعداد قاعدة البيانات

### تثبيت MySQL

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install mysql-server
sudo mysql_secure_installation
```

#### CentOS/RHEL
```bash
sudo yum install mysql-server
sudo systemctl start mysqld
sudo mysql_secure_installation
```

#### macOS
```bash
brew install mysql
brew services start mysql
```

### إنشاء قاعدة البيانات

```sql
-- تسجيل الدخول كـ root
mysql -u root -p

-- إنشاء قاعدة البيانات
CREATE DATABASE amazon_deals_bot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- إنشاء مستخدم
CREATE USER 'amazon_bot'@'localhost' IDENTIFIED BY 'secure_password_2025';
GRANT ALL PRIVILEGES ON amazon_deals_bot.* TO 'amazon_bot'@'localhost';
FLUSH PRIVILEGES;

-- استخدام قاعدة البيانات
USE amazon_deals_bot;

-- تنفيذ ملف الإعداد
SOURCE setup_database.sql;
```

### فحص الإعداد

```sql
-- فحص الجداول
SHOW TABLES;

-- فحص البيانات الأساسية
SELECT * FROM categories;
SELECT COUNT(*) FROM products;
```

## ⚙️ تخصيص الإعدادات

### ملف الإعدادات الرئيسي

```yaml
# config/config.yaml

# إعدادات قاعدة البيانات
database:
  host: "localhost"
  port: 3306
  username: "amazon_bot"
  password: "secure_password_2025"
  database: "amazon_deals_bot"
  charset: "utf8mb4"
  pool_size: 10

# إعدادات التليجرام
telegram:
  bot_token: "YOUR_BOT_TOKEN"
  api_url: "https://api.telegram.org/bot"
  max_message_length: 4096
  rate_limit:
    messages_per_second: 30
    messages_per_minute: 20
  channels:
    - id: "@your_channel"
      name: "القناة الرئيسية"
      active: true

# إعدادات الاستخراج
scraping:
  base_url: "https://www.amazon.sa"
  user_agents:
    - "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  headers:
    Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    Accept-Language: "ar,en-US;q=0.7,en;q=0.3"
  delays:
    min_delay: 2
    max_delay: 5
    error_delay: 10
  retries:
    max_retries: 3
    backoff_factor: 2
  timeout: 30

# إعدادات العروض
deals:
  min_discount_percentage: 20
  min_original_price: 100
  max_original_price: 5000
  categories:
    - "electronics"
    - "computers"
    - "mobile-phones"
    - "home-kitchen"
  quality_scoring:
    discount_weight: 0.4
    rating_weight: 0.3
    review_count_weight: 0.2
    price_range_weight: 0.1

# إعدادات الرسائل
messaging:
  max_deals_per_message: 1
  include_image: true
  message_template: |
    🔥 **عرض مميز من أمازون السعودية**
    
    📱 **{product_name}**
    ⭐ التقييم: {rating}/5 ({review_count} تقييم)
    
    💰 السعر الأصلي: ~~{original_price} ريال~~
    🎯 سعر العرض: **{deal_price} ريال**
    💸 الخصم: {discount_percentage}% ({discount_amount} ريال)
    
    🛒 [اشتري الآن]({amazon_url})

# إعدادات الجدولة
scheduling:
  scraping_interval: 3600  # كل ساعة
  message_sending_interval: 300  # كل 5 دقائق
  cleanup_interval: 86400  # يومياً
  peak_hours:
    start: 18  # 6 مساءً
    end: 23    # 11 مساءً
    interval: 1800  # كل 30 دقيقة

# إعدادات السجلات
logging:
  level: "INFO"
  format: "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}"
  files:
    main: "logs/amazon_bot.log"
    scraping: "logs/scraping.log"
    telegram: "logs/telegram.log"
    errors: "logs/errors.log"
```

### متغيرات البيئة

```bash
# .env

# إعدادات أساسية
TELEGRAM_BOT_TOKEN=your_bot_token_here
DB_PASSWORD=your_database_password
ADMIN_CHAT_ID=your_admin_chat_id

# إعدادات الأمان
ENCRYPTION_KEY=your_32_character_encryption_key
JWT_SECRET=your_jwt_secret_key

# إعدادات التطوير
DEBUG_MODE=false
TEST_MODE=false
LOG_LEVEL=INFO

# إعدادات الأداء
MAX_CONCURRENT_SCRAPERS=5
SCRAPING_TIMEOUT=30
DATABASE_POOL_SIZE=10
```

## 🎮 استخدام النظام

### تشغيل النظام

#### الطريقة الأولى: التشغيل المباشر
```bash
python run.py start
```

#### الطريقة الثانية: التشغيل السريع
```bash
./quick_start.sh start
```

#### الطريقة الثالثة: Docker
```bash
docker-compose up -d
```

### أوامر الإدارة

```bash
# عرض حالة النظام
python run.py status

# تشغيل الاختبارات
python run.py test

# إيقاف النظام
python run.py stop

# عرض المساعدة
python run.py help
```

### مراقبة النظام

#### مراقبة السجلات
```bash
# السجل الرئيسي
tail -f logs/amazon_bot.log

# سجل الاستخراج
tail -f logs/scraping.log

# سجل التليجرام
tail -f logs/telegram.log

# سجل الأخطاء
tail -f logs/errors.log
```

#### مراقبة قاعدة البيانات
```sql
-- عدد العروض النشطة
SELECT COUNT(*) FROM deals WHERE deal_status = 'active';

-- العروض المضافة اليوم
SELECT COUNT(*) FROM deals WHERE DATE(created_at) = CURDATE();

-- أفضل العروض
SELECT * FROM deals ORDER BY quality_score DESC LIMIT 10;
```

## 👥 إدارة القنوات والمستخدمين

### إضافة قناة جديدة

1. **إنشاء القناة في التليجرام**
2. **إضافة البوت كمشرف**
3. **تحديث ملف الإعدادات**:

```yaml
telegram:
  channels:
    - id: "@new_channel"
      name: "القناة الجديدة"
      type: "channel"
      active: true
      settings:
        max_deals_per_day: 50
        min_quality_score: 7.0
```

4. **إعادة تشغيل النظام**

### إدارة المستخدمين

#### عرض المستخدمين النشطين
```sql
SELECT telegram_id, username, first_name, created_at 
FROM telegram_users 
WHERE is_active = 1 
ORDER BY created_at DESC;
```

#### إحصائيات المستخدمين
```sql
SELECT 
    COUNT(*) as total_users,
    SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_users,
    SUM(CASE WHEN DATE(last_interaction) = CURDATE() THEN 1 ELSE 0 END) as daily_active
FROM telegram_users;
```

### تخصيص الرسائل

#### قالب الرسالة الأساسي
```yaml
messaging:
  message_template: |
    🔥 **عرض مميز**
    
    📱 {product_name}
    ⭐ {rating}/5 ({review_count} تقييم)
    
    💰 ~~{original_price} ريال~~
    🎯 **{deal_price} ريال**
    💸 خصم {discount_percentage}%
    
    🛒 [اشتري الآن]({amazon_url})
```

#### قوالب مخصصة للفئات
```yaml
messaging:
  category_templates:
    electronics: |
      ⚡ **عرض إلكترونيات**
      {product_name}
      خصم {discount_percentage}% - {deal_price} ريال
    
    fashion: |
      👗 **عرض أزياء**
      {product_name}
      خصم {discount_percentage}% - {deal_price} ريال
```

## 📊 مراقبة الأداء

### لوحة المراقبة الأساسية

```bash
# عرض إحصائيات سريعة
python -c "
from src.database import DatabaseManager
db = DatabaseManager()
stats = db.get_system_stats()
print(f'العروض النشطة: {stats[\"active_deals\"]}')
print(f'المستخدمين النشطين: {stats[\"active_users\"]}')
print(f'الرسائل المرسلة اليوم: {stats[\"messages_today\"]}')
"
```

### مراقبة الأداء المتقدمة

#### استخدام Prometheus و Grafana

1. **تشغيل خدمات المراقبة**:
```bash
docker-compose up -d monitoring grafana
```

2. **الوصول للوحات المراقبة**:
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000 (admin/admin123)

#### مؤشرات الأداء الرئيسية

- **معدل اكتشاف العروض**: عدد العروض الجديدة في الساعة
- **جودة العروض**: متوسط نقاط الجودة
- **معدل الاستجابة**: زمن استجابة النظام
- **معدل النجاح**: نسبة العمليات الناجحة

### تنبيهات الأداء

```yaml
# config/alerts.yaml
alerts:
  low_deals_rate:
    threshold: 5  # أقل من 5 عروض في الساعة
    action: "send_admin_notification"
  
  high_error_rate:
    threshold: 10  # أكثر من 10% أخطاء
    action: "restart_scraper"
  
  database_slow:
    threshold: 5000  # أكثر من 5 ثوانٍ
    action: "optimize_queries"
```

## ❓ الأسئلة الشائعة

### س: كيف أغير فئات المنتجات المراد البحث فيها؟

ج: عدّل ملف `config/config.yaml`:

```yaml
deals:
  categories:
    - "electronics"
    - "computers"
    - "mobile-phones"
    - "books"  # إضافة فئة جديدة
```

### س: كيف أزيد من سرعة اكتشاف العروض؟

ج: قلل من `scraping_interval` في الإعدادات:

```yaml
scheduling:
  scraping_interval: 1800  # كل 30 دقيقة بدلاً من ساعة
```

### س: كيف أضيف فلاتر إضافية للعروض؟

ج: عدّل إعدادات العروض:

```yaml
deals:
  min_discount_percentage: 30  # خصم أدنى 30%
  min_rating: 4.0  # تقييم أدنى 4 نجوم
  min_review_count: 50  # عدد تقييمات أدنى
```

### س: كيف أضيف قناة تليجرام جديدة؟

ج: 
1. أنشئ القناة وأضف البوت كمشرف
2. أضف القناة في الإعدادات:

```yaml
telegram:
  channels:
    - id: "@new_channel"
      name: "القناة الجديدة"
      active: true
```

### س: كيف أحل مشكلة "Rate limit exceeded"؟

ج: زد من التأخير بين الطلبات:

```yaml
scraping:
  delays:
    min_delay: 5  # زيادة التأخير
    max_delay: 10
```

### س: كيف أنشئ نسخة احتياطية من البيانات؟

ج: استخدم الأمر التالي:

```bash
mysqldump -u amazon_bot -p amazon_deals_bot > backup_$(date +%Y%m%d).sql
```

### س: كيف أستعيد النسخة الاحتياطية؟

ج: استخدم الأمر التالي:

```bash
mysql -u amazon_bot -p amazon_deals_bot < backup_20250711.sql
```

### س: كيف أراقب استخدام الموارد؟

ج: استخدم الأوامر التالية:

```bash
# مراقبة الذاكرة والمعالج
htop

# مراقبة مساحة القرص
df -h

# مراقبة قاعدة البيانات
mysql -u amazon_bot -p -e "SHOW PROCESSLIST;"
```

### س: كيف أحدث النظام لإصدار جديد؟

ج: 
1. أوقف النظام: `python run.py stop`
2. احفظ نسخة احتياطية من الإعدادات
3. حدث الكود: `git pull origin main`
4. حدث المتطلبات: `pip install -r requirements.txt`
5. شغل النظام: `python run.py start`

---

للمزيد من المساعدة، راجع [README.md](../README.md) أو تواصل معنا عبر [GitHub Issues](https://github.com/your-repo/amazon-deals-bot/issues).

