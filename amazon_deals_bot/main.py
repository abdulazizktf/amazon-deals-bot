"""
الملف الرئيسي لنظام Amazon Deals Bot
يربط جميع المكونات ويدير الجدولة التلقائية
تاريخ الإنشاء: 11 يوليو 2025
"""

import asyncio
import logging
import signal
import sys
import os
from datetime import datetime
import yaml
from typing import Dict, Any

# إضافة مجلد src إلى المسار
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from deals_engine import DealsEngine
from telegram_bot import TelegramBot
from channel_manager import ChannelManager
from database import DatabaseManager

class AmazonDealsBot:
    """النظام الرئيسي لبوت عروض أمازون"""
    
    def __init__(self, config_path: str = 'config/config.yaml'):
        """
        تهيئة النظام الرئيسي
        
        Args:
            config_path: مسار ملف الإعدادات
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.logger = self._setup_logging()
        
        # المكونات الرئيسية
        self.db_manager = None
        self.deals_engine = None
        self.telegram_bot = None
        self.channel_manager = None
        
        # حالة النظام
        self.is_running = False
        self.should_stop = False
        
        # مهام الجدولة
        self.scheduled_tasks = []
        
    def _load_config(self) -> Dict[str, Any]:
        """تحميل ملف الإعدادات"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"خطأ في تحميل الإعدادات: {e}")
            sys.exit(1)
    
    def _setup_logging(self) -> logging.Logger:
        """إعداد نظام السجلات"""
        logging_config = self.config['logging']
        
        # إنشاء مجلد السجلات
        os.makedirs('logs', exist_ok=True)
        
        # إعداد التنسيق
        formatter = logging.Formatter(
            fmt=logging_config['format'],
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # إعداد logger الرئيسي
        logger = logging.getLogger('amazon_deals_bot')
        logger.setLevel(getattr(logging, logging_config['level']))
        
        # إضافة handler للملف الرئيسي
        main_handler = logging.FileHandler(
            logging_config['files']['main'], 
            encoding='utf-8'
        )
        main_handler.setFormatter(formatter)
        logger.addHandler(main_handler)
        
        # إضافة handler للكونسول
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    async def initialize(self):
        """تهيئة جميع مكونات النظام"""
        try:
            self.logger.info("🚀 بدء تهيئة نظام Amazon Deals Bot...")
            
            # تهيئة قاعدة البيانات
            self.logger.info("📊 تهيئة قاعدة البيانات...")
            self.db_manager = DatabaseManager(self.config)
            
            # تهيئة محرك العروض
            self.logger.info("🔍 تهيئة محرك العروض...")
            self.deals_engine = DealsEngine(self.config_path)
            await self.deals_engine.initialize()
            
            # تهيئة مدير القنوات
            self.logger.info("📱 تهيئة مدير القنوات...")
            self.channel_manager = ChannelManager(self.db_manager)
            
            # تهيئة بوت التليجرام
            self.logger.info("🤖 تهيئة بوت التليجرام...")
            self.telegram_bot = TelegramBot(self.config, self.db_manager, self.deals_engine)
            await self.telegram_bot.initialize()
            
            self.logger.info("✅ تم تهيئة جميع مكونات النظام بنجاح")
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في تهيئة النظام: {e}")
            raise
    
    async def start(self):
        """بدء تشغيل النظام"""
        try:
            self.is_running = True
            self.should_stop = False
            
            self.logger.info("🎯 بدء تشغيل نظام Amazon Deals Bot")
            
            # إعداد معالجات الإشارات
            self._setup_signal_handlers()
            
            # بدء المهام المتوازية
            tasks = [
                asyncio.create_task(self._run_deals_monitoring(), name="deals_monitoring"),
                asyncio.create_task(self._run_telegram_bot(), name="telegram_bot"),
                asyncio.create_task(self._run_scheduled_tasks(), name="scheduled_tasks"),
                asyncio.create_task(self._run_system_monitoring(), name="system_monitoring")
            ]
            
            self.scheduled_tasks = tasks
            
            # انتظار المهام
            try:
                await asyncio.gather(*tasks)
            except asyncio.CancelledError:
                self.logger.info("تم إلغاء المهام")
            
        except Exception as e:
            self.logger.error(f"خطأ في تشغيل النظام: {e}")
        finally:
            await self.cleanup()
    
    def _setup_signal_handlers(self):
        """إعداد معالجات إشارات النظام"""
        def signal_handler(signum, frame):
            self.logger.info(f"تم استلام إشارة الإيقاف: {signum}")
            self.should_stop = True
            
            # إلغاء المهام
            for task in self.scheduled_tasks:
                if not task.done():
                    task.cancel()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _run_deals_monitoring(self):
        """تشغيل مراقبة العروض"""
        self.logger.info("🔍 بدء مراقبة العروض...")
        
        try:
            while not self.should_stop:
                # تشغيل دورة استخراج العروض
                await self.deals_engine.run_deals_extraction_cycle()
                
                # الحصول على العروض الجديدة
                new_deals = await self.deals_engine.get_active_deals(limit=20)
                
                if new_deals:
                    self.logger.info(f"🎯 تم العثور على {len(new_deals)} عرض جديد")
                    
                    # إرسال العروض عبر التليجرام
                    await self._broadcast_new_deals(new_deals)
                
                # انتظار الفترة المحددة
                interval = self._get_monitoring_interval()
                self.logger.debug(f"انتظار {interval} ثانية قبل الدورة التالية")
                
                await asyncio.sleep(interval)
                
        except asyncio.CancelledError:
            self.logger.info("تم إيقاف مراقبة العروض")
        except Exception as e:
            self.logger.error(f"خطأ في مراقبة العروض: {e}")
    
    async def _run_telegram_bot(self):
        """تشغيل بوت التليجرام"""
        self.logger.info("🤖 بدء تشغيل بوت التليجرام...")
        
        try:
            await self.telegram_bot.start_bot()
        except asyncio.CancelledError:
            self.logger.info("تم إيقاف بوت التليجرام")
        except Exception as e:
            self.logger.error(f"خطأ في تشغيل بوت التليجرام: {e}")
    
    async def _run_scheduled_tasks(self):
        """تشغيل المهام المجدولة"""
        self.logger.info("⏰ بدء المهام المجدولة...")
        
        try:
            while not self.should_stop:
                current_time = datetime.now()
                
                # تنظيف البيانات القديمة (يومياً في الساعة 2 صباحاً)
                if current_time.hour == 2 and current_time.minute == 0:
                    await self._run_daily_cleanup()
                
                # إرسال تقرير يومي (يومياً في الساعة 8 صباحاً)
                if current_time.hour == 8 and current_time.minute == 0:
                    await self._send_daily_report()
                
                # تحديث إحصائيات النظام (كل ساعة)
                if current_time.minute == 0:
                    await self._update_system_stats()
                
                # انتظار دقيقة واحدة
                await asyncio.sleep(60)
                
        except asyncio.CancelledError:
            self.logger.info("تم إيقاف المهام المجدولة")
        except Exception as e:
            self.logger.error(f"خطأ في المهام المجدولة: {e}")
    
    async def _run_system_monitoring(self):
        """مراقبة حالة النظام"""
        self.logger.info("📊 بدء مراقبة النظام...")
        
        try:
            while not self.should_stop:
                # فحص حالة المكونات
                await self._check_system_health()
                
                # انتظار 5 دقائق
                await asyncio.sleep(300)
                
        except asyncio.CancelledError:
            self.logger.info("تم إيقاف مراقبة النظام")
        except Exception as e:
            self.logger.error(f"خطأ في مراقبة النظام: {e}")
    
    def _get_monitoring_interval(self) -> int:
        """الحصول على فترة المراقبة حسب الوقت"""
        current_hour = datetime.now().hour
        peak_hours = self.config['scheduling']['peak_hours']
        
        # فحص إذا كنا في ساعات الذروة
        if peak_hours['start'] <= current_hour <= peak_hours['end']:
            return peak_hours['interval']
        else:
            return self.config['scheduling']['scraping_interval']
    
    async def _broadcast_new_deals(self, deals: list):
        """بث العروض الجديدة"""
        try:
            # فلترة العروض عالية الجودة فقط
            quality_deals = [deal for deal in deals if deal.get('quality_score', 0) >= 6.0]
            
            if quality_deals:
                # إرسال العروض عبر التليجرام
                broadcast_stats = await self.telegram_bot.broadcast_deals(quality_deals)
                
                self.logger.info(
                    f"📤 تم بث {len(quality_deals)} عرض - "
                    f"القنوات: {broadcast_stats['channels_sent']}, "
                    f"الرسائل: {broadcast_stats['messages_sent']}"
                )
                
                # تسجيل النشاط
                self.db_manager.log_activity(
                    'deals_broadcast',
                    f"تم بث {len(quality_deals)} عرض عبر {broadcast_stats['channels_sent']} قناة",
                    metadata={
                        'deals_count': len(quality_deals),
                        'channels_sent': broadcast_stats['channels_sent'],
                        'messages_sent': broadcast_stats['messages_sent']
                    }
                )
        
        except Exception as e:
            self.logger.error(f"خطأ في بث العروض: {e}")
    
    async def _run_daily_cleanup(self):
        """تشغيل تنظيف البيانات اليومي"""
        try:
            self.logger.info("🧹 بدء التنظيف اليومي...")
            
            # تنظيف البيانات القديمة
            await self.deals_engine.cleanup_old_data()
            
            # تنظيف المستخدمين غير النشطين
            inactive_users = await self.channel_manager.cleanup_inactive_users(days=30)
            
            self.logger.info(f"✅ انتهى التنظيف اليومي - تم تعطيل {inactive_users} مستخدم غير نشط")
            
        except Exception as e:
            self.logger.error(f"خطأ في التنظيف اليومي: {e}")
    
    async def _send_daily_report(self):
        """إرسال التقرير اليومي"""
        try:
            self.logger.info("📊 إعداد التقرير اليومي...")
            
            # الحصول على الإحصائيات
            system_stats = self.deals_engine.get_system_stats()
            channel_stats = await self.channel_manager.get_channel_stats()
            bot_stats = self.telegram_bot.get_stats()
            
            # إعداد التقرير
            report = f"""
📊 **التقرير اليومي - {datetime.now().strftime('%Y-%m-%d')}**

🔍 **محرك العروض:**
• المنتجات المفحوصة: {system_stats.get('session_stats', {}).get('products_scraped', 0):,}
• العروض المكتشفة: {system_stats.get('session_stats', {}).get('deals_found', 0):,}
• العروض النشطة: {system_stats.get('database_stats', {}).get('active_deals', 0):,}

🤖 **بوت التليجرام:**
• الرسائل المرسلة: {bot_stats['messages_sent']:,}
• المستخدمين النشطين: {channel_stats.get('active_users', 0):,}
• القنوات النشطة: {channel_stats.get('active_channels', 0):,}

⏱️ **وقت التشغيل:** {system_stats.get('runtime_hours', 0):.1f} ساعة
            """
            
            # يمكن إرسال التقرير لقناة إدارية محددة
            self.logger.info("📊 تم إعداد التقرير اليومي")
            
        except Exception as e:
            self.logger.error(f"خطأ في إعداد التقرير اليومي: {e}")
    
    async def _update_system_stats(self):
        """تحديث إحصائيات النظام"""
        try:
            # تحديث الإحصائيات في قاعدة البيانات
            stats = self.deals_engine.get_system_stats()
            
            # تسجيل الإحصائيات
            self.db_manager.log_activity(
                'system_stats',
                'تحديث إحصائيات النظام',
                metadata=stats
            )
            
        except Exception as e:
            self.logger.error(f"خطأ في تحديث الإحصائيات: {e}")
    
    async def _check_system_health(self):
        """فحص صحة النظام"""
        try:
            health_status = {
                'database': 'healthy',
                'deals_engine': 'healthy',
                'telegram_bot': 'healthy',
                'timestamp': datetime.now().isoformat()
            }
            
            # فحص قاعدة البيانات
            try:
                self.db_manager.execute_query("SELECT 1", fetch=True)
            except Exception:
                health_status['database'] = 'unhealthy'
                self.logger.warning("⚠️ مشكلة في قاعدة البيانات")
            
            # فحص محرك العروض
            if not self.deals_engine.is_running:
                health_status['deals_engine'] = 'stopped'
                self.logger.warning("⚠️ محرك العروض متوقف")
            
            # تسجيل حالة النظام
            if all(status == 'healthy' for status in health_status.values() if status != health_status['timestamp']):
                self.logger.debug("✅ النظام يعمل بشكل طبيعي")
            else:
                self.logger.warning(f"⚠️ مشاكل في النظام: {health_status}")
                
                # تسجيل المشكلة
                self.db_manager.log_activity(
                    'system_health',
                    'مشاكل في صحة النظام',
                    metadata=health_status,
                    severity='warning'
                )
        
        except Exception as e:
            self.logger.error(f"خطأ في فحص صحة النظام: {e}")
    
    async def stop(self):
        """إيقاف النظام"""
        self.logger.info("🛑 بدء إيقاف النظام...")
        self.should_stop = True
        
        # إلغاء المهام
        for task in self.scheduled_tasks:
            if not task.done():
                task.cancel()
        
        # انتظار انتهاء المهام
        if self.scheduled_tasks:
            await asyncio.gather(*self.scheduled_tasks, return_exceptions=True)
        
        await self.cleanup()
    
    async def cleanup(self):
        """تنظيف الموارد"""
        try:
            self.logger.info("🧹 تنظيف موارد النظام...")
            
            # إيقاف بوت التليجرام
            if self.telegram_bot:
                await self.telegram_bot.stop_bot()
            
            # إيقاف محرك العروض
            if self.deals_engine:
                await self.deals_engine.stop()
            
            # إغلاق قاعدة البيانات
            if self.db_manager:
                self.db_manager.close()
            
            self.is_running = False
            self.logger.info("✅ تم تنظيف جميع الموارد")
            
        except Exception as e:
            self.logger.error(f"خطأ في تنظيف الموارد: {e}")

# دالة مساعدة لإنشاء قاعدة البيانات
async def setup_database():
    """إعداد قاعدة البيانات الأولي"""
    print("🔧 إعداد قاعدة البيانات...")
    
    # يمكن إضافة منطق إنشاء الجداول هنا
    # أو تشغيل ملف SQL منفصل
    
    print("✅ تم إعداد قاعدة البيانات")

# الدالة الرئيسية
async def main():
    """الدالة الرئيسية لتشغيل النظام"""
    print("🚀 بدء تشغيل Amazon Deals Bot")
    print("=" * 50)
    
    # فحص وجود ملف الإعدادات
    config_path = 'config/config.yaml'
    if not os.path.exists(config_path):
        print(f"❌ ملف الإعدادات غير موجود: {config_path}")
        print("يرجى إنشاء ملف الإعدادات أولاً")
        return
    
    # إنشاء النظام
    bot_system = AmazonDealsBot(config_path)
    
    try:
        # تهيئة النظام
        await bot_system.initialize()
        
        # بدء التشغيل
        await bot_system.start()
        
    except KeyboardInterrupt:
        print("\n⏹️ تم إيقاف النظام بواسطة المستخدم")
    except Exception as e:
        print(f"❌ خطأ في تشغيل النظام: {e}")
        logging.getLogger('amazon_deals_bot').error(f"خطأ في تشغيل النظام: {e}")
    finally:
        await bot_system.stop()
        print("👋 تم إيقاف النظام بنجاح")

if __name__ == "__main__":
    # تشغيل النظام
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 وداعاً!")
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")
        sys.exit(1)

