"""
وحدة إدارة القنوات والمستخدمين
تاريخ الإنشاء: 11 يوليو 2025
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json

class ChannelManager:
    """مدير القنوات والمستخدمين"""
    
    def __init__(self, database_manager):
        """
        تهيئة مدير القنوات
        
        Args:
            database_manager: مدير قاعدة البيانات
        """
        self.db = database_manager
        self.logger = logging.getLogger(__name__)
    
    async def register_channel(self, channel_data: Dict[str, Any]) -> bool:
        """
        تسجيل قناة جديدة
        
        Args:
            channel_data: بيانات القناة
            
        Returns:
            True إذا تم التسجيل بنجاح
        """
        try:
            query = """
            INSERT INTO telegram_channels (telegram_id, channel_name, channel_type,
                                         admin_user_id, settings, is_active)
            VALUES (%(telegram_id)s, %(channel_name)s, %(channel_type)s,
                    %(admin_user_id)s, %(settings)s, %(is_active)s)
            ON DUPLICATE KEY UPDATE
                channel_name = VALUES(channel_name),
                settings = VALUES(settings),
                is_active = VALUES(is_active),
                updated_at = CURRENT_TIMESTAMP
            """
            
            # تحضير البيانات
            record_data = {
                'telegram_id': channel_data['telegram_id'],
                'channel_name': channel_data.get('channel_name', ''),
                'channel_type': channel_data.get('channel_type', 'channel'),
                'admin_user_id': channel_data.get('admin_user_id'),
                'settings': json.dumps(channel_data.get('settings', {}), ensure_ascii=False),
                'is_active': channel_data.get('is_active', True)
            }
            
            self.db.execute_query(query, record_data)
            
            self.logger.info(f"تم تسجيل القناة: {channel_data['telegram_id']}")
            
            # تسجيل النشاط
            self.db.log_activity(
                'channel_registered',
                f"تم تسجيل قناة جديدة: {channel_data.get('channel_name', 'Unknown')}",
                'telegram_channels',
                None,
                {'telegram_id': channel_data['telegram_id']}
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"خطأ في تسجيل القناة: {e}")
            return False
    
    async def register_user(self, user_data: Dict[str, Any]) -> bool:
        """
        تسجيل مستخدم جديد
        
        Args:
            user_data: بيانات المستخدم
            
        Returns:
            True إذا تم التسجيل بنجاح
        """
        try:
            query = """
            INSERT INTO telegram_users (telegram_id, username, first_name, last_name,
                                      language_code, preferences, is_active)
            VALUES (%(telegram_id)s, %(username)s, %(first_name)s, %(last_name)s,
                    %(language_code)s, %(preferences)s, %(is_active)s)
            ON DUPLICATE KEY UPDATE
                username = VALUES(username),
                first_name = VALUES(first_name),
                last_name = VALUES(last_name),
                language_code = VALUES(language_code),
                last_interaction = CURRENT_TIMESTAMP
            """
            
            # تحضير البيانات
            record_data = {
                'telegram_id': user_data['telegram_id'],
                'username': user_data.get('username', '')[:50] if user_data.get('username') else None,
                'first_name': user_data.get('first_name', '')[:100],
                'last_name': user_data.get('last_name', '')[:100] if user_data.get('last_name') else None,
                'language_code': user_data.get('language_code', 'ar'),
                'preferences': json.dumps(user_data.get('preferences', {}), ensure_ascii=False),
                'is_active': user_data.get('is_active', True)
            }
            
            self.db.execute_query(query, record_data)
            
            self.logger.info(f"تم تسجيل المستخدم: {user_data['telegram_id']}")
            return True
            
        except Exception as e:
            self.logger.error(f"خطأ في تسجيل المستخدم: {e}")
            return False
    
    async def get_active_channels(self) -> List[Dict[str, Any]]:
        """الحصول على القنوات النشطة"""
        try:
            query = """
            SELECT telegram_id, channel_name, channel_type, settings, created_at
            FROM telegram_channels 
            WHERE is_active = 1
            ORDER BY created_at DESC
            """
            
            results = self.db.execute_query(query, fetch=True)
            
            channels = []
            for row in results:
                channel = {
                    'telegram_id': row[0],
                    'channel_name': row[1],
                    'channel_type': row[2],
                    'settings': json.loads(row[3]) if row[3] else {},
                    'created_at': row[4]
                }
                channels.append(channel)
            
            return channels
            
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على القنوات النشطة: {e}")
            return []
    
    async def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """الحصول على تفضيلات المستخدم"""
        try:
            query = """
            SELECT preferences FROM telegram_users 
            WHERE telegram_id = %s AND is_active = 1
            """
            
            results = self.db.execute_query(query, (user_id,), fetch=True)
            
            if results:
                preferences = json.loads(results[0][0]) if results[0][0] else {}
                return preferences
            
            # إعدادات افتراضية للمستخدمين الجدد
            return {
                'notifications': True,
                'min_discount': 20,
                'max_price': 1000,
                'categories': [],
                'deal_types': ['all'],
                'language': 'ar'
            }
            
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على تفضيلات المستخدم: {e}")
            return {}
    
    async def update_user_preferences(self, user_id: int, preferences: Dict[str, Any]) -> bool:
        """تحديث تفضيلات المستخدم"""
        try:
            query = """
            UPDATE telegram_users 
            SET preferences = %s, updated_at = CURRENT_TIMESTAMP
            WHERE telegram_id = %s
            """
            
            preferences_json = json.dumps(preferences, ensure_ascii=False)
            self.db.execute_query(query, (preferences_json, user_id))
            
            self.logger.info(f"تم تحديث تفضيلات المستخدم: {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"خطأ في تحديث تفضيلات المستخدم: {e}")
            return False
    
    async def subscribe_user_to_category(self, user_id: int, category: str) -> bool:
        """اشتراك المستخدم في فئة معينة"""
        try:
            # الحصول على التفضيلات الحالية
            preferences = await self.get_user_preferences(user_id)
            
            # إضافة الفئة
            categories = preferences.get('categories', [])
            if category not in categories:
                categories.append(category)
                preferences['categories'] = categories
                
                # تحديث التفضيلات
                await self.update_user_preferences(user_id, preferences)
                
                # تسجيل الاشتراك
                self.db.log_activity(
                    'user_subscribed',
                    f"اشترك المستخدم في فئة: {category}",
                    'telegram_users',
                    user_id,
                    {'category': category}
                )
                
                return True
            
            return False  # المستخدم مشترك بالفعل
            
        except Exception as e:
            self.logger.error(f"خطأ في اشتراك المستخدم: {e}")
            return False
    
    async def unsubscribe_user_from_category(self, user_id: int, category: str) -> bool:
        """إلغاء اشتراك المستخدم من فئة معينة"""
        try:
            # الحصول على التفضيلات الحالية
            preferences = await self.get_user_preferences(user_id)
            
            # إزالة الفئة
            categories = preferences.get('categories', [])
            if category in categories:
                categories.remove(category)
                preferences['categories'] = categories
                
                # تحديث التفضيلات
                await self.update_user_preferences(user_id, preferences)
                
                # تسجيل إلغاء الاشتراك
                self.db.log_activity(
                    'user_unsubscribed',
                    f"ألغى المستخدم اشتراكه من فئة: {category}",
                    'telegram_users',
                    user_id,
                    {'category': category}
                )
                
                return True
            
            return False  # المستخدم غير مشترك
            
        except Exception as e:
            self.logger.error(f"خطأ في إلغاء اشتراك المستخدم: {e}")
            return False
    
    async def get_users_for_deal(self, deal: Dict[str, Any]) -> List[int]:
        """
        الحصول على المستخدمين المهتمين بعرض معين
        
        Args:
            deal: معلومات العرض
            
        Returns:
            قائمة معرفات المستخدمين
        """
        try:
            # الحصول على جميع المستخدمين النشطين
            query = """
            SELECT telegram_id, preferences FROM telegram_users 
            WHERE is_active = 1 AND preferences IS NOT NULL
            """
            
            results = self.db.execute_query(query, fetch=True)
            
            interested_users = []
            
            for row in results:
                user_id = row[0]
                preferences = json.loads(row[1]) if row[1] else {}
                
                if self._is_user_interested_in_deal(deal, preferences):
                    interested_users.append(user_id)
            
            return interested_users
            
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على المستخدمين المهتمين: {e}")
            return []
    
    def _is_user_interested_in_deal(self, deal: Dict[str, Any], preferences: Dict[str, Any]) -> bool:
        """فحص إذا كان المستخدم مهتماً بالعرض"""
        try:
            # فحص الإشعارات
            if not preferences.get('notifications', True):
                return False
            
            # فحص نسبة الخصم الدنيا
            min_discount = preferences.get('min_discount', 0)
            if deal.get('discount_percentage', 0) < min_discount:
                return False
            
            # فحص الحد الأقصى للسعر
            max_price = preferences.get('max_price', float('inf'))
            if deal.get('deal_price', 0) > max_price:
                return False
            
            # فحص الفئات المفضلة
            user_categories = preferences.get('categories', [])
            if user_categories and 'all' not in user_categories:
                # يمكن تطوير هذا لاحقاً لمطابقة فئات المنتج
                pass
            
            # فحص أنواع العروض المفضلة
            user_deal_types = preferences.get('deal_types', ['all'])
            if 'all' not in user_deal_types:
                deal_type = deal.get('deal_type', 'other')
                if deal_type not in user_deal_types:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"خطأ في فحص اهتمام المستخدم: {e}")
            return False
    
    async def log_message_sent(self, deal_id: int, recipient_id: Union[str, int], 
                             message_id: int, message_type: str = 'deal_alert') -> bool:
        """تسجيل رسالة مرسلة"""
        try:
            query = """
            INSERT INTO sent_messages (deal_id, recipient_id, message_id, message_type,
                                     delivery_status, sent_at)
            VALUES (%s, %s, %s, %s, 'sent', CURRENT_TIMESTAMP)
            """
            
            self.db.execute_query(query, (deal_id, str(recipient_id), message_id, message_type))
            return True
            
        except Exception as e:
            self.logger.error(f"خطأ في تسجيل الرسالة المرسلة: {e}")
            return False
    
    async def update_message_status(self, message_id: int, status: str, 
                                  error_message: Optional[str] = None) -> bool:
        """تحديث حالة الرسالة"""
        try:
            query = """
            UPDATE sent_messages 
            SET delivery_status = %s, error_message = %s, updated_at = CURRENT_TIMESTAMP
            WHERE message_id = %s
            """
            
            self.db.execute_query(query, (status, error_message, message_id))
            return True
            
        except Exception as e:
            self.logger.error(f"خطأ في تحديث حالة الرسالة: {e}")
            return False
    
    async def get_channel_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات القنوات"""
        try:
            stats = {}
            
            # عدد القنوات النشطة
            query = "SELECT COUNT(*) FROM telegram_channels WHERE is_active = 1"
            result = self.db.execute_query(query, fetch=True)
            stats['active_channels'] = result[0][0] if result else 0
            
            # عدد المستخدمين النشطين
            query = "SELECT COUNT(*) FROM telegram_users WHERE is_active = 1"
            result = self.db.execute_query(query, fetch=True)
            stats['active_users'] = result[0][0] if result else 0
            
            # عدد الرسائل المرسلة اليوم
            query = """
            SELECT COUNT(*) FROM sent_messages 
            WHERE DATE(sent_at) = CURDATE() AND delivery_status = 'sent'
            """
            result = self.db.execute_query(query, fetch=True)
            stats['messages_today'] = result[0][0] if result else 0
            
            # عدد الرسائل الفاشلة اليوم
            query = """
            SELECT COUNT(*) FROM sent_messages 
            WHERE DATE(sent_at) = CURDATE() AND delivery_status = 'failed'
            """
            result = self.db.execute_query(query, fetch=True)
            stats['failed_messages_today'] = result[0][0] if result else 0
            
            return stats
            
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على إحصائيات القنوات: {e}")
            return {}
    
    async def cleanup_inactive_users(self, days: int = 30) -> int:
        """تنظيف المستخدمين غير النشطين"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            query = """
            UPDATE telegram_users 
            SET is_active = 0 
            WHERE last_interaction < %s AND is_active = 1
            """
            
            rows_affected = self.db.execute_query(query, (cutoff_date,))
            
            if rows_affected:
                self.logger.info(f"تم تعطيل {rows_affected} مستخدم غير نشط")
                
                # تسجيل النشاط
                self.db.log_activity(
                    'cleanup',
                    f"تم تعطيل {rows_affected} مستخدم غير نشط",
                    severity='info'
                )
            
            return rows_affected or 0
            
        except Exception as e:
            self.logger.error(f"خطأ في تنظيف المستخدمين غير النشطين: {e}")
            return 0
    
    async def get_user_activity_stats(self, days: int = 7) -> Dict[str, Any]:
        """الحصول على إحصائيات نشاط المستخدمين"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            stats = {}
            
            # المستخدمين النشطين
            query = """
            SELECT COUNT(*) FROM telegram_users 
            WHERE last_interaction >= %s AND is_active = 1
            """
            result = self.db.execute_query(query, (start_date,), fetch=True)
            stats['active_users'] = result[0][0] if result else 0
            
            # المستخدمين الجدد
            query = """
            SELECT COUNT(*) FROM telegram_users 
            WHERE created_at >= %s
            """
            result = self.db.execute_query(query, (start_date,), fetch=True)
            stats['new_users'] = result[0][0] if result else 0
            
            # الاشتراكات الجديدة
            query = """
            SELECT COUNT(*) FROM activity_log 
            WHERE activity_type = 'user_subscribed' AND created_at >= %s
            """
            result = self.db.execute_query(query, (start_date,), fetch=True)
            stats['new_subscriptions'] = result[0][0] if result else 0
            
            return stats
            
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على إحصائيات النشاط: {e}")
            return {}

