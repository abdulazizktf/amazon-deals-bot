#!/usr/bin/env python3
"""
ملف تشغيل نظام Amazon Deals Bot
يوفر واجهة سهلة لتشغيل وإدارة النظام
تاريخ الإنشاء: 11 يوليو 2025
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# إضافة مجلد src إلى المسار
sys.path.append(str(Path(__file__).parent / 'src'))

from main import AmazonDealsBot, setup_database

def print_banner():
    """طباعة شعار النظام"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    Amazon Deals Bot                          ║
║              نظام AI للبحث عن العروض التلقائي              ║
║                                                              ║
║  🔍 يبحث عن أفضل العروض من أمازون السعودية                ║
║  📱 ينشر العروض تلقائياً في قنوات التليجرام                ║
║  🤖 يستخدم الذكاء الاصطناعي لتحليل جودة العروض            ║
║                                                              ║
║                   تاريخ الإنشاء: 11 يوليو 2025              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_requirements():
    """فحص المتطلبات الأساسية"""
    print("🔍 فحص المتطلبات...")
    
    # فحص ملف الإعدادات
    config_path = Path('config/config.yaml')
    if not config_path.exists():
        print("❌ ملف الإعدادات غير موجود!")
        print(f"يرجى إنشاء الملف: {config_path}")
        print("يمكنك نسخ config/config.yaml.example وتعديله")
        return False
    
    # فحص المجلدات المطلوبة
    required_dirs = ['logs', 'data']
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            print(f"📁 إنشاء مجلد: {dir_name}")
            dir_path.mkdir(exist_ok=True)
    
    print("✅ تم فحص المتطلبات بنجاح")
    return True

async def run_setup():
    """إعداد النظام للمرة الأولى"""
    print("🔧 بدء إعداد النظام...")
    
    try:
        # إعداد قاعدة البيانات
        await setup_database()
        
        print("✅ تم إعداد النظام بنجاح!")
        print("يمكنك الآن تشغيل النظام باستخدام: python run.py start")
        
    except Exception as e:
        print(f"❌ خطأ في إعداد النظام: {e}")
        return False
    
    return True

async def start_bot():
    """تشغيل النظام"""
    print("🚀 بدء تشغيل Amazon Deals Bot...")
    
    if not check_requirements():
        return False
    
    try:
        # إنشاء وتشغيل النظام
        bot = AmazonDealsBot()
        await bot.initialize()
        await bot.start()
        
    except KeyboardInterrupt:
        print("\n⏹️ تم إيقاف النظام بواسطة المستخدم")
    except Exception as e:
        print(f"❌ خطأ في تشغيل النظام: {e}")
        return False
    
    return True

async def test_system():
    """اختبار النظام"""
    print("🧪 بدء اختبار النظام...")
    
    try:
        # إنشاء النظام في وضع الاختبار
        bot = AmazonDealsBot()
        await bot.initialize()
        
        # تشغيل اختبارات أساسية
        print("🔍 اختبار محرك العروض...")
        deals = await bot.deals_engine.get_active_deals(limit=5)
        print(f"✅ تم العثور على {len(deals)} عرض")
        
        print("🤖 اختبار بوت التليجرام...")
        bot_stats = bot.telegram_bot.get_stats()
        print(f"✅ إحصائيات البوت: {bot_stats}")
        
        print("📊 اختبار قاعدة البيانات...")
        system_stats = bot.deals_engine.get_system_stats()
        print(f"✅ إحصائيات النظام: {system_stats}")
        
        await bot.cleanup()
        print("✅ تم اختبار النظام بنجاح!")
        
    except Exception as e:
        print(f"❌ خطأ في اختبار النظام: {e}")
        return False
    
    return True

def show_status():
    """عرض حالة النظام"""
    print("📊 حالة النظام:")
    
    # فحص الملفات المطلوبة
    files_to_check = [
        'config/config.yaml',
        'src/main.py',
        'src/deals_engine.py',
        'src/telegram_bot.py'
    ]
    
    for file_path in files_to_check:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
    
    # فحص المجلدات
    dirs_to_check = ['logs', 'data', 'config', 'src']
    for dir_path in dirs_to_check:
        if Path(dir_path).exists():
            print(f"📁 {dir_path}/")
        else:
            print(f"❌ {dir_path}/")

def show_help():
    """عرض المساعدة"""
    help_text = """
🆘 دليل استخدام Amazon Deals Bot

الأوامر المتاحة:
  setup     - إعداد النظام للمرة الأولى
  start     - تشغيل النظام
  test      - اختبار النظام
  status    - عرض حالة النظام
  help      - عرض هذه المساعدة

أمثلة:
  python run.py setup    # إعداد النظام
  python run.py start    # تشغيل النظام
  python run.py test     # اختبار النظام

متطلبات التشغيل:
  - Python 3.8+
  - MySQL/MariaDB
  - ملف إعدادات صحيح في config/config.yaml
  - توكن بوت التليجرام

للمساعدة الإضافية، راجع ملف README.md
    """
    print(help_text)

async def main():
    """الدالة الرئيسية"""
    parser = argparse.ArgumentParser(
        description='Amazon Deals Bot - نظام AI للبحث عن العروض التلقائي',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'command',
        choices=['setup', 'start', 'test', 'status', 'help'],
        help='الأمر المطلوب تنفيذه'
    )
    
    parser.add_argument(
        '--config',
        default='config/config.yaml',
        help='مسار ملف الإعدادات'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='تفعيل وضع التشخيص'
    )
    
    args = parser.parse_args()
    
    # طباعة الشعار
    print_banner()
    
    # تنفيذ الأمر المطلوب
    if args.command == 'setup':
        success = await run_setup()
        sys.exit(0 if success else 1)
        
    elif args.command == 'start':
        success = await start_bot()
        sys.exit(0 if success else 1)
        
    elif args.command == 'test':
        success = await test_system()
        sys.exit(0 if success else 1)
        
    elif args.command == 'status':
        show_status()
        
    elif args.command == 'help':
        show_help()
        
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 تم إيقاف البرنامج")
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")
        sys.exit(1)

