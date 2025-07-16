"""
وحدة استخراج البيانات من أمازون السعودية
تاريخ الإنشاء: 11 يوليو 2025
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import re
from typing import Dict, List, Optional, Any, Tuple
import logging
from urllib.parse import urljoin, urlparse, parse_qs
from fake_useragent import UserAgent
from retrying import retry
import json
from datetime import datetime
import os

class AmazonScraper:
    """مستخرج البيانات من أمازون السعودية"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        تهيئة المستخرج
        
        Args:
            config: إعدادات النظام
        """
        self.config = config
        self.scraping_config = config['scraping']
        self.base_url = self.scraping_config['base_url']
        self.logger = logging.getLogger(__name__)
        
        # إعداد User Agent
        self.ua = UserAgent()
        self.user_agents = self.scraping_config.get('user_agents', [])
        
        # إعداد الجلسة
        self.session = requests.Session()
        self._setup_session()
        
        # إعدادات التأخير
        self.min_delay = self.scraping_config['delays']['min_delay']
        self.max_delay = self.scraping_config['delays']['max_delay']
        self.error_delay = self.scraping_config['delays']['error_delay']
        
        # إعدادات إعادة المحاولة
        self.max_retries = self.scraping_config['retries']['max_retries']
        self.backoff_factor = self.scraping_config['retries']['backoff_factor']
        
        # قوائم البحث
        self.search_terms = self._load_search_terms()
        
    def _setup_session(self):
        """إعداد جلسة HTTP"""
        headers = self.scraping_config['headers'].copy()
        headers['User-Agent'] = self._get_random_user_agent()
        
        self.session.headers.update(headers)
        self.session.timeout = self.scraping_config['timeout']
        
        # إعداد البروكسي إذا كان مفعلاً
        if self.config.get('proxy', {}).get('enabled', False):
            self._setup_proxy()
    
    def _setup_proxy(self):
        """إعداد البروكسي"""
        proxy_config = self.config['proxy']
        if proxy_config.get('proxies'):
            proxy = random.choice(proxy_config['proxies'])
            self.session.proxies = {
                'http': proxy,
                'https': proxy
            }
            self.logger.info(f"تم إعداد البروكسي: {proxy}")
    
    def _get_random_user_agent(self) -> str:
        """الحصول على User Agent عشوائي"""
        if self.user_agents:
            return random.choice(self.user_agents)
        else:
            return self.ua.random
    
    def _load_search_terms(self) -> List[str]:
        """تحميل مصطلحات البحث"""
        # يمكن تحميلها من ملف أو قاعدة البيانات
        return [
            "electronics deals",
            "laptop offers",
            "smartphone discount",
            "home appliances sale",
            "fashion deals",
            "books discount",
            "sports equipment offers"
        ]
    
    def _random_delay(self):
        """تأخير عشوائي بين الطلبات"""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)
    
    def _error_delay(self):
        """تأخير عند حدوث خطأ"""
        time.sleep(self.error_delay)
    
    @retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000)
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[requests.Response]:
        """
        إرسال طلب HTTP مع إعادة المحاولة
        
        Args:
            url: الرابط
            params: معاملات الطلب
            
        Returns:
            استجابة HTTP أو None
        """
        try:
            # تحديث User Agent
            self.session.headers['User-Agent'] = self._get_random_user_agent()
            
            # إرسال الطلب
            response = self.session.get(url, params=params)
            
            # فحص حالة الاستجابة
            if response.status_code == 200:
                return response
            elif response.status_code == 503:
                self.logger.warning("تم حظر الطلب (503) - إعادة المحاولة")
                self._error_delay()
                raise Exception("Service Unavailable")
            elif response.status_code == 429:
                self.logger.warning("تم تجاوز حد الطلبات (429) - إعادة المحاولة")
                self._error_delay()
                raise Exception("Rate Limited")
            else:
                self.logger.error(f"خطأ في الطلب: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"خطأ في الشبكة: {e}")
            self._error_delay()
            raise
    
    def search_products(self, search_term: str, page: int = 1) -> List[Dict[str, Any]]:
        """
        البحث عن المنتجات
        
        Args:
            search_term: مصطلح البحث
            page: رقم الصفحة
            
        Returns:
            قائمة المنتجات
        """
        search_url = f"{self.base_url}/s"
        params = {
            'k': search_term,
            'page': page,
            'ref': 'sr_pg_' + str(page)
        }
        
        try:
            response = self._make_request(search_url, params)
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            products = self._parse_search_results(soup)
            
            self.logger.info(f"تم العثور على {len(products)} منتج للبحث: {search_term}")
            return products
            
        except Exception as e:
            self.logger.error(f"خطأ في البحث عن المنتجات: {e}")
            return []
        finally:
            self._random_delay()
    
    def _parse_search_results(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        تحليل نتائج البحث
        
        Args:
            soup: محتوى HTML المحلل
            
        Returns:
            قائمة المنتجات
        """
        products = []
        
        # البحث عن عناصر المنتجات
        product_containers = soup.find_all('div', {'data-component-type': 's-search-result'})
        
        for container in product_containers:
            try:
                product = self._extract_product_info(container)
                if product and self._is_valid_product(product):
                    products.append(product)
            except Exception as e:
                self.logger.debug(f"خطأ في تحليل منتج: {e}")
                continue
        
        return products
    
    def _extract_product_info(self, container) -> Optional[Dict[str, Any]]:
        """
        استخراج معلومات المنتج من العنصر
        
        Args:
            container: عنصر HTML للمنتج
            
        Returns:
            معلومات المنتج أو None
        """
        try:
            # ASIN
            asin = container.get('data-asin')
            if not asin:
                return None
            
            # العنوان
            title_element = container.find('h2', class_='a-size-mini')
            if not title_element:
                title_element = container.find('span', class_='a-size-medium')
            
            title = title_element.get_text(strip=True) if title_element else ""
            
            # الرابط
            link_element = container.find('h2').find('a') if container.find('h2') else None
            product_url = urljoin(self.base_url, link_element['href']) if link_element else ""
            
            # السعر
            price_info = self._extract_price_info(container)
            
            # التقييم
            rating_info = self._extract_rating_info(container)
            
            # الصورة
            image_element = container.find('img', class_='s-image')
            image_url = image_element.get('src', '') if image_element else ""
            
            # معلومات البائع
            seller_info = self._extract_seller_info(container)
            
            product = {
                'asin': asin,
                'title': title,
                'amazon_url': product_url,
                'image_url': image_url,
                'current_price': price_info.get('current_price'),
                'original_price': price_info.get('original_price'),
                'currency': price_info.get('currency', 'SAR'),
                'discount_percentage': price_info.get('discount_percentage'),
                'rating': rating_info.get('rating'),
                'review_count': rating_info.get('review_count'),
                'seller_name': seller_info.get('seller_name'),
                'is_prime': seller_info.get('is_prime', False),
                'availability': seller_info.get('availability', 'unknown'),
                'scraped_at': datetime.now()
            }
            
            return product
            
        except Exception as e:
            self.logger.debug(f"خطأ في استخراج معلومات المنتج: {e}")
            return None
    
    def _extract_price_info(self, container) -> Dict[str, Any]:
        """استخراج معلومات السعر"""
        price_info = {
            'current_price': None,
            'original_price': None,
            'currency': 'SAR',
            'discount_percentage': None
        }
        
        try:
            # البحث عن السعر الحالي
            current_price_element = container.find('span', class_='a-price-whole')
            if current_price_element:
                price_text = current_price_element.get_text(strip=True)
                price_info['current_price'] = self._parse_price(price_text)
            
            # البحث عن السعر الأصلي (المشطوب)
            original_price_element = container.find('span', class_='a-price-was')
            if not original_price_element:
                original_price_element = container.find('span', class_='a-text-price')
            
            if original_price_element:
                price_text = original_price_element.get_text(strip=True)
                price_info['original_price'] = self._parse_price(price_text)
            
            # حساب نسبة الخصم
            if price_info['current_price'] and price_info['original_price']:
                current = price_info['current_price']
                original = price_info['original_price']
                if original > current:
                    discount = ((original - current) / original) * 100
                    price_info['discount_percentage'] = round(discount, 2)
            
            # البحث عن نسبة الخصم المعروضة
            discount_element = container.find('span', class_='a-badge-text')
            if discount_element and '%' in discount_element.get_text():
                discount_text = discount_element.get_text(strip=True)
                discount_match = re.search(r'(\d+)%', discount_text)
                if discount_match:
                    price_info['discount_percentage'] = int(discount_match.group(1))
        
        except Exception as e:
            self.logger.debug(f"خطأ في استخراج السعر: {e}")
        
        return price_info
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        """تحليل نص السعر وتحويله لرقم"""
        try:
            # إزالة العملة والرموز
            price_clean = re.sub(r'[^\d.,]', '', price_text)
            price_clean = price_clean.replace(',', '')
            
            if price_clean:
                return float(price_clean)
        except:
            pass
        
        return None
    
    def _extract_rating_info(self, container) -> Dict[str, Any]:
        """استخراج معلومات التقييم"""
        rating_info = {
            'rating': None,
            'review_count': None
        }
        
        try:
            # التقييم
            rating_element = container.find('span', class_='a-icon-alt')
            if rating_element:
                rating_text = rating_element.get_text(strip=True)
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    rating_info['rating'] = float(rating_match.group(1))
            
            # عدد المراجعات
            review_element = container.find('span', class_='a-size-base')
            if review_element and '(' in review_element.get_text():
                review_text = review_element.get_text(strip=True)
                review_match = re.search(r'\((\d+(?:,\d+)*)\)', review_text)
                if review_match:
                    review_count = review_match.group(1).replace(',', '')
                    rating_info['review_count'] = int(review_count)
        
        except Exception as e:
            self.logger.debug(f"خطأ في استخراج التقييم: {e}")
        
        return rating_info
    
    def _extract_seller_info(self, container) -> Dict[str, Any]:
        """استخراج معلومات البائع"""
        seller_info = {
            'seller_name': None,
            'is_prime': False,
            'availability': 'unknown'
        }
        
        try:
            # فحص Prime
            prime_element = container.find('span', class_='a-icon-prime')
            seller_info['is_prime'] = prime_element is not None
            
            # حالة التوفر
            availability_element = container.find('span', class_='a-size-base-plus')
            if availability_element:
                availability_text = availability_element.get_text(strip=True).lower()
                if 'متوفر' in availability_text or 'in stock' in availability_text:
                    seller_info['availability'] = 'in_stock'
                elif 'غير متوفر' in availability_text or 'out of stock' in availability_text:
                    seller_info['availability'] = 'out_of_stock'
        
        except Exception as e:
            self.logger.debug(f"خطأ في استخراج معلومات البائع: {e}")
        
        return seller_info
    
    def _is_valid_product(self, product: Dict[str, Any]) -> bool:
        """
        فحص صحة بيانات المنتج
        
        Args:
            product: بيانات المنتج
            
        Returns:
            True إذا كان المنتج صالحاً
        """
        # فحص الحقول الأساسية
        if not product.get('asin') or not product.get('title'):
            return False
        
        # فحص وجود سعر
        if not product.get('current_price'):
            return False
        
        # فحص نطاق السعر
        price = product['current_price']
        min_price = self.config['deals']['min_original_price']
        max_price = self.config['deals']['max_original_price']
        
        if price < min_price or price > max_price:
            return False
        
        return True
    
    def get_product_details(self, asin: str) -> Optional[Dict[str, Any]]:
        """
        الحصول على تفاصيل منتج محدد
        
        Args:
            asin: معرف أمازون للمنتج
            
        Returns:
            تفاصيل المنتج أو None
        """
        product_url = f"{self.base_url}/dp/{asin}"
        
        try:
            response = self._make_request(product_url)
            if not response:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            product_details = self._parse_product_page(soup, asin)
            
            return product_details
            
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على تفاصيل المنتج {asin}: {e}")
            return None
        finally:
            self._random_delay()
    
    def _parse_product_page(self, soup: BeautifulSoup, asin: str) -> Dict[str, Any]:
        """تحليل صفحة المنتج"""
        product = {'asin': asin}
        
        try:
            # العنوان
            title_element = soup.find('span', {'id': 'productTitle'})
            product['title'] = title_element.get_text(strip=True) if title_element else ""
            
            # الوصف
            description_element = soup.find('div', {'id': 'feature-bullets'})
            if description_element:
                bullets = description_element.find_all('span', class_='a-list-item')
                description = ' '.join([bullet.get_text(strip=True) for bullet in bullets])
                product['description'] = description[:1000]  # تحديد الطول
            
            # العلامة التجارية
            brand_element = soup.find('a', {'id': 'bylineInfo'})
            if brand_element:
                product['brand'] = brand_element.get_text(strip=True)
            
            # الصور
            image_element = soup.find('img', {'id': 'landingImage'})
            if image_element:
                product['image_url'] = image_element.get('src', '')
            
            # السعر والعروض
            price_info = self._extract_detailed_price_info(soup)
            product.update(price_info)
            
            # التقييم المفصل
            rating_info = self._extract_detailed_rating_info(soup)
            product.update(rating_info)
            
        except Exception as e:
            self.logger.error(f"خطأ في تحليل صفحة المنتج: {e}")
        
        return product
    
    def _extract_detailed_price_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """استخراج معلومات السعر المفصلة من صفحة المنتج"""
        price_info = {}
        
        try:
            # السعر الحالي
            current_price_element = soup.find('span', class_='a-price-whole')
            if current_price_element:
                price_text = current_price_element.get_text(strip=True)
                price_info['current_price'] = self._parse_price(price_text)
            
            # السعر الأصلي
            original_price_element = soup.find('span', class_='a-price-was')
            if original_price_element:
                price_text = original_price_element.get_text(strip=True)
                price_info['original_price'] = self._parse_price(price_text)
            
            # معلومات العرض
            deal_element = soup.find('span', {'id': 'dealBadgeDisplayText'})
            if deal_element:
                deal_text = deal_element.get_text(strip=True)
                price_info['deal_type'] = deal_text
        
        except Exception as e:
            self.logger.debug(f"خطأ في استخراج السعر المفصل: {e}")
        
        return price_info
    
    def _extract_detailed_rating_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """استخراج معلومات التقييم المفصلة"""
        rating_info = {}
        
        try:
            # التقييم
            rating_element = soup.find('span', class_='a-icon-alt')
            if rating_element:
                rating_text = rating_element.get_text(strip=True)
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    rating_info['rating'] = float(rating_match.group(1))
            
            # عدد المراجعات
            review_element = soup.find('span', {'id': 'acrCustomerReviewText'})
            if review_element:
                review_text = review_element.get_text(strip=True)
                review_match = re.search(r'(\d+(?:,\d+)*)', review_text)
                if review_match:
                    review_count = review_match.group(1).replace(',', '')
                    rating_info['review_count'] = int(review_count)
        
        except Exception as e:
            self.logger.debug(f"خطأ في استخراج التقييم المفصل: {e}")
        
        return rating_info
    
    def scrape_deals_page(self) -> List[Dict[str, Any]]:
        """استخراج العروض من صفحة العروض الخاصة"""
        deals_url = f"{self.base_url}/deals"
        
        try:
            response = self._make_request(deals_url)
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            deals = self._parse_deals_page(soup)
            
            self.logger.info(f"تم العثور على {len(deals)} عرض من صفحة العروض")
            return deals
            
        except Exception as e:
            self.logger.error(f"خطأ في استخراج صفحة العروض: {e}")
            return []
        finally:
            self._random_delay()
    
    def _parse_deals_page(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """تحليل صفحة العروض"""
        deals = []
        
        # البحث عن عناصر العروض
        deal_containers = soup.find_all('div', {'data-testid': 'deal-card'})
        
        for container in deal_containers:
            try:
                deal = self._extract_deal_info(container)
                if deal and self._is_valid_deal(deal):
                    deals.append(deal)
            except Exception as e:
                self.logger.debug(f"خطأ في تحليل عرض: {e}")
                continue
        
        return deals
    
    def _extract_deal_info(self, container) -> Optional[Dict[str, Any]]:
        """استخراج معلومات العرض"""
        try:
            # الحصول على ASIN من الرابط
            link_element = container.find('a')
            if not link_element:
                return None
            
            href = link_element.get('href', '')
            asin_match = re.search(r'/dp/([A-Z0-9]{10})', href)
            if not asin_match:
                return None
            
            asin = asin_match.group(1)
            
            # استخراج معلومات المنتج
            product_info = self._extract_product_info(container)
            if not product_info:
                return None
            
            # إضافة معلومات العرض
            deal_info = {
                'deal_type': 'daily',  # افتراضي
                'deal_url': urljoin(self.base_url, href),
                'scraped_at': datetime.now()
            }
            
            product_info.update(deal_info)
            return product_info
            
        except Exception as e:
            self.logger.debug(f"خطأ في استخراج معلومات العرض: {e}")
            return None
    
    def _is_valid_deal(self, deal: Dict[str, Any]) -> bool:
        """فحص صحة العرض"""
        # فحص وجود خصم
        discount = deal.get('discount_percentage')
        if not discount:
            return False
        
        # فحص نسبة الخصم الدنيا
        min_discount = self.config['deals']['min_discount_percentage']
        if discount < min_discount:
            return False
        
        # فحص صحة المنتج
        return self._is_valid_product(deal)
    
    def save_html_for_debug(self, content: str, filename: str):
        """حفظ HTML للتشخيص"""
        if self.config.get('development', {}).get('save_html_files', False):
            debug_dir = 'data/debug_html'
            os.makedirs(debug_dir, exist_ok=True)
            
            filepath = os.path.join(debug_dir, f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.debug(f"تم حفظ HTML للتشخيص: {filepath}")
    
    def get_categories_to_scrape(self) -> List[str]:
        """الحصول على قائمة الفئات للاستخراج"""
        return self.config['deals']['categories']
    
    def close(self):
        """إغلاق الجلسة"""
        if self.session:
            self.session.close()
            self.logger.info("تم إغلاق جلسة الاستخراج")

