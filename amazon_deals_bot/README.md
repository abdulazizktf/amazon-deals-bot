# Amazon Deals Bot 🤖

نظام ذكي للبحث التلقائي عن أفضل العروض من أمازون السعودية ونشرها في قنوات التليجرام

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)

## 📋 المحتويات

- [نظرة عامة](#نظرة-عامة)
- [المميزات](#المميزات)
- [متطلبات النظام](#متطلبات-النظام)
- [التثبيت](#التثبيت)
- [الإعداد](#الإعداد)
- [الاستخدام](#الاستخدام)
- [الهيكل التقني](#الهيكل-التقني)
- [الصيانة](#الصيانة)
- [استكشاف الأخطاء](#استكشاف-الأخطاء)
- [المساهمة](#المساهمة)
- [الترخيص](#الترخيص)

## 🎯 نظرة عامة

Amazon Deals Bot هو نظام ذكي مطور بلغة Python يستخدم تقنيات الذكاء الاصطناعي للبحث التلقائي عن أفضل العروض والخصومات من موقع أمازون السعودية، ثم ينشرها تلقائياً في قنوات التليجرام المحددة.

### كيف يعمل النظام؟

1. **البحث الذكي**: يبحث النظام في فئات مختلفة من المنتجات على أمازون السعودية
2. **تحليل العروض**: يحلل العروض ويقيمها باستخدام خوارزميات ذكية
3. **الفلترة**: يفلتر العروض عالية الجودة فقط
4. **النشر التلقائي**: ينشر العروض المختارة في قنوات التليجرام
5. **المراقبة**: يراقب الأسعار ويتتبع التغييرات

## ✨ المميزات

### 🔍 البحث والاستخراج
- **بحث ذكي** في فئات متعددة من المنتجات
- **استخراج تلقائي** لبيانات المنتجات والأسعار
- **تتبع الأسعار** ومراقبة التغييرات
- **كشف العروض** الجديدة والخصومات

### 🤖 الذكاء الاصطناعي
- **تحليل جودة العروض** باستخدام خوارزميات متقدمة
- **تصنيف العروض** حسب الأهمية والجودة
- **فلترة ذكية** للعروض المكررة أو منخفضة الجودة
- **تعلم من تفاعل المستخدمين**

### 📱 التليجرام
- **بوت تليجرام** تفاعلي ومتقدم
- **نشر تلقائي** في قنوات متعددة
- **رسائل منسقة** وجذابة بصرياً
- **إدارة المستخدمين** والاشتراكات

### 📊 المراقبة والإحصائيات
- **لوحة مراقبة** شاملة
- **إحصائيات مفصلة** عن الأداء
- **تقارير يومية** تلقائية
- **تنبيهات الأخطاء** الفورية

### 🔧 المرونة والتخصيص
- **إعدادات قابلة للتخصيص** بالكامل
- **دعم فئات متعددة** من المنتجات
- **جدولة مرنة** للمهام
- **واجهة برمجية** للتكامل

## 🖥️ متطلبات النظام

### المتطلبات الأساسية
- **Python 3.8+**
- **MySQL 8.0+** أو **MariaDB 10.5+**
- **Redis 6.0+** (اختياري للتخزين المؤقت)
- **4GB RAM** كحد أدنى (8GB مُوصى به)
- **10GB مساحة تخزين** كحد أدنى

### المتطلبات الاختيارية
- **Docker & Docker Compose** للنشر السهل
- **Nginx** للـ reverse proxy
- **Prometheus & Grafana** للمراقبة المتقدمة

### متطلبات الشبكة
- **اتصال إنترنت مستقر**
- **وصول إلى amazon.sa**
- **وصول إلى Telegram API**

## 🚀 التثبيت

### التثبيت السريع

```bash
# 1. استنساخ المشروع
git clone https://github.com/your-repo/amazon-deals-bot.git
cd amazon-deals-bot

# 2. تشغيل الإعداد التلقائي
./quick_start.sh setup

# 3. تشغيل النظام
./quick_start.sh start
```

### التثبيت اليدوي

#### 1. إعداد البيئة

```bash
# إنشاء بيئة Python افتراضية
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# أو
venv\\Scripts\\activate  # Windows

# تثبيت المتطلبات
pip install -r requirements.txt
```

#### 2. إعداد قاعدة البيانات

```bash
# تسجيل الدخول إلى MySQL
mysql -u root -p

# تنفيذ ملف الإعداد
source setup_database.sql;
```

#### 3. إعداد الملفات

```bash
# نسخ ملف الإعدادات
cp config/config.yaml.example config/config.yaml

# نسخ متغيرات البيئة
cp .env.example .env

# تعديل الإعدادات
nano config/config.yaml
nano .env
```

### التثبيت باستخدام Docker

```bash
# بناء وتشغيل الحاويات
docker-compose up --build -d

# مراقبة السجلات
docker-compose logs -f
```

## ⚙️ الإعداد

### 1. إعداد بوت التليجرام

1. **إنشاء بوت جديد**:
   - تحدث مع [@BotFather](https://t.me/botfather) في التليجرام
   - أرسل `/newbot` واتبع التعليمات
   - احفظ التوكن المُعطى

2. **إعداد القنوات**:
   - أنشئ قناة أو مجموعة في التليجرام
   - أضف البوت كمشرف
   - احصل على معرف القناة

### 2. تعديل ملف الإعدادات

```yaml
# config/config.yaml
telegram:
  bot_token: "YOUR_BOT_TOKEN_HERE"
  channels:
    - id: "@your_channel"
      name: "قناة العروض الرئيسية"
      active: true

database:
  host: "localhost"
  username: "amazon_bot"
  password: "your_password"
  database: "amazon_deals_bot"

scraping:
  categories:
    - "electronics"
    - "computers"
    - "mobile-phones"
  
deals:
  min_discount_percentage: 20
  min_original_price: 100
```

### 3. تعديل متغيرات البيئة

```bash
# .env
TELEGRAM_BOT_TOKEN=your_bot_token_here
DB_PASSWORD=your_database_password
ADMIN_CHAT_ID=your_admin_chat_id
```

## 🎮 الاستخدام

### تشغيل النظام

```bash
# التشغيل العادي
python run.py start

# التشغيل مع Docker
docker-compose up -d

# التشغيل السريع
./quick_start.sh start
```

### أوامر التحكم

```bash
# عرض الحالة
python run.py status

# تشغيل الاختبارات
python run.py test

# إيقاف النظام
python run.py stop
```

### أوامر البوت في التليجرام

- `/start` - بدء التفاعل مع البوت
- `/help` - عرض المساعدة
- `/subscribe` - الاشتراك في العروض
- `/unsubscribe` - إلغاء الاشتراك
- `/settings` - إعدادات المستخدم
- `/stats` - إحصائيات العروض

### إدارة النظام

```bash
# مراقبة السجلات
tail -f logs/amazon_bot.log

# فحص قاعدة البيانات
mysql -u amazon_bot -p amazon_deals_bot

# إعادة تشغيل الخدمة
systemctl restart amazon-deals-bot
```

## 🏗️ الهيكل التقني

### معمارية النظام

```
Amazon Deals Bot
├── 🔍 محرك البحث (Scraping Engine)
│   ├── استخراج البيانات من أمازون
│   ├── تحليل HTML والمحتوى
│   └── إدارة الطلبات والجلسات
│
├── 🧠 محلل العروض (Deal Analyzer)
│   ├── تقييم جودة العروض
│   ├── حساب نقاط الجودة
│   └── فلترة العروض المكررة
│
├── 🤖 بوت التليجرام (Telegram Bot)
│   ├── إدارة الرسائل والقنوات
│   ├── تنسيق وإرسال العروض
│   └── التفاعل مع المستخدمين
│
├── 📊 قاعدة البيانات (Database)
│   ├── تخزين المنتجات والعروض
│   ├── إدارة المستخدمين والقنوات
│   └── سجلات النشاط والإحصائيات
│
└── ⚙️ نظام الإدارة (Management System)
    ├── جدولة المهام
    ├── مراقبة الأداء
    └── إدارة الأخطاء
```

### قاعدة البيانات

```sql
-- الجداول الرئيسية
products          -- المنتجات
deals             -- العروض
price_history     -- تاريخ الأسعار
telegram_users    -- مستخدمي التليجرام
telegram_channels -- قنوات التليجرام
sent_messages     -- الرسائل المرسلة
activity_log      -- سجل النشاطات
system_stats      -- إحصائيات النظام
```

### ملفات المشروع

```
amazon_deals_bot/
├── 📁 src/                    # الكود المصدري
│   ├── main.py               # الملف الرئيسي
│   ├── deals_engine.py       # محرك العروض
│   ├── scraper.py            # مستخرج البيانات
│   ├── deal_analyzer.py      # محلل العروض
│   ├── telegram_bot.py       # بوت التليجرام
│   ├── channel_manager.py    # مدير القنوات
│   └── database.py           # مدير قاعدة البيانات
│
├── 📁 config/                 # ملفات الإعداد
│   ├── config.yaml           # الإعدادات الرئيسية
│   └── config.yaml.example   # مثال الإعدادات
│
├── 📁 tests/                  # الاختبارات
│   └── test_system.py        # اختبارات شاملة
│
├── 📁 logs/                   # ملفات السجلات
├── 📁 data/                   # البيانات المحلية
├── 📁 docs/                   # التوثيق
│
├── requirements.txt           # متطلبات Python
├── Dockerfile                # ملف Docker
├── docker-compose.yml        # إعداد Docker Compose
├── setup_database.sql        # إعداد قاعدة البيانات
├── run.py                    # ملف التشغيل
├── quick_start.sh            # التشغيل السريع
├── .env.example              # مثال متغيرات البيئة
└── README.md                 # هذا الملف
```

## 🔧 الصيانة

### المهام اليومية

```bash
# فحص حالة النظام
./quick_start.sh status

# مراجعة السجلات
tail -f logs/amazon_bot.log

# فحص قاعدة البيانات
mysql -u amazon_bot -p -e "SELECT COUNT(*) FROM deals WHERE DATE(created_at) = CURDATE();"
```

### المهام الأسبوعية

```bash
# تنظيف السجلات القديمة
find logs/ -name "*.log" -mtime +7 -delete

# تحديث الإحصائيات
python -c "from src.database import DatabaseManager; db = DatabaseManager(); db.update_weekly_stats()"

# نسخ احتياطي لقاعدة البيانات
mysqldump -u amazon_bot -p amazon_deals_bot > backup_$(date +%Y%m%d).sql
```

### المهام الشهرية

```bash
# تحديث المتطلبات
pip install --upgrade -r requirements.txt

# تنظيف البيانات القديمة
python -c "from src.deals_engine import DealsEngine; engine = DealsEngine(); engine.cleanup_old_data(days=30)"

# مراجعة الأداء
python -c "from src.database import DatabaseManager; db = DatabaseManager(); print(db.get_performance_stats())"
```

### مراقبة الأداء

#### مؤشرات الأداء الرئيسية (KPIs)

- **معدل اكتشاف العروض**: عدد العروض المكتشفة يومياً
- **جودة العروض**: متوسط نقاط الجودة للعروض المنشورة
- **معدل الاستجابة**: سرعة استجابة النظام
- **معدل الأخطاء**: نسبة الأخطاء في العمليات

#### أدوات المراقبة

```bash
# مراقبة استخدام الموارد
htop

# مراقبة قاعدة البيانات
mysql -u amazon_bot -p -e "SHOW PROCESSLIST;"

# مراقبة الشبكة
netstat -tulpn | grep python

# مراقبة المساحة
df -h
```

## 🐛 استكشاف الأخطاء

### المشاكل الشائعة

#### 1. خطأ في الاتصال بقاعدة البيانات

```bash
# فحص حالة MySQL
systemctl status mysql

# فحص الاتصال
mysql -u amazon_bot -p -e "SELECT 1;"

# إعادة تشغيل MySQL
sudo systemctl restart mysql
```

#### 2. خطأ في بوت التليجرام

```bash
# فحص التوكن
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"

# فحص الشبكة
ping api.telegram.org

# مراجعة السجلات
grep "telegram" logs/amazon_bot.log
```

#### 3. مشاكل في استخراج البيانات

```bash
# فحص الوصول لأمازون
curl -I https://www.amazon.sa

# فحص User-Agent
grep "user_agent" config/config.yaml

# تشغيل اختبار الاستخراج
python -c "from src.scraper import AmazonScraper; scraper = AmazonScraper(); print(scraper.test_connection())"
```

### رسائل الخطأ الشائعة

| رسالة الخطأ | السبب المحتمل | الحل |
|-------------|---------------|------|
| `Connection refused` | قاعدة البيانات متوقفة | إعادة تشغيل MySQL |
| `Invalid bot token` | توكن البوت خاطئ | تحديث التوكن في الإعدادات |
| `Rate limit exceeded` | تجاوز حد الطلبات | زيادة التأخير بين الطلبات |
| `Permission denied` | مشكلة في الصلاحيات | فحص صلاحيات الملفات |

### تشخيص متقدم

```bash
# تفعيل وضع التشخيص
export DEBUG_MODE=true
python run.py start

# تشغيل اختبارات شاملة
python -m pytest tests/ -v --tb=long

# فحص الذاكرة
python -c "
import psutil
process = psutil.Process()
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"
```

## 📈 التحسين والتطوير

### تحسين الأداء

#### 1. تحسين قاعدة البيانات

```sql
-- إضافة فهارس للاستعلامات السريعة
CREATE INDEX idx_deals_quality_date ON deals(quality_score DESC, created_at DESC);
CREATE INDEX idx_products_category_rating ON products(category_id, rating DESC);

-- تحسين إعدادات MySQL
SET GLOBAL innodb_buffer_pool_size = 1073741824; -- 1GB
SET GLOBAL query_cache_size = 268435456; -- 256MB
```

#### 2. تحسين الاستخراج

```python
# استخدام connection pooling
session = requests.Session()
adapter = HTTPAdapter(pool_connections=10, pool_maxsize=20)
session.mount('https://', adapter)

# تحسين التوازي
import asyncio
import aiohttp

async def scrape_concurrent(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [scrape_url(session, url) for url in urls]
        return await asyncio.gather(*tasks)
```

#### 3. تحسين الذاكرة

```python
# استخدام generators بدلاً من lists
def get_products():
    for product in database.get_products_iterator():
        yield process_product(product)

# تنظيف الذاكرة
import gc
gc.collect()
```

### إضافة مميزات جديدة

#### 1. دعم مواقع إضافية

```python
# src/scrapers/noon_scraper.py
class NoonScraper(BaseScraper):
    def __init__(self):
        self.base_url = "https://www.noon.com"
    
    def scrape_products(self, category):
        # تنفيذ استخراج من نون
        pass
```

#### 2. تحليل متقدم للعروض

```python
# src/analyzers/ml_analyzer.py
from sklearn.ensemble import RandomForestClassifier

class MLDealAnalyzer:
    def __init__(self):
        self.model = RandomForestClassifier()
    
    def predict_deal_quality(self, features):
        return self.model.predict([features])[0]
```

#### 3. واجهة ويب للإدارة

```python
# src/web/admin_panel.py
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/dashboard')
def dashboard():
    stats = get_system_stats()
    return render_template('dashboard.html', stats=stats)
```

## 🤝 المساهمة

نرحب بمساهماتكم في تطوير المشروع!

### كيفية المساهمة

1. **Fork المشروع**
2. **إنشاء branch جديد** (`git checkout -b feature/amazing-feature`)
3. **Commit التغييرات** (`git commit -m 'Add amazing feature'`)
4. **Push للـ branch** (`git push origin feature/amazing-feature`)
5. **فتح Pull Request**

### إرشادات المساهمة

- اتبع معايير PEP 8 لكتابة Python
- أضف اختبارات للمميزات الجديدة
- حدث التوثيق عند الحاجة
- استخدم رسائل commit واضحة

### الإبلاغ عن المشاكل

- استخدم [GitHub Issues](https://github.com/your-repo/amazon-deals-bot/issues)
- قدم وصفاً مفصلاً للمشكلة
- أرفق السجلات ذات الصلة
- حدد خطوات إعادة إنتاج المشكلة

## 📄 الترخيص

هذا المشروع مرخص تحت رخصة MIT - راجع ملف [LICENSE](LICENSE) للتفاصيل.

## 🙏 شكر وتقدير

- **Python Community** - للأدوات والمكتبات الرائعة
- **Telegram** - لتوفير API مجاني وقوي
- **MySQL** - لقاعدة البيانات الموثوقة
- **Docker** - لتسهيل النشر والتوزيع

## 📞 الدعم والتواصل

- **البريد الإلكتروني**: support@amazon-deals-bot.com
- **التليجرام**: [@AmazonDealsSupport](https://t.me/AmazonDealsSupport)
- **GitHub Issues**: [رابط المشاكل](https://github.com/your-repo/amazon-deals-bot/issues)
- **التوثيق**: [رابط التوثيق](https://docs.amazon-deals-bot.com)

---

<div align="center">

**صُنع بـ ❤️ في السعودية**

[⬆️ العودة للأعلى](#amazon-deals-bot-)

</div>

