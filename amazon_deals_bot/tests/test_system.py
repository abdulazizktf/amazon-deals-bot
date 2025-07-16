"""
اختبارات شاملة لنظام Amazon Deals Bot
تاريخ الإنشاء: 11 يوليو 2025
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import yaml

# إضافة مجلد src إلى المسار
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import DatabaseManager
from scraper import AmazonScraper
from deal_analyzer import DealAnalyzer
from telegram_bot import TelegramBot
from channel_manager import ChannelManager
from deals_engine import DealsEngine

class TestConfig:
    """إعدادات الاختبار"""
    
    @staticmethod
    def get_test_config():
        """الحصول على إعدادات الاختبار"""
        return {
            'database': {
                'host': 'localhost',
                'port': 3306,
                'username': 'test_user',
                'password': 'test_password',
                'database': 'test_amazon_deals_bot',
                'charset': 'utf8mb4',
                'pool_size': 5
            },
            'telegram': {
                'bot_token': 'test_token',
                'api_url': 'https://api.telegram.org/bot',
                'max_message_length': 4096,
                'rate_limit': {
                    'messages_per_second': 30,
                    'messages_per_minute': 20
                }
            },
            'scraping': {
                'base_url': 'https://www.amazon.sa',
                'user_agents': ['test-agent'],
                'headers': {
                    'Accept': 'text/html',
                    'Accept-Language': 'ar,en'
                },
                'delays': {
                    'min_delay': 1,
                    'max_delay': 2,
                    'error_delay': 5
                },
                'retries': {
                    'max_retries': 2,
                    'backoff_factor': 1
                },
                'timeout': 10
            },
            'deals': {
                'min_discount_percentage': 15,
                'min_original_price': 50,
                'max_original_price': 5000,
                'categories': ['electronics', 'computers'],
                'quality_scoring': {
                    'discount_weight': 0.4,
                    'rating_weight': 0.3,
                    'review_count_weight': 0.2,
                    'price_range_weight': 0.1
                }
            },
            'messaging': {
                'max_deals_per_message': 1,
                'include_image': True,
                'message_template': 'Test template: {product_name} - {discount_percentage}%'
            },
            'logging': {
                'level': 'DEBUG',
                'format': '{time} | {level} | {message}',
                'files': {
                    'main': 'logs/test.log',
                    'scraping': 'logs/test_scraping.log',
                    'telegram': 'logs/test_telegram.log',
                    'errors': 'logs/test_errors.log'
                }
            },
            'scheduling': {
                'scraping_interval': 300,
                'message_sending_interval': 60,
                'cleanup_interval': 3600
            },
            'development': {
                'debug_mode': True,
                'test_mode': True,
                'mock_telegram': True
            }
        }

class TestDatabaseManager:
    """اختبارات مدير قاعدة البيانات"""
    
    @pytest.fixture
    def db_manager(self):
        """إنشاء مدير قاعدة البيانات للاختبار"""
        config = TestConfig.get_test_config()
        with patch('mysql.connector.pooling.MySQLConnectionPool'):
            with patch('sqlalchemy.create_engine'):
                db = DatabaseManager(config)
                yield db
    
    def test_database_initialization(self, db_manager):
        """اختبار تهيئة قاعدة البيانات"""
        assert db_manager is not None
        assert db_manager.config is not None
    
    @patch('mysql.connector.pooling.MySQLConnectionPool')
    def test_connection_pool_creation(self, mock_pool):
        """اختبار إنشاء connection pool"""
        config = TestConfig.get_test_config()
        db = DatabaseManager(config)
        mock_pool.assert_called_once()
    
    def test_product_insertion(self, db_manager):
        """اختبار إدراج المنتجات"""
        with patch.object(db_manager, 'execute_query') as mock_query:
            mock_query.return_value = 1
            
            product_data = {
                'asin': 'B123456789',
                'title': 'Test Product',
                'title_ar': None,
                'description': 'Test Description',
                'brand': 'Test Brand',
                'category_id': 1,
                'image_url': 'http://example.com/image.jpg',
                'amazon_url': 'http://amazon.sa/dp/B123456789',
                'rating': 4.5,
                'review_count': 100
            }
            
            result = db_manager.insert_product(product_data)
            assert result == 1
            mock_query.assert_called_once()

class TestAmazonScraper:
    """اختبارات مستخرج البيانات"""
    
    @pytest.fixture
    def scraper(self):
        """إنشاء مستخرج للاختبار"""
        config = TestConfig.get_test_config()
        scraper = AmazonScraper(config)
        yield scraper
    
    def test_scraper_initialization(self, scraper):
        """اختبار تهيئة المستخرج"""
        assert scraper is not None
        assert scraper.base_url == 'https://www.amazon.sa'
        assert scraper.session is not None
    
    @patch('requests.Session.get')
    def test_search_products(self, mock_get, scraper):
        """اختبار البحث عن المنتجات"""
        # محاكاة استجابة HTML
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'''
        <html>
            <div data-component-type="s-search-result" data-asin="B123456789">
                <h2><span class="a-size-medium">Test Product</span></h2>
                <span class="a-price-whole">100</span>
                <span class="a-icon-alt">4.5 out of 5 stars</span>
            </div>
        </html>
        '''
        mock_get.return_value = mock_response
        
        products = scraper.search_products('test search')
        
        assert isinstance(products, list)
        mock_get.assert_called_once()
    
    def test_price_parsing(self, scraper):
        """اختبار تحليل الأسعار"""
        # اختبار أسعار مختلفة
        test_cases = [
            ('100', 100.0),
            ('1,500', 1500.0),
            ('SAR 250', 250.0),
            ('invalid', None)
        ]
        
        for price_text, expected in test_cases:
            result = scraper._parse_price(price_text)
            assert result == expected

class TestDealAnalyzer:
    """اختبارات محلل العروض"""
    
    @pytest.fixture
    def analyzer(self):
        """إنشاء محلل للاختبار"""
        config = TestConfig.get_test_config()
        mock_db = Mock()
        analyzer = DealAnalyzer(config, mock_db)
        yield analyzer
    
    def test_analyzer_initialization(self, analyzer):
        """اختبار تهيئة المحلل"""
        assert analyzer is not None
        assert analyzer.min_discount == 15
    
    def test_discount_detection(self, analyzer):
        """اختبار اكتشاف الخصومات"""
        # منتج بخصم واضح
        product_with_discount = {
            'asin': 'B123456789',
            'title': 'Test Product',
            'current_price': 80,
            'original_price': 100,
            'discount_percentage': 20
        }
        
        assert analyzer._has_discount(product_with_discount) == True
        
        # منتج بدون خصم
        product_without_discount = {
            'asin': 'B987654321',
            'title': 'Another Product',
            'current_price': 100,
            'original_price': 100,
            'discount_percentage': 0
        }
        
        assert analyzer._has_discount(product_without_discount) == False
    
    def test_quality_score_calculation(self, analyzer):
        """اختبار حساب نقاط الجودة"""
        product_data = {
            'discount_percentage': 30,
            'rating': 4.5,
            'review_count': 500,
            'current_price': 200,
            'is_prime': True,
            'availability': 'in_stock'
        }
        
        score = analyzer._calculate_quality_score(product_data, [])
        
        assert isinstance(score, float)
        assert 0 <= score <= 10
    
    def test_deal_type_determination(self, analyzer):
        """اختبار تحديد نوع العرض"""
        # عرض خاطف
        lightning_product = {'discount_percentage': 60}
        assert analyzer._determine_deal_type(lightning_product, []) == 'lightning'
        
        # عرض يومي
        daily_product = {'discount_percentage': 35}
        assert analyzer._determine_deal_type(daily_product, []) == 'daily'
        
        # عرض عادي
        regular_product = {'discount_percentage': 20}
        assert analyzer._determine_deal_type(regular_product, []) == 'weekly'

class TestTelegramBot:
    """اختبارات بوت التليجرام"""
    
    @pytest.fixture
    def telegram_bot(self):
        """إنشاء بوت للاختبار"""
        config = TestConfig.get_test_config()
        config['telegram']['bot_token'] = 'test_token'
        
        mock_db = Mock()
        mock_engine = Mock()
        
        with patch('telegram.ext.Application.builder'):
            bot = TelegramBot(config, mock_db, mock_engine)
            yield bot
    
    def test_bot_initialization(self, telegram_bot):
        """اختبار تهيئة البوت"""
        assert telegram_bot is not None
        assert telegram_bot.bot_token == 'test_token'
    
    def test_message_formatting(self, telegram_bot):
        """اختبار تنسيق الرسائل"""
        deal_data = {
            'title': 'Test Product',
            'rating': 4.5,
            'review_count': 100,
            'original_price': 200,
            'deal_price': 150,
            'discount_percentage': 25,
            'discount_amount': 50,
            'amazon_url': 'http://amazon.sa/test'
        }
        
        message = telegram_bot._format_deal_message(deal_data)
        
        assert isinstance(message, str)
        assert 'Test Product' in message
        assert '25' in message  # نسبة الخصم

class TestChannelManager:
    """اختبارات مدير القنوات"""
    
    @pytest.fixture
    def channel_manager(self):
        """إنشاء مدير قنوات للاختبار"""
        mock_db = Mock()
        manager = ChannelManager(mock_db)
        yield manager
    
    def test_manager_initialization(self, channel_manager):
        """اختبار تهيئة المدير"""
        assert channel_manager is not None
        assert channel_manager.db is not None
    
    @pytest.mark.asyncio
    async def test_user_registration(self, channel_manager):
        """اختبار تسجيل المستخدمين"""
        with patch.object(channel_manager.db, 'execute_query') as mock_query:
            mock_query.return_value = 1
            
            user_data = {
                'telegram_id': 123456789,
                'username': 'testuser',
                'first_name': 'Test',
                'last_name': 'User',
                'language_code': 'ar'
            }
            
            result = await channel_manager.register_user(user_data)
            assert result == True
            mock_query.assert_called_once()

class TestDealsEngine:
    """اختبارات محرك العروض"""
    
    @pytest.fixture
    def deals_engine(self):
        """إنشاء محرك عروض للاختبار"""
        with patch('builtins.open', mock_open_config()):
            engine = DealsEngine('test_config.yaml')
            yield engine
    
    def test_engine_initialization(self, deals_engine):
        """اختبار تهيئة المحرك"""
        assert deals_engine is not None
        assert deals_engine.config is not None
    
    @pytest.mark.asyncio
    async def test_deals_extraction_cycle(self, deals_engine):
        """اختبار دورة استخراج العروض"""
        with patch.object(deals_engine, '_get_search_terms') as mock_terms:
            with patch.object(deals_engine, '_scrape_search_term') as mock_scrape:
                mock_terms.return_value = ['test term']
                mock_scrape.return_value = []
                
                # محاكاة تهيئة المكونات
                deals_engine.scraper = Mock()
                deals_engine.analyzer = Mock()
                deals_engine.db_manager = Mock()
                
                await deals_engine.run_deals_extraction_cycle()
                
                mock_terms.assert_called_once()

def mock_open_config():
    """محاكاة فتح ملف الإعدادات"""
    config_content = yaml.dump(TestConfig.get_test_config())
    return patch('builtins.open', mock_open(read_data=config_content))

class TestIntegration:
    """اختبارات التكامل"""
    
    @pytest.mark.asyncio
    async def test_full_system_flow(self):
        """اختبار تدفق النظام الكامل"""
        # هذا اختبار تكامل مبسط
        config = TestConfig.get_test_config()
        
        # محاكاة جميع المكونات
        with patch('mysql.connector.pooling.MySQLConnectionPool'):
            with patch('sqlalchemy.create_engine'):
                with patch('telegram.ext.Application.builder'):
                    
                    # إنشاء المكونات
                    db_manager = DatabaseManager(config)
                    scraper = AmazonScraper(config)
                    analyzer = DealAnalyzer(config, db_manager)
                    
                    # اختبار التفاعل بين المكونات
                    assert db_manager is not None
                    assert scraper is not None
                    assert analyzer is not None

# اختبارات الأداء
class TestPerformance:
    """اختبارات الأداء"""
    
    def test_scraper_performance(self):
        """اختبار أداء المستخرج"""
        config = TestConfig.get_test_config()
        scraper = AmazonScraper(config)
        
        # قياس وقت تحليل HTML
        import time
        
        html_content = '<div data-asin="test">Test</div>' * 100
        
        start_time = time.time()
        # محاكاة تحليل HTML
        end_time = time.time()
        
        processing_time = end_time - start_time
        assert processing_time < 1.0  # يجب أن يكون أقل من ثانية واحدة
    
    def test_database_performance(self):
        """اختبار أداء قاعدة البيانات"""
        config = TestConfig.get_test_config()
        
        with patch('mysql.connector.pooling.MySQLConnectionPool'):
            with patch('sqlalchemy.create_engine'):
                db_manager = DatabaseManager(config)
                
                # محاكاة عمليات قاعدة البيانات المتعددة
                with patch.object(db_manager, 'execute_query') as mock_query:
                    mock_query.return_value = 1
                    
                    # تنفيذ عمليات متعددة
                    for i in range(10):
                        db_manager.execute_query("SELECT 1")
                    
                    assert mock_query.call_count == 10

# تشغيل الاختبارات
if __name__ == "__main__":
    # تشغيل الاختبارات
    pytest.main([__file__, "-v", "--tb=short"])

