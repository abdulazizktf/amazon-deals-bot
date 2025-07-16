"""
وحدة تحليل وتقييم العروض
تاريخ الإنشاء: 11 يوليو 2025
"""

from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime, timedelta
import statistics
import re

class DealAnalyzer:
    """محلل ومقيم العروض"""
    
    def __init__(self, config: Dict[str, Any], database_manager):
        """
        تهيئة محلل العروض
        
        Args:
            config: إعدادات النظام
            database_manager: مدير قاعدة البيانات
        """
        self.config = config
        self.db = database_manager
        self.logger = logging.getLogger(__name__)
        
        # إعدادات التقييم
        self.quality_config = config['deals']['quality_scoring']
        self.min_discount = config['deals']['min_discount_percentage']
        self.min_price = config['deals']['min_original_price']
        self.max_price = config['deals']['max_original_price']
        
        # أوزان التقييم
        self.discount_weight = self.quality_config['discount_weight']
        self.rating_weight = self.quality_config['rating_weight']
        self.review_count_weight = self.quality_config['review_count_weight']
        self.price_range_weight = self.quality_config['price_range_weight']
    
    def analyze_product_for_deals(self, product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        تحليل منتج لاكتشاف العروض
        
        Args:
            product_data: بيانات المنتج المستخرجة
            
        Returns:
            معلومات العرض إذا تم اكتشافه أو None
        """
        try:
            # فحص وجود خصم
            if not self._has_discount(product_data):
                return None
            
            # الحصول على السجل التاريخي للمنتج
            existing_product = self.db.get_product_by_asin(product_data['asin'])
            price_history = []
            
            if existing_product:
                latest_price = self.db.get_latest_price(existing_product['id'])
                if latest_price:
                    price_history = [latest_price]
            
            # تحليل العرض
            deal_info = self._analyze_deal(product_data, price_history)
            
            if deal_info and self._is_significant_deal(deal_info):
                return deal_info
            
            return None
            
        except Exception as e:
            self.logger.error(f"خطأ في تحليل المنتج للعروض: {e}")
            return None
    
    def _has_discount(self, product_data: Dict[str, Any]) -> bool:
        """فحص وجود خصم في المنتج"""
        discount_percentage = product_data.get('discount_percentage')
        original_price = product_data.get('original_price')
        current_price = product_data.get('current_price')
        
        # فحص نسبة الخصم المباشرة
        if discount_percentage and discount_percentage >= self.min_discount:
            return True
        
        # حساب الخصم من الأسعار
        if original_price and current_price and original_price > current_price:
            calculated_discount = ((original_price - current_price) / original_price) * 100
            if calculated_discount >= self.min_discount:
                product_data['discount_percentage'] = round(calculated_discount, 2)
                return True
        
        return False
    
    def _analyze_deal(self, product_data: Dict[str, Any], 
                     price_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        تحليل تفاصيل العرض
        
        Args:
            product_data: بيانات المنتج
            price_history: تاريخ الأسعار
            
        Returns:
            معلومات العرض المحللة
        """
        current_price = product_data.get('current_price', 0)
        original_price = product_data.get('original_price', current_price)
        discount_percentage = product_data.get('discount_percentage', 0)
        
        # حساب مبلغ الخصم
        discount_amount = original_price - current_price if original_price > current_price else 0
        
        # تحديد نوع العرض
        deal_type = self._determine_deal_type(product_data, price_history)
        
        # حساب نقاط الجودة
        quality_score = self._calculate_quality_score(product_data, price_history)
        
        # تحديد مدة العرض المتوقعة
        estimated_end_date = self._estimate_deal_duration(deal_type)
        
        deal_info = {
            'product_id': None,  # سيتم تحديده لاحقاً
            'deal_type': deal_type,
            'original_price': original_price,
            'deal_price': current_price,
            'discount_percentage': discount_percentage,
            'discount_amount': discount_amount,
            'start_date': datetime.now(),
            'end_date': estimated_end_date,
            'deal_status': 'active',
            'quality_score': quality_score,
            'deal_url': product_data.get('amazon_url', ''),
            'is_featured': quality_score >= 8.0,  # العروض المميزة
            'analysis_metadata': {
                'price_trend': self._analyze_price_trend(price_history),
                'deal_strength': self._assess_deal_strength(discount_percentage, quality_score),
                'urgency_level': self._calculate_urgency_level(deal_type, quality_score),
                'target_audience': self._identify_target_audience(product_data)
            }
        }
        
        return deal_info
    
    def _determine_deal_type(self, product_data: Dict[str, Any], 
                           price_history: List[Dict[str, Any]]) -> str:
        """تحديد نوع العرض"""
        discount = product_data.get('discount_percentage', 0)
        
        # فحص العروض الخاطفة (خصم عالي)
        if discount >= 50:
            return 'lightning'
        
        # فحص العروض اليومية
        if discount >= 30:
            return 'daily'
        
        # فحص عروض التصفية
        if discount >= 20 and self._is_clearance_item(product_data):
            return 'clearance'
        
        # عروض الكوبونات
        if self._has_coupon(product_data):
            return 'coupon'
        
        # العروض الأسبوعية
        if discount >= 15:
            return 'weekly'
        
        return 'other'
    
    def _is_clearance_item(self, product_data: Dict[str, Any]) -> bool:
        """فحص إذا كان المنتج من عروض التصفية"""
        title = product_data.get('title', '').lower()
        clearance_keywords = ['تصفية', 'clearance', 'outlet', 'last chance', 'final sale']
        
        return any(keyword in title for keyword in clearance_keywords)
    
    def _has_coupon(self, product_data: Dict[str, Any]) -> bool:
        """فحص وجود كوبون خصم"""
        # يمكن تطوير هذا لاحقاً للبحث عن كوبونات في صفحة المنتج
        return False
    
    def _calculate_quality_score(self, product_data: Dict[str, Any], 
                               price_history: List[Dict[str, Any]]) -> float:
        """
        حساب نقاط جودة العرض
        
        Returns:
            نقاط الجودة من 0 إلى 10
        """
        scores = []
        
        # نقاط الخصم (0-10)
        discount = product_data.get('discount_percentage', 0)
        discount_score = min(10, (discount / 70) * 10)  # 70% = نقاط كاملة
        scores.append(discount_score * self.discount_weight)
        
        # نقاط التقييم (0-10)
        rating = product_data.get('rating', 0)
        rating_score = (rating / 5) * 10 if rating else 5  # افتراضي 5 إذا لم يكن متوفر
        scores.append(rating_score * self.rating_weight)
        
        # نقاط عدد المراجعات (0-10)
        review_count = product_data.get('review_count', 0)
        review_score = min(10, (review_count / 1000) * 10)  # 1000 مراجعة = نقاط كاملة
        scores.append(review_score * self.review_count_weight)
        
        # نقاط نطاق السعر (0-10)
        price = product_data.get('current_price', 0)
        price_score = self._calculate_price_range_score(price)
        scores.append(price_score * self.price_range_weight)
        
        # النقاط الإضافية
        bonus_score = self._calculate_bonus_score(product_data)
        
        total_score = sum(scores) + bonus_score
        return round(min(10, max(0, total_score)), 2)
    
    def _calculate_price_range_score(self, price: float) -> float:
        """حساب نقاط نطاق السعر"""
        if price <= 100:
            return 8  # أسعار منخفضة جذابة
        elif price <= 500:
            return 10  # النطاق الأمثل
        elif price <= 1000:
            return 7  # أسعار متوسطة
        elif price <= 2000:
            return 5  # أسعار عالية
        else:
            return 3  # أسعار عالية جداً
    
    def _calculate_bonus_score(self, product_data: Dict[str, Any]) -> float:
        """حساب النقاط الإضافية"""
        bonus = 0
        
        # Prime shipping
        if product_data.get('is_prime'):
            bonus += 0.5
        
        # توفر المنتج
        if product_data.get('availability') == 'in_stock':
            bonus += 0.3
        
        # علامة تجارية معروفة
        brand = product_data.get('brand', '').lower()
        known_brands = ['samsung', 'apple', 'sony', 'lg', 'hp', 'dell', 'nike', 'adidas']
        if any(brand_name in brand for brand_name in known_brands):
            bonus += 0.2
        
        return bonus
    
    def _analyze_price_trend(self, price_history: List[Dict[str, Any]]) -> str:
        """تحليل اتجاه السعر"""
        if len(price_history) < 2:
            return 'insufficient_data'
        
        prices = [record['price'] for record in price_history[-10:]]  # آخر 10 سجلات
        
        if len(prices) >= 3:
            # حساب الاتجاه
            recent_avg = statistics.mean(prices[-3:])
            older_avg = statistics.mean(prices[:-3])
            
            if recent_avg < older_avg * 0.9:
                return 'declining'
            elif recent_avg > older_avg * 1.1:
                return 'rising'
            else:
                return 'stable'
        
        return 'stable'
    
    def _assess_deal_strength(self, discount_percentage: float, quality_score: float) -> str:
        """تقييم قوة العرض"""
        if discount_percentage >= 50 and quality_score >= 8:
            return 'excellent'
        elif discount_percentage >= 30 and quality_score >= 7:
            return 'very_good'
        elif discount_percentage >= 20 and quality_score >= 6:
            return 'good'
        elif discount_percentage >= 15 and quality_score >= 5:
            return 'fair'
        else:
            return 'weak'
    
    def _calculate_urgency_level(self, deal_type: str, quality_score: float) -> str:
        """حساب مستوى الإلحاح للعرض"""
        if deal_type == 'lightning' or quality_score >= 9:
            return 'high'
        elif deal_type in ['daily', 'clearance'] or quality_score >= 7:
            return 'medium'
        else:
            return 'low'
    
    def _identify_target_audience(self, product_data: Dict[str, Any]) -> List[str]:
        """تحديد الجمهور المستهدف"""
        title = product_data.get('title', '').lower()
        price = product_data.get('current_price', 0)
        
        audiences = []
        
        # حسب السعر
        if price <= 100:
            audiences.append('budget_conscious')
        elif price >= 1000:
            audiences.append('premium_buyers')
        
        # حسب الفئة
        if any(keyword in title for keyword in ['laptop', 'computer', 'gaming']):
            audiences.append('tech_enthusiasts')
        elif any(keyword in title for keyword in ['fashion', 'clothing', 'shoes']):
            audiences.append('fashion_lovers')
        elif any(keyword in title for keyword in ['home', 'kitchen', 'furniture']):
            audiences.append('homeowners')
        elif any(keyword in title for keyword in ['book', 'kindle']):
            audiences.append('readers')
        
        return audiences if audiences else ['general']
    
    def _estimate_deal_duration(self, deal_type: str) -> Optional[datetime]:
        """تقدير مدة العرض"""
        now = datetime.now()
        
        duration_map = {
            'lightning': timedelta(hours=6),
            'daily': timedelta(days=1),
            'weekly': timedelta(days=7),
            'clearance': timedelta(days=30),
            'coupon': timedelta(days=14),
            'other': timedelta(days=3)
        }
        
        duration = duration_map.get(deal_type, timedelta(days=1))
        return now + duration
    
    def _is_significant_deal(self, deal_info: Dict[str, Any]) -> bool:
        """فحص إذا كان العرض مهماً بما يكفي للنشر"""
        quality_score = deal_info.get('quality_score', 0)
        discount_percentage = deal_info.get('discount_percentage', 0)
        
        # الحد الأدنى للجودة
        if quality_score < 4.0:
            return False
        
        # الحد الأدنى للخصم
        if discount_percentage < self.min_discount:
            return False
        
        # فحص السعر
        price = deal_info.get('deal_price', 0)
        if price < self.min_price or price > self.max_price:
            return False
        
        return True
    
    def compare_deals(self, deals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        مقارنة وترتيب العروض
        
        Args:
            deals: قائمة العروض
            
        Returns:
            العروض مرتبة حسب الأولوية
        """
        try:
            # ترتيب حسب نقاط الجودة ونسبة الخصم
            sorted_deals = sorted(deals, 
                                key=lambda x: (x.get('quality_score', 0), 
                                             x.get('discount_percentage', 0)), 
                                reverse=True)
            
            # إضافة ترتيب الأولوية
            for i, deal in enumerate(sorted_deals):
                deal['priority_rank'] = i + 1
                deal['is_top_deal'] = i < 5  # أفضل 5 عروض
            
            return sorted_deals
            
        except Exception as e:
            self.logger.error(f"خطأ في مقارنة العروض: {e}")
            return deals
    
    def filter_duplicate_deals(self, deals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        فلترة العروض المكررة
        
        Args:
            deals: قائمة العروض
            
        Returns:
            العروض بدون تكرار
        """
        seen_asins = set()
        unique_deals = []
        
        for deal in deals:
            asin = deal.get('asin')
            if asin and asin not in seen_asins:
                seen_asins.add(asin)
                unique_deals.append(deal)
        
        return unique_deals
    
    def generate_deal_summary(self, deal: Dict[str, Any]) -> Dict[str, str]:
        """
        إنشاء ملخص للعرض
        
        Args:
            deal: معلومات العرض
            
        Returns:
            ملخص العرض
        """
        try:
            analysis = deal.get('analysis_metadata', {})
            
            summary = {
                'title': self._generate_deal_title(deal),
                'description': self._generate_deal_description(deal),
                'urgency_message': self._generate_urgency_message(deal),
                'value_proposition': self._generate_value_proposition(deal),
                'recommendation': self._generate_recommendation(deal)
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء ملخص العرض: {e}")
            return {}
    
    def _generate_deal_title(self, deal: Dict[str, Any]) -> str:
        """إنشاء عنوان للعرض"""
        discount = deal.get('discount_percentage', 0)
        deal_type = deal.get('deal_type', 'other')
        
        if deal_type == 'lightning':
            return f"🔥 عرض خاطف - خصم {discount}%"
        elif deal_type == 'daily':
            return f"⭐ عرض اليوم - خصم {discount}%"
        elif deal_type == 'clearance':
            return f"🏷️ عرض تصفية - خصم {discount}%"
        else:
            return f"💰 عرض مميز - خصم {discount}%"
    
    def _generate_deal_description(self, deal: Dict[str, Any]) -> str:
        """إنشاء وصف للعرض"""
        original_price = deal.get('original_price', 0)
        deal_price = deal.get('deal_price', 0)
        savings = original_price - deal_price
        
        return f"وفر {savings:.0f} ريال على هذا المنتج المميز!"
    
    def _generate_urgency_message(self, deal: Dict[str, Any]) -> str:
        """إنشاء رسالة الإلحاح"""
        analysis = deal.get('analysis_metadata', {})
        urgency = analysis.get('urgency_level', 'low')
        
        if urgency == 'high':
            return "⚡ عرض محدود - احصل عليه الآن قبل انتهاء الكمية!"
        elif urgency == 'medium':
            return "⏰ عرض لفترة محدودة - لا تفوت الفرصة!"
        else:
            return "🛒 عرض رائع - اطلبه الآن!"
    
    def _generate_value_proposition(self, deal: Dict[str, Any]) -> str:
        """إنشاء عرض القيمة"""
        quality_score = deal.get('quality_score', 0)
        
        if quality_score >= 8:
            return "منتج عالي الجودة بسعر ممتاز"
        elif quality_score >= 6:
            return "قيمة رائعة مقابل السعر"
        else:
            return "فرصة جيدة للتوفير"
    
    def _generate_recommendation(self, deal: Dict[str, Any]) -> str:
        """إنشاء التوصية"""
        analysis = deal.get('analysis_metadata', {})
        strength = analysis.get('deal_strength', 'fair')
        
        if strength == 'excellent':
            return "🌟 موصى به بشدة - عرض استثنائي!"
        elif strength == 'very_good':
            return "👍 موصى به - عرض ممتاز!"
        elif strength == 'good':
            return "✅ عرض جيد يستحق النظر"
        else:
            return "💡 عرض مناسب للمهتمين"

