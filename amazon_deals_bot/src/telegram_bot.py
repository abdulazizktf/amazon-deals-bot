"""
وحدة بوت التليجرام لنشر العروض والتفاعل مع المستخدمين
تاريخ الإنشاء: 11 يوليو 2025
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import re
import json

from telegram import (
    Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup,
    ParseMode, InputMediaPhoto, Message
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes
)
from telegram.error import TelegramError, RetryAfter, TimedOut

class TelegramBot:
    """بوت التليجرام لنشر العروض"""
    
    def __init__(self, config: Dict[str, Any], database_manager, deals_engine):
        """
        تهيئة بوت التليجرام
        
        Args:
            config: إعدادات النظام
            database_manager: مدير قاعدة البيانات
            deals_engine: محرك العروض
        """
        self.config = config
        self.telegram_config = config['telegram']
        self.messaging_config = config['messaging']
        self.db = database_manager
        self.deals_engine = deals_engine
        self.logger = logging.getLogger(__name__)
        
        # إعداد البوت
        self.bot_token = self.telegram_config['bot_token']
        if not self.bot_token:
            raise ValueError("يجب تحديد bot_token في الإعدادات")
        
        self.application = None
        self.bot = None
        
        # إعدادات الرسائل
        self.max_message_length = self.telegram_config['max_message_length']
        self.rate_limit = self.telegram_config['rate_limit']
        
        # قوالب الرسائل
        self.message_template = self.messaging_config['message_template']
        
        # إحصائيات الإرسال
        self.stats = {
            'messages_sent': 0,
            'messages_failed': 0,
            'users_count': 0,
            'channels_count': 0
        }
    
    async def initialize(self):
        """تهيئة بوت التليجرام"""
        try:
            self.logger.info("بدء تهيئة بوت التليجرام...")
            
            # إنشاء التطبيق
            self.application = Application.builder().token(self.bot_token).build()
            self.bot = self.application.bot
            
            # إضافة معالجات الأوامر
            self._setup_handlers()
            
            # فحص صحة التوكن
            bot_info = await self.bot.get_me()
            self.logger.info(f"تم تهيئة البوت: @{bot_info.username}")
            
            # تسجيل النشاط
            self.db.log_activity(
                'system',
                f'تم تهيئة بوت التليجرام: @{bot_info.username}',
                severity='info'
            )
            
        except Exception as e:
            self.logger.error(f"خطأ في تهيئة بوت التليجرام: {e}")
            raise
    
    def _setup_handlers(self):
        """إعداد معالجات الأوامر والرسائل"""
        # أوامر أساسية
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("deals", self.deals_command))
        self.application.add_handler(CommandHandler("subscribe", self.subscribe_command))
        self.application.add_handler(CommandHandler("unsubscribe", self.unsubscribe_command))
        self.application.add_handler(CommandHandler("settings", self.settings_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        
        # معالج الأزرار التفاعلية
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # معالج الرسائل النصية
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        
        # معالج الأخطاء
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج أمر /start"""
        user = update.effective_user
        chat = update.effective_chat
        
        try:
            # تسجيل المستخدم
            await self._register_user(user, chat)
            
            welcome_message = """
🤖 **مرحباً بك في بوت عروض أمازون السعودية!**

أنا هنا لأساعدك في العثور على أفضل العروض والخصومات من أمازون السعودية 🇸🇦

**ما يمكنني فعله:**
🔍 البحث عن أحدث العروض والخصومات
📱 إرسال تنبيهات فورية للعروض المميزة
⚙️ تخصيص التفضيلات حسب اهتماماتك
📊 عرض إحصائيات العروض

**الأوامر المتاحة:**
/deals - عرض أحدث العروض
/subscribe - الاشتراك في التنبيهات
/settings - إعدادات التفضيلات
/help - المساعدة

اضغط على /deals لمشاهدة أحدث العروض! 🛒
            """
            
            keyboard = [
                [InlineKeyboardButton("🔥 أحدث العروض", callback_data="latest_deals")],
                [InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings")],
                [InlineKeyboardButton("📞 المساعدة", callback_data="help")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                welcome_message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            self.logger.error(f"خطأ في أمر start: {e}")
            await update.message.reply_text("حدث خطأ، يرجى المحاولة مرة أخرى.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج أمر /help"""
        help_text = """
📖 **دليل استخدام بوت عروض أمازون**

**الأوامر الأساسية:**
/start - بدء استخدام البوت
/deals - عرض أحدث العروض (آخر 10 عروض)
/subscribe - الاشتراك في تنبيهات العروض
/unsubscribe - إلغاء الاشتراك
/settings - تخصيص الإعدادات والتفضيلات
/stats - عرض إحصائيات النظام

**كيفية الاشتراك:**
1. استخدم الأمر /subscribe
2. اختر نوع الاشتراك (فئة، علامة تجارية، نطاق سعري)
3. حدد التفضيلات
4. ستصلك التنبيهات تلقائياً!

**أنواع العروض:**
🔥 عروض خاطفة - خصومات عالية لفترة محدودة
⭐ عروض يومية - عروض مميزة يومياً
🏷️ عروض تصفية - خصومات على المخزون
💰 عروض عامة - خصومات متنوعة

**نصائح:**
• فعّل الإشعارات لتلقي التنبيهات فوراً
• استخدم الفلاتر لتخصيص العروض
• تحقق من التقييمات قبل الشراء

للمساعدة الإضافية، تواصل معنا! 📞
        """
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def deals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج أمر /deals"""
        try:
            # الحصول على أحدث العروض
            deals = await self.deals_engine.get_active_deals(limit=10)
            
            if not deals:
                await update.message.reply_text(
                    "🤷‍♂️ لا توجد عروض متاحة حالياً. سنبحث عن المزيد قريباً!"
                )
                return
            
            # إرسال العروض
            await self._send_deals_to_chat(update.effective_chat.id, deals, context)
            
        except Exception as e:
            self.logger.error(f"خطأ في أمر deals: {e}")
            await update.message.reply_text("حدث خطأ في جلب العروض، يرجى المحاولة لاحقاً.")
    
    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج أمر /subscribe"""
        keyboard = [
            [InlineKeyboardButton("📱 الإلكترونيات", callback_data="sub_electronics")],
            [InlineKeyboardButton("💻 أجهزة الكمبيوتر", callback_data="sub_computers")],
            [InlineKeyboardButton("🏠 المنزل والمطبخ", callback_data="sub_home")],
            [InlineKeyboardButton("👕 الأزياء", callback_data="sub_fashion")],
            [InlineKeyboardButton("📚 الكتب", callback_data="sub_books")],
            [InlineKeyboardButton("🎯 جميع العروض", callback_data="sub_all")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔔 **اختر نوع العروض التي تريد الاشتراك فيها:**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج أمر /settings"""
        user_id = update.effective_user.id
        
        # الحصول على إعدادات المستخدم الحالية
        user_settings = await self._get_user_settings(user_id)
        
        settings_text = f"""
⚙️ **إعداداتك الحالية:**

🔔 الإشعارات: {'مفعلة' if user_settings.get('notifications', True) else 'معطلة'}
💰 الحد الأدنى للخصم: {user_settings.get('min_discount', 20)}%
💵 الحد الأقصى للسعر: {user_settings.get('max_price', 1000)} ريال
🏷️ الفئات المفضلة: {', '.join(user_settings.get('categories', ['جميع الفئات']))}

**لتغيير الإعدادات، استخدم الأزرار أدناه:**
        """
        
        keyboard = [
            [InlineKeyboardButton("🔔 تبديل الإشعارات", callback_data="toggle_notifications")],
            [InlineKeyboardButton("💰 تغيير حد الخصم", callback_data="change_discount")],
            [InlineKeyboardButton("💵 تغيير حد السعر", callback_data="change_price")],
            [InlineKeyboardButton("🏷️ تغيير الفئات", callback_data="change_categories")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            settings_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج أمر /stats"""
        try:
            # الحصول على إحصائيات النظام
            system_stats = self.deals_engine.get_system_stats()
            bot_stats = self.stats
            
            stats_text = f"""
📊 **إحصائيات النظام:**

🤖 **البوت:**
• الرسائل المرسلة: {bot_stats['messages_sent']:,}
• الرسائل الفاشلة: {bot_stats['messages_failed']:,}
• عدد المستخدمين: {bot_stats['users_count']:,}
• عدد القنوات: {bot_stats['channels_count']:,}

🔍 **محرك العروض:**
• المنتجات المفحوصة: {system_stats.get('session_stats', {}).get('products_scraped', 0):,}
• العروض المكتشفة: {system_stats.get('session_stats', {}).get('deals_found', 0):,}
• آخر تشغيل: {system_stats.get('last_run', 'غير متاح')}
• حالة النظام: {'🟢 يعمل' if system_stats.get('is_running', False) else '🔴 متوقف'}

💾 **قاعدة البيانات:**
• إجمالي المنتجات: {system_stats.get('database_stats', {}).get('total_products', 0):,}
• العروض النشطة: {system_stats.get('database_stats', {}).get('active_deals', 0):,}
• الرسائل المرسلة (7 أيام): {system_stats.get('database_stats', {}).get('messages_sent', 0):,}

⏱️ **وقت التشغيل:** {system_stats.get('runtime_hours', 0):.1f} ساعة
            """
            
            await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            self.logger.error(f"خطأ في أمر stats: {e}")
            await update.message.reply_text("حدث خطأ في جلب الإحصائيات.")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الأزرار التفاعلية"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        try:
            if data == "latest_deals":
                await self.deals_command(update, context)
            elif data == "help":
                await self.help_command(update, context)
            elif data == "settings":
                await self.settings_command(update, context)
            elif data.startswith("sub_"):
                await self._handle_subscription(query, data)
            elif data.startswith("deal_"):
                await self._handle_deal_action(query, data)
            else:
                await query.edit_message_text("خيار غير معروف.")
                
        except Exception as e:
            self.logger.error(f"خطأ في معالج الأزرار: {e}")
            await query.edit_message_text("حدث خطأ، يرجى المحاولة مرة أخرى.")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الرسائل النصية"""
        text = update.message.text.lower()
        
        # ردود تلقائية بسيطة
        if any(word in text for word in ['مرحبا', 'السلام', 'أهلا']):
            await update.message.reply_text("مرحباً! كيف يمكنني مساعدتك؟ استخدم /help للمساعدة.")
        elif any(word in text for word in ['عروض', 'خصومات', 'تخفيضات']):
            await update.message.reply_text("استخدم الأمر /deals لمشاهدة أحدث العروض!")
        elif any(word in text for word in ['مساعدة', 'help']):
            await self.help_command(update, context)
        else:
            await update.message.reply_text(
                "لم أفهم طلبك. استخدم /help لمشاهدة الأوامر المتاحة."
            )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الأخطاء"""
        self.logger.error(f"خطأ في البوت: {context.error}")
        
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى لاحقاً."
                )
            except:
                pass
    
    async def send_deal_to_channel(self, channel_id: Union[str, int], deal: Dict[str, Any]) -> bool:
        """
        إرسال عرض إلى قناة محددة
        
        Args:
            channel_id: معرف القناة
            deal: معلومات العرض
            
        Returns:
            True إذا تم الإرسال بنجاح
        """
        try:
            # تنسيق رسالة العرض
            message_text = self._format_deal_message(deal)
            
            # إعداد الأزرار
            keyboard = [
                [InlineKeyboardButton("🛒 اشتري الآن", url=deal.get('amazon_url', ''))],
                [InlineKeyboardButton("📊 تفاصيل أكثر", callback_data=f"deal_{deal.get('id')}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # إرسال الرسالة
            if deal.get('image_url') and self.messaging_config.get('include_image', True):
                # إرسال مع صورة
                message = await self.bot.send_photo(
                    chat_id=channel_id,
                    photo=deal['image_url'],
                    caption=message_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            else:
                # إرسال نص فقط
                message = await self.bot.send_message(
                    chat_id=channel_id,
                    text=message_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup,
                    disable_web_page_preview=False
                )
            
            # تسجيل الرسالة المرسلة
            await self._log_sent_message(deal, channel_id, message.message_id, 'deal_alert')
            
            self.stats['messages_sent'] += 1
            return True
            
        except RetryAfter as e:
            self.logger.warning(f"تم تجاوز حد الإرسال، انتظار {e.retry_after} ثانية")
            await asyncio.sleep(e.retry_after)
            return await self.send_deal_to_channel(channel_id, deal)
            
        except TelegramError as e:
            self.logger.error(f"خطأ في إرسال العرض للقناة {channel_id}: {e}")
            self.stats['messages_failed'] += 1
            return False
            
        except Exception as e:
            self.logger.error(f"خطأ غير متوقع في إرسال العرض: {e}")
            self.stats['messages_failed'] += 1
            return False
    
    def _format_deal_message(self, deal: Dict[str, Any]) -> str:
        """تنسيق رسالة العرض"""
        try:
            # استخدام القالب من الإعدادات
            template = self.message_template
            
            # تحضير البيانات للقالب
            format_data = {
                'product_name': deal.get('title', 'منتج غير محدد')[:100],
                'rating': deal.get('rating', 0),
                'review_count': deal.get('review_count', 0),
                'original_price': f"{deal.get('original_price', 0):.0f}",
                'deal_price': f"{deal.get('deal_price', 0):.0f}",
                'discount_percentage': f"{deal.get('discount_percentage', 0):.0f}",
                'savings': f"{deal.get('discount_amount', 0):.0f}",
                'product_url': deal.get('amazon_url', '')
            }
            
            # تطبيق القالب
            message = template.format(**format_data)
            
            # التأكد من عدم تجاوز الحد الأقصى للطول
            if len(message) > self.max_message_length:
                message = message[:self.max_message_length-3] + "..."
            
            return message
            
        except Exception as e:
            self.logger.error(f"خطأ في تنسيق رسالة العرض: {e}")
            # رسالة احتياطية
            return f"""
🔥 **عرض مميز**

📱 {deal.get('title', 'منتج')[:50]}
💰 السعر: {deal.get('deal_price', 0):.0f} ريال
📉 خصم: {deal.get('discount_percentage', 0):.0f}%

🛒 [اشتري الآن]({deal.get('amazon_url', '')})
            """.strip()
    
    async def broadcast_deals(self, deals: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        بث العروض لجميع القنوات المشتركة
        
        Args:
            deals: قائمة العروض
            
        Returns:
            إحصائيات الإرسال
        """
        broadcast_stats = {
            'channels_sent': 0,
            'messages_sent': 0,
            'messages_failed': 0
        }
        
        try:
            # الحصول على قائمة القنوات النشطة
            active_channels = await self._get_active_channels()
            
            if not active_channels:
                self.logger.warning("لا توجد قنوات نشطة للبث")
                return broadcast_stats
            
            # إرسال العروض لكل قناة
            for channel in active_channels:
                channel_id = channel['telegram_id']
                
                try:
                    # فلترة العروض حسب إعدادات القناة
                    filtered_deals = self._filter_deals_for_channel(deals, channel)
                    
                    if not filtered_deals:
                        continue
                    
                    # إرسال العروض (حد أقصى 5 عروض لكل قناة)
                    sent_count = 0
                    max_deals = self.messaging_config.get('max_deals_per_message', 1)
                    
                    for deal in filtered_deals[:5]:  # حد أقصى 5 عروض
                        if await self.send_deal_to_channel(channel_id, deal):
                            sent_count += 1
                            broadcast_stats['messages_sent'] += 1
                        else:
                            broadcast_stats['messages_failed'] += 1
                        
                        # تأخير بين الرسائل
                        await asyncio.sleep(1)
                    
                    if sent_count > 0:
                        broadcast_stats['channels_sent'] += 1
                        self.logger.info(f"تم إرسال {sent_count} عرض للقناة {channel_id}")
                
                except Exception as e:
                    self.logger.error(f"خطأ في إرسال العروض للقناة {channel_id}: {e}")
                    broadcast_stats['messages_failed'] += 1
            
            self.logger.info(
                f"انتهى البث - القنوات: {broadcast_stats['channels_sent']}, "
                f"الرسائل: {broadcast_stats['messages_sent']}, "
                f"الأخطاء: {broadcast_stats['messages_failed']}"
            )
            
            return broadcast_stats
            
        except Exception as e:
            self.logger.error(f"خطأ في بث العروض: {e}")
            return broadcast_stats
    
    async def _register_user(self, user, chat):
        """تسجيل مستخدم جديد"""
        try:
            user_data = {
                'telegram_id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'language_code': user.language_code or 'ar'
            }
            
            # يمكن إضافة منطق حفظ المستخدم في قاعدة البيانات هنا
            self.logger.info(f"تم تسجيل مستخدم جديد: {user.id}")
            
        except Exception as e:
            self.logger.error(f"خطأ في تسجيل المستخدم: {e}")
    
    async def _get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """الحصول على إعدادات المستخدم"""
        # يمكن تطوير هذا لاحقاً لجلب الإعدادات من قاعدة البيانات
        return {
            'notifications': True,
            'min_discount': 20,
            'max_price': 1000,
            'categories': ['جميع الفئات']
        }
    
    async def _get_active_channels(self) -> List[Dict[str, Any]]:
        """الحصول على القنوات النشطة"""
        try:
            # يمكن تطوير هذا لاحقاً لجلب القنوات من قاعدة البيانات
            # حالياً نعيد قائمة فارغة
            return []
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على القنوات النشطة: {e}")
            return []
    
    def _filter_deals_for_channel(self, deals: List[Dict[str, Any]], 
                                 channel: Dict[str, Any]) -> List[Dict[str, Any]]:
        """فلترة العروض حسب إعدادات القناة"""
        # يمكن تطوير هذا لاحقاً لتطبيق فلاتر متقدمة
        return deals
    
    async def _log_sent_message(self, deal: Dict[str, Any], channel_id: Union[str, int], 
                              message_id: int, message_type: str):
        """تسجيل الرسالة المرسلة"""
        try:
            # يمكن إضافة منطق حفظ سجل الرسائل في قاعدة البيانات هنا
            self.logger.debug(f"تم إرسال رسالة {message_type} للقناة {channel_id}")
        except Exception as e:
            self.logger.error(f"خطأ في تسجيل الرسالة المرسلة: {e}")
    
    async def _send_deals_to_chat(self, chat_id: int, deals: List[Dict[str, Any]], context):
        """إرسال العروض لمحادثة محددة"""
        try:
            for i, deal in enumerate(deals[:5]):  # حد أقصى 5 عروض
                await self.send_deal_to_channel(chat_id, deal)
                
                if i < len(deals) - 1:  # تأخير بين الرسائل
                    await asyncio.sleep(1)
                    
        except Exception as e:
            self.logger.error(f"خطأ في إرسال العروض للمحادثة: {e}")
    
    async def _handle_subscription(self, query, data):
        """معالجة طلبات الاشتراك"""
        # يمكن تطوير هذا لاحقاً
        await query.edit_message_text("تم تسجيل اشتراكك! ستصلك التنبيهات قريباً.")
    
    async def _handle_deal_action(self, query, data):
        """معالجة إجراءات العروض"""
        # يمكن تطوير هذا لاحقاً
        await query.edit_message_text("تفاصيل العرض...")
    
    async def start_bot(self):
        """بدء تشغيل البوت"""
        try:
            self.logger.info("بدء تشغيل بوت التليجرام...")
            await self.application.initialize()
            await self.application.start()
            
            # بدء polling
            await self.application.updater.start_polling()
            self.logger.info("بوت التليجرام يعمل الآن...")
            
        except Exception as e:
            self.logger.error(f"خطأ في تشغيل البوت: {e}")
            raise
    
    async def stop_bot(self):
        """إيقاف البوت"""
        try:
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            
            self.logger.info("تم إيقاف بوت التليجرام")
            
        except Exception as e:
            self.logger.error(f"خطأ في إيقاف البوت: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات البوت"""
        return self.stats.copy()

