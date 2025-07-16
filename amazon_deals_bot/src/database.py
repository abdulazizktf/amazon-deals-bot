"""
وحدة إدارة قاعدة البيانات لنظام Amazon Deals Bot
تاريخ الإنشاء: 11 يوليو 2025
"""

import mysql.connector
from mysql.connector import pooling, Error
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime, timedelta
import json

class DatabaseManager:
    """مدير قاعدة البيانات الرئيسي"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        تهيئة مدير قاعدة البيانات
        
        Args:
            config: إعدادات قاعدة البيانات
        """
        self.config = config['database']
        self.logger = logging.getLogger(__name__)
        self.connection_pool = None
        self.engine = None
        self.Session = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """تهيئة اتصال قاعدة البيانات"""
        try:
            # إنشاء connection pool
            pool_config = {
                'pool_name': 'amazon_bot_pool',
                'pool_size': self.config.get('pool_size', 10),
                'pool_reset_session': True,
                'host': self.config['host'],
                'port': self.config['port'],
                'user': self.config['username'],
                'password': self.config['password'],
                'database': self.config['database'],
                'charset': self.config.get('charset', 'utf8mb4'),
                'autocommit': False,
                'time_zone': '+03:00'  # توقيت السعودية
            }
            
            self.connection_pool = pooling.MySQLConnectionPool(**pool_config)
            
            # إنشاء SQLAlchemy engine
            db_url = (f"mysql+mysqlconnector://{self.config['username']}:"
                     f"{self.config['password']}@{self.config['host']}:"
                     f"{self.config['port']}/{self.config['database']}")
            
            self.engine = create_engine(
                db_url,
                pool_size=self.config.get('pool_size', 10),
                max_overflow=self.config.get('max_overflow', 20),
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            self.Session = sessionmaker(bind=self.engine)
            
            self.logger.info("تم تهيئة اتصال قاعدة البيانات بنجاح")
            
        except Error as e:
            self.logger.error(f"خطأ في تهيئة قاعدة البيانات: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """الحصول على اتصال من pool"""
        connection = None
        try:
            connection = self.connection_pool.get_connection()
            yield connection
        except Error as e:
            self.logger.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()
    
    @contextmanager
    def get_session(self):
        """الحصول على SQLAlchemy session"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"خطأ في جلسة قاعدة البيانات: {e}")
            raise
        finally:
            session.close()
    
    def execute_query(self, query: str, params: Optional[Tuple] = None, 
                     fetch: bool = False) -> Optional[List[Tuple]]:
        """
        تنفيذ استعلام SQL
        
        Args:
            query: الاستعلام
            params: المعاملات
            fetch: هل نريد استرجاع النتائج
            
        Returns:
            النتائج إذا كان fetch=True
        """
        with self.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, params or ())
                
                if fetch:
                    return cursor.fetchall()
                else:
                    connection.commit()
                    return cursor.rowcount
                    
            except Error as e:
                self.logger.error(f"خطأ في تنفيذ الاستعلام: {e}")
                connection.rollback()
                raise
            finally:
                cursor.close()
    
    def insert_product(self, product_data: Dict[str, Any]) -> int:
        """
        إدراج منتج جديد
        
        Args:
            product_data: بيانات المنتج
            
        Returns:
            معرف المنتج المدرج
        """
        query = """
        INSERT INTO products (asin, title, title_ar, description, brand, 
                            category_id, image_url, amazon_url, rating, review_count)
        VALUES (%(asin)s, %(title)s, %(title_ar)s, %(description)s, %(brand)s,
                %(category_id)s, %(image_url)s, %(amazon_url)s, %(rating)s, %(review_count)s)
        ON DUPLICATE KEY UPDATE
            title = VALUES(title),
            description = VALUES(description),
            brand = VALUES(brand),
            image_url = VALUES(image_url),
            rating = VALUES(rating),
            review_count = VALUES(review_count),
            last_updated = CURRENT_TIMESTAMP
        """
        
        with self.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, product_data)
                connection.commit()
                
                # الحصول على معرف المنتج
                if cursor.lastrowid:
                    return cursor.lastrowid
                else:
                    # المنتج موجود، نحصل على معرفه
                    cursor.execute("SELECT id FROM products WHERE asin = %s", 
                                 (product_data['asin'],))
                    result = cursor.fetchone()
                    return result[0] if result else None
                    
            except Error as e:
                self.logger.error(f"خطأ في إدراج المنتج: {e}")
                connection.rollback()
                raise
            finally:
                cursor.close()
    
    def insert_price_history(self, price_data: Dict[str, Any]) -> bool:
        """
        إدراج سجل سعر جديد
        
        Args:
            price_data: بيانات السعر
            
        Returns:
            True إذا تم الإدراج بنجاح
        """
        query = """
        INSERT INTO price_history (product_id, price, currency, availability_status,
                                 seller_name, is_prime)
        VALUES (%(product_id)s, %(price)s, %(currency)s, %(availability_status)s,
                %(seller_name)s, %(is_prime)s)
        """
        
        try:
            self.execute_query(query, price_data)
            return True
        except Error as e:
            self.logger.error(f"خطأ في إدراج سجل السعر: {e}")
            return False
    
    def insert_deal(self, deal_data: Dict[str, Any]) -> int:
        """
        إدراج عرض جديد
        
        Args:
            deal_data: بيانات العرض
            
        Returns:
            معرف العرض المدرج
        """
        query = """
        INSERT INTO deals (product_id, deal_type, original_price, deal_price,
                          discount_percentage, discount_amount, start_date, end_date,
                          deal_status, max_quantity, deal_url, quality_score)
        VALUES (%(product_id)s, %(deal_type)s, %(original_price)s, %(deal_price)s,
                %(discount_percentage)s, %(discount_amount)s, %(start_date)s, %(end_date)s,
                %(deal_status)s, %(max_quantity)s, %(deal_url)s, %(quality_score)s)
        """
        
        with self.get_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, deal_data)
                connection.commit()
                return cursor.lastrowid
                
            except Error as e:
                self.logger.error(f"خطأ في إدراج العرض: {e}")
                connection.rollback()
                raise
            finally:
                cursor.close()
    
    def get_active_deals(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        الحصول على العروض النشطة
        
        Args:
            limit: عدد العروض المطلوبة
            
        Returns:
            قائمة العروض النشطة
        """
        query = """
        SELECT d.*, p.asin, p.title, p.image_url, p.amazon_url, p.rating, p.review_count
        FROM deals d
        JOIN products p ON d.product_id = p.id
        WHERE d.deal_status = 'active'
        AND (d.end_date IS NULL OR d.end_date > NOW())
        ORDER BY d.quality_score DESC, d.discount_percentage DESC
        LIMIT %s
        """
        
        results = self.execute_query(query, (limit,), fetch=True)
        
        deals = []
        for row in results:
            deal = {
                'id': row[0],
                'product_id': row[1],
                'deal_type': row[2],
                'original_price': float(row[3]),
                'deal_price': float(row[4]),
                'discount_percentage': float(row[5]),
                'discount_amount': float(row[6]),
                'start_date': row[7],
                'end_date': row[8],
                'deal_status': row[9],
                'quality_score': float(row[15]) if row[15] else 0,
                'asin': row[16],
                'title': row[17],
                'image_url': row[18],
                'amazon_url': row[19],
                'rating': float(row[20]) if row[20] else 0,
                'review_count': row[21] or 0
            }
            deals.append(deal)
        
        return deals
    
    def get_product_by_asin(self, asin: str) -> Optional[Dict[str, Any]]:
        """
        الحصول على منتج بواسطة ASIN
        
        Args:
            asin: معرف أمازون للمنتج
            
        Returns:
            بيانات المنتج أو None
        """
        query = "SELECT * FROM products WHERE asin = %s"
        results = self.execute_query(query, (asin,), fetch=True)
        
        if results:
            row = results[0]
            return {
                'id': row[0],
                'asin': row[1],
                'title': row[2],
                'title_ar': row[3],
                'description': row[4],
                'brand': row[5],
                'category_id': row[6],
                'image_url': row[7],
                'amazon_url': row[8],
                'rating': float(row[9]) if row[9] else 0,
                'review_count': row[10] or 0,
                'is_active': row[11],
                'first_seen': row[12],
                'last_updated': row[13]
            }
        
        return None
    
    def get_latest_price(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        الحصول على آخر سعر للمنتج
        
        Args:
            product_id: معرف المنتج
            
        Returns:
            بيانات آخر سعر أو None
        """
        query = """
        SELECT * FROM price_history 
        WHERE product_id = %s 
        ORDER BY recorded_at DESC 
        LIMIT 1
        """
        
        results = self.execute_query(query, (product_id,), fetch=True)
        
        if results:
            row = results[0]
            return {
                'id': row[0],
                'product_id': row[1],
                'price': float(row[2]),
                'currency': row[3],
                'availability_status': row[4],
                'seller_name': row[5],
                'is_prime': row[6],
                'recorded_at': row[7]
            }
        
        return None
    
    def log_activity(self, activity_type: str, description: str, 
                    related_table: Optional[str] = None, 
                    related_id: Optional[int] = None,
                    metadata: Optional[Dict] = None,
                    severity: str = 'info'):
        """
        تسجيل نشاط في السجل
        
        Args:
            activity_type: نوع النشاط
            description: وصف النشاط
            related_table: الجدول المرتبط
            related_id: معرف السجل المرتبط
            metadata: بيانات إضافية
            severity: مستوى الأهمية
        """
        query = """
        INSERT INTO activity_log (activity_type, description, related_table,
                                related_id, metadata, severity)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else None
        
        try:
            self.execute_query(query, (activity_type, description, related_table,
                                     related_id, metadata_json, severity))
        except Error as e:
            self.logger.error(f"خطأ في تسجيل النشاط: {e}")
    
    def cleanup_old_data(self, days: int = 30):
        """
        تنظيف البيانات القديمة
        
        Args:
            days: عدد الأيام للاحتفاظ بالبيانات
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # حذف سجلات الأسعار القديمة (الاحتفاظ بسجل واحد يومياً)
        cleanup_queries = [
            """
            DELETE ph1 FROM price_history ph1
            INNER JOIN price_history ph2 
            WHERE ph1.product_id = ph2.product_id
            AND ph1.recorded_at < %s
            AND DATE(ph1.recorded_at) = DATE(ph2.recorded_at)
            AND ph1.id < ph2.id
            """,
            
            # حذف سجلات النشاط القديمة
            "DELETE FROM activity_log WHERE created_at < %s",
            
            # حذف العروض المنتهية القديمة
            """
            DELETE FROM deals 
            WHERE deal_status = 'expired' 
            AND updated_at < %s
            """
        ]
        
        for query in cleanup_queries:
            try:
                rows_affected = self.execute_query(query, (cutoff_date,))
                self.logger.info(f"تم حذف {rows_affected} سجل من البيانات القديمة")
            except Error as e:
                self.logger.error(f"خطأ في تنظيف البيانات: {e}")
    
    def get_performance_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        الحصول على إحصائيات الأداء
        
        Args:
            days: عدد الأيام للإحصائيات
            
        Returns:
            إحصائيات الأداء
        """
        start_date = datetime.now() - timedelta(days=days)
        
        queries = {
            'total_products': "SELECT COUNT(*) FROM products WHERE is_active = 1",
            'active_deals': "SELECT COUNT(*) FROM deals WHERE deal_status = 'active'",
            'messages_sent': """
                SELECT COUNT(*) FROM sent_messages 
                WHERE sent_at >= %s AND delivery_status = 'sent'
            """,
            'errors_count': """
                SELECT COUNT(*) FROM activity_log 
                WHERE created_at >= %s AND severity IN ('error', 'critical')
            """
        }
        
        stats = {}
        for key, query in queries.items():
            try:
                if key in ['messages_sent', 'errors_count']:
                    result = self.execute_query(query, (start_date,), fetch=True)
                else:
                    result = self.execute_query(query, fetch=True)
                
                stats[key] = result[0][0] if result else 0
            except Error as e:
                self.logger.error(f"خطأ في الحصول على إحصائية {key}: {e}")
                stats[key] = 0
        
        return stats
    
    def close(self):
        """إغلاق الاتصالات"""
        try:
            if self.engine:
                self.engine.dispose()
            self.logger.info("تم إغلاق اتصالات قاعدة البيانات")
        except Exception as e:
            self.logger.error(f"خطأ في إغلاق قاعدة البيانات: {e}")

