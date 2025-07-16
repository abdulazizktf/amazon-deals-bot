"""
محرك العروض الرئيسي - يربط بين جميع مكونات النظام
تاريخ الإنشاء: 11 يوليو 2025
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import yaml
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from database import DatabaseManager
from scraper import AmazonScraper
from deal_analyzer import DealAnalyzer

class DealsEngine:
    """محرك العروض الرئيسي"""
    
    def __init__(self, config_path: str = 'config/config.yaml'):
        """
        تهيئة محرك العروض
        
        Args:
            config_path: مسار ملف الإعدادات
        """
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        
        # تهيئة المكونات
        self.db_manager = None
        self.scraper = None
        self.analyzer = None
        
        # إحصائيات التشغيل
        self.stats = {
            'products_scraped': 0,
            'deals_found': 0,
            'deals_processed': 0,
            'errors_count': 0,
            'last_run': None,
            'start_time': datetime.now()
        }
        
        # حالة التشغيل
        self.is_running = False
        self.should_stop = False
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """تحميل ملف الإعدادات"""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            return config
        except Exception as e:
            print(f"خطأ في تحميل الإعدادات: {e}")
            raise
    
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
        logger = logging.getLogger('deals_engine')
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
            self.logger.info("بدء تهيئة محرك العروض...")
            
            # تهيئة قاعدة البيانات
            self.db_manager = DatabaseManager(self.config)
            self.logger.info("تم تهيئة قاعدة البيانات")
            
            # تهيئة المستخرج
            self.scraper = AmazonScraper(self.config)
            self.logger.info("تم تهيئة مستخرج البيانات")
            
            # تهيئة المحلل
            self.analyzer = DealAnalyzer(self.config, self.db_manager)
            self.logger.info("تم تهيئة محلل العروض")
            
            # تسجيل بداية التشغيل
            self.db_manager.log_activity(
                'system', 
                'تم تهيئة محرك العروض بنجاح',
                severity='info'
            )
            
            self.logger.info("تم تهيئة محرك العروض بنجاح")
            
        except Exception as e:
            self.logger.error(f"خطأ في تهيئة محرك العروض: {e}")
            raise
    
    async def start_continuous_monitoring(self):
        """بدء المراقبة المستمرة للعروض"""
        self.is_running = True
        self.should_stop = False
        
        self.logger.info("بدء المراقبة المستمرة للعروض")
        
        try:
            while not self.should_stop:
                # تشغيل دورة استخراج العروض
                await self.run_deals_extraction_cycle()
                
                # انتظار الفترة المحددة
                interval = self._get_scraping_interval()
                self.logger.info(f"انتظار {interval} ثانية قبل الدورة التالية")
                
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            self.logger.info("تم إيقاف المراقبة بواسطة المستخدم")
        except Exception as e:
            self.logger.error(f"خطأ في المراقبة المستمرة: {e}")
        finally:
            self.is_running = False
            await self.cleanup()
    
    def _get_scraping_interval(self) -> int:
        """الحصول على فترة الاستخراج حسب الوقت"""
        current_hour = datetime.now().hour
        peak_hours = self.config['scheduling']['peak_hours']
        
        # فحص إذا كنا في ساعات الذروة
        if peak_hours['start'] <= current_hour <= peak_hours['end']:
            return peak_hours['interval']
        else:
            return self.config['scheduling']['scraping_interval']
    
    async def run_deals_extraction_cycle(self):
        """تشغيل دورة استخراج العروض"""
        cycle_start = datetime.now()
        self.logger.info("بدء دورة استخراج العروض")
        
        try:
            # إعادة تعيين إحصائيات الدورة
            cycle_stats = {
                'products_scraped': 0,
                'deals_found': 0,
                'deals_processed': 0,
                'errors': 0
            }
            
            # الحصول على قائمة المصطلحات للبحث
            search_terms = self._get_search_terms()
            
            # استخراج البيانات بشكل متوازي
            all_products = []
            
            with ThreadPoolExecutor(max_workers=self.config['performance']['max_concurrent_scrapers']) as executor:
                # إرسال مهام البحث
                future_to_term = {
                    executor.submit(self._scrape_search_term, term): term 
                    for term in search_terms
                }
                
                # جمع النتائج
                for future in as_completed(future_to_term):
                    term = future_to_term[future]
                    try:
                        products = future.result()
                        all_products.extend(products)
                        cycle_stats['products_scraped'] += len(products)
                        self.logger.info(f"تم استخراج {len(products)} منتج من البحث: {term}")
                    except Exception as e:
                        cycle_stats['errors'] += 1
                        self.logger.error(f"خطأ في استخراج البحث {term}: {e}")
            
            # استخراج صفحة العروض الخاصة
            try:
                deals_page_products = self.scraper.scrape_deals_page()
                all_products.extend(deals_page_products)
                cycle_stats['products_scraped'] += len(deals_page_products)
                self.logger.info(f"تم استخراج {len(deals_page_products)} منتج من صفحة العروض")
            except Exception as e:
                cycle_stats['errors'] += 1
                self.logger.error(f"خطأ في استخراج صفحة العروض: {e}")
            
            # معالجة المنتجات المستخرجة
            if all_products:
                processed_deals = await self._process_extracted_products(all_products)
                cycle_stats['deals_found'] = len(processed_deals)
                cycle_stats['deals_processed'] = len(processed_deals)
            
            # تحديث الإحصائيات العامة
            self.stats['products_scraped'] += cycle_stats['products_scraped']
            self.stats['deals_found'] += cycle_stats['deals_found']
            self.stats['deals_processed'] += cycle_stats['deals_processed']
            self.stats['errors_count'] += cycle_stats['errors']
            self.stats['last_run'] = cycle_start
            
            # حفظ إحصائيات الأداء
            await self._save_performance_stats(cycle_stats)
            
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            self.logger.info(
                f"انتهت دورة الاستخراج - "
                f"المنتجات: {cycle_stats['products_scraped']}, "
                f"العروض: {cycle_stats['deals_found']}, "
                f"الأخطاء: {cycle_stats['errors']}, "
                f"المدة: {cycle_duration:.1f}s"
            )
            
        except Exception as e:
            self.logger.error(f"خطأ في دورة استخراج العروض: {e}")
            self.stats['errors_count'] += 1
    
    def _get_search_terms(self) -> List[str]:
        """الحصول على مصطلحات البحث"""
        # يمكن تحسين هذا لاحقاً لجلب المصطلحات من قاعدة البيانات
        categories = self.config['deals']['categories']
        search_terms = []
        
        # إضافة مصطلحات البحث الأساسية
        base_terms = [
            "deals", "offers", "discount", "sale",
            "عروض", "خصومات", "تخفيضات"
        ]
        
        # دمج الفئات مع المصطلحات
        for category in categories:
            for term in base_terms:
                search_terms.append(f"{category} {term}")
        
        # إضافة مصطلحات إضافية
        additional_terms = [
            "lightning deals",
            "daily deals", 
            "clearance",
            "best sellers discount"
        ]
        search_terms.extend(additional_terms)
        
        return search_terms[:20]  # تحديد العدد لتجنب الحمل الزائد
    
    def _scrape_search_term(self, search_term: str) -> List[Dict[str, Any]]:
        """استخراج منتجات مصطلح بحث محدد"""
        try:
            products = self.scraper.search_products(search_term, page=1)
            
            # يمكن إضافة صفحات إضافية للبحث المهم
            if len(products) >= 15 and search_term in ["deals", "offers"]:
                page2_products = self.scraper.search_products(search_term, page=2)
                products.extend(page2_products)
            
            return products
            
        except Exception as e:
            self.logger.error(f"خطأ في استخراج مصطلح البحث {search_term}: {e}")
            return []
    
    async def _process_extracted_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """معالجة المنتجات المستخرجة واكتشاف العروض"""
        processed_deals = []
        
        self.logger.info(f"بدء معالجة {len(products)} منتج")
        
        for product in products:
            try:
                # تحليل المنتج للعروض
                deal_info = self.analyzer.analyze_product_for_deals(product)
                
                if deal_info:
                    # حفظ المنتج في قاعدة البيانات
                    product_id = await self._save_product(product)
                    
                    if product_id:
                        # ربط العرض بالمنتج
                        deal_info['product_id'] = product_id
                        
                        # حفظ العرض
                        deal_id = await self._save_deal(deal_info)
                        
                        if deal_id:
                            deal_info['id'] = deal_id
                            deal_info.update(product)  # إضافة بيانات المنتج
                            processed_deals.append(deal_info)
                            
                            self.logger.debug(f"تم اكتشاف عرض جديد: {product.get('title', 'Unknown')}")
                
                # حفظ سجل السعر حتى لو لم يكن هناك عرض
                if product.get('current_price'):
                    await self._save_price_history(product, product_id if 'product_id' in locals() else None)
                
            except Exception as e:
                self.logger.error(f"خطأ في معالجة المنتج: {e}")
                continue
        
        # فلترة العروض المكررة وترتيبها
        if processed_deals:
            processed_deals = self.analyzer.filter_duplicate_deals(processed_deals)
            processed_deals = self.analyzer.compare_deals(processed_deals)
        
        self.logger.info(f"تم معالجة {len(processed_deals)} عرض جديد")
        return processed_deals
    
    async def _save_product(self, product_data: Dict[str, Any]) -> Optional[int]:
        """حفظ المنتج في قاعدة البيانات"""
        try:
            # تحضير بيانات المنتج
            product_record = {
                'asin': product_data.get('asin'),
                'title': product_data.get('title', '')[:500],  # تحديد الطول
                'title_ar': None,  # يمكن إضافة ترجمة لاحقاً
                'description': product_data.get('description', '')[:1000] if product_data.get('description') else None,
                'brand': product_data.get('brand', '')[:255] if product_data.get('brand') else None,
                'category_id': None,  # يمكن تحديده لاحقاً
                'image_url': product_data.get('image_url', '')[:500] if product_data.get('image_url') else None,
                'amazon_url': product_data.get('amazon_url', '')[:500],
                'rating': product_data.get('rating'),
                'review_count': product_data.get('review_count', 0)
            }
            
            product_id = self.db_manager.insert_product(product_record)
            return product_id
            
        except Exception as e:
            self.logger.error(f"خطأ في حفظ المنتج: {e}")
            return None
    
    async def _save_deal(self, deal_info: Dict[str, Any]) -> Optional[int]:
        """حفظ العرض في قاعدة البيانات"""
        try:
            deal_record = {
                'product_id': deal_info['product_id'],
                'deal_type': deal_info['deal_type'],
                'original_price': deal_info['original_price'],
                'deal_price': deal_info['deal_price'],
                'discount_percentage': deal_info['discount_percentage'],
                'discount_amount': deal_info['discount_amount'],
                'start_date': deal_info['start_date'],
                'end_date': deal_info.get('end_date'),
                'deal_status': deal_info['deal_status'],
                'max_quantity': None,
                'deal_url': deal_info.get('deal_url', '')[:500] if deal_info.get('deal_url') else None,
                'quality_score': deal_info['quality_score']
            }
            
            deal_id = self.db_manager.insert_deal(deal_record)
            
            # تسجيل اكتشاف العرض
            if deal_id:
                self.db_manager.log_activity(
                    'deal_found',
                    f"تم اكتشاف عرض جديد - خصم {deal_info['discount_percentage']}%",
                    'deals',
                    deal_id,
                    {
                        'asin': deal_info.get('asin'),
                        'quality_score': deal_info['quality_score'],
                        'deal_type': deal_info['deal_type']
                    }
                )
            
            return deal_id
            
        except Exception as e:
            self.logger.error(f"خطأ في حفظ العرض: {e}")
            return None
    
    async def _save_price_history(self, product_data: Dict[str, Any], product_id: Optional[int]):
        """حفظ سجل السعر"""
        if not product_id or not product_data.get('current_price'):
            return
        
        try:
            price_record = {
                'product_id': product_id,
                'price': product_data['current_price'],
                'currency': product_data.get('currency', 'SAR'),
                'availability_status': product_data.get('availability', 'unknown'),
                'seller_name': product_data.get('seller_name', '')[:255] if product_data.get('seller_name') else None,
                'is_prime': product_data.get('is_prime', False)
            }
            
            self.db_manager.insert_price_history(price_record)
            
        except Exception as e:
            self.logger.error(f"خطأ في حفظ سجل السعر: {e}")
    
    async def _save_performance_stats(self, cycle_stats: Dict[str, int]):
        """حفظ إحصائيات الأداء"""
        try:
            # يمكن إضافة حفظ الإحصائيات في قاعدة البيانات
            self.logger.debug(f"إحصائيات الدورة: {cycle_stats}")
        except Exception as e:
            self.logger.error(f"خطأ في حفظ إحصائيات الأداء: {e}")
    
    async def get_active_deals(self, limit: int = 50) -> List[Dict[str, Any]]:
        """الحصول على العروض النشطة"""
        try:
            deals = self.db_manager.get_active_deals(limit)
            
            # إضافة ملخصات للعروض
            for deal in deals:
                summary = self.analyzer.generate_deal_summary(deal)
                deal['summary'] = summary
            
            return deals
            
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على العروض النشطة: {e}")
            return []
    
    async def cleanup_old_data(self):
        """تنظيف البيانات القديمة"""
        try:
            self.logger.info("بدء تنظيف البيانات القديمة")
            self.db_manager.cleanup_old_data(days=30)
            self.logger.info("تم تنظيف البيانات القديمة")
        except Exception as e:
            self.logger.error(f"خطأ في تنظيف البيانات: {e}")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات النظام"""
        try:
            db_stats = self.db_manager.get_performance_stats()
            
            runtime = datetime.now() - self.stats['start_time']
            
            system_stats = {
                'runtime_hours': runtime.total_seconds() / 3600,
                'is_running': self.is_running,
                'last_run': self.stats['last_run'],
                'session_stats': self.stats.copy(),
                'database_stats': db_stats
            }
            
            return system_stats
            
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على إحصائيات النظام: {e}")
            return {}
    
    async def stop(self):
        """إيقاف محرك العروض"""
        self.logger.info("بدء إيقاف محرك العروض...")
        self.should_stop = True
        
        # انتظار انتهاء العمليات الجارية
        timeout = 30  # ثانية
        start_time = time.time()
        
        while self.is_running and (time.time() - start_time) < timeout:
            await asyncio.sleep(1)
        
        if self.is_running:
            self.logger.warning("تم إجبار إيقاف محرك العروض")
        
        await self.cleanup()
    
    async def cleanup(self):
        """تنظيف الموارد"""
        try:
            if self.scraper:
                self.scraper.close()
            
            if self.db_manager:
                self.db_manager.close()
            
            self.logger.info("تم تنظيف موارد محرك العروض")
            
        except Exception as e:
            self.logger.error(f"خطأ في تنظيف الموارد: {e}")

# دالة مساعدة لتشغيل المحرك
async def main():
    """الدالة الرئيسية لتشغيل محرك العروض"""
    engine = DealsEngine()
    
    try:
        await engine.initialize()
        await engine.start_continuous_monitoring()
    except KeyboardInterrupt:
        print("\nتم إيقاف النظام بواسطة المستخدم")
    except Exception as e:
        print(f"خطأ في تشغيل النظام: {e}")
    finally:
        await engine.stop()

if __name__ == "__main__":
    asyncio.run(main())

