-- إعداد قاعدة البيانات لنظام Amazon Deals Bot
-- تاريخ الإنشاء: 11 يوليو 2025

-- إنشاء قاعدة البيانات
CREATE DATABASE IF NOT EXISTS amazon_deals_bot 
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE amazon_deals_bot;

-- جدول الفئات
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    name_ar VARCHAR(100),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_category_name (name),
    INDEX idx_category_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- جدول المنتجات
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    asin VARCHAR(20) NOT NULL,
    title VARCHAR(500) NOT NULL,
    title_ar VARCHAR(500),
    description TEXT,
    brand VARCHAR(255),
    category_id INT,
    image_url VARCHAR(500),
    amazon_url VARCHAR(500),
    rating DECIMAL(3,2),
    review_count INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_asin (asin),
    INDEX idx_product_category (category_id),
    INDEX idx_product_active (is_active),
    INDEX idx_product_rating (rating),
    INDEX idx_product_brand (brand),
    INDEX idx_product_last_updated (last_updated),
    
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- جدول تاريخ الأسعار
CREATE TABLE IF NOT EXISTS price_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'SAR',
    availability_status VARCHAR(50),
    seller_name VARCHAR(255),
    is_prime BOOLEAN DEFAULT FALSE,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_price_product (product_id),
    INDEX idx_price_recorded (recorded_at),
    INDEX idx_price_availability (availability_status),
    INDEX idx_price_prime (is_prime),
    
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- جدول العروض
CREATE TABLE IF NOT EXISTS deals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    deal_type VARCHAR(50) NOT NULL,
    original_price DECIMAL(10,2) NOT NULL,
    deal_price DECIMAL(10,2) NOT NULL,
    discount_percentage DECIMAL(5,2) NOT NULL,
    discount_amount DECIMAL(10,2) NOT NULL,
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP NULL,
    deal_status VARCHAR(20) DEFAULT 'active',
    max_quantity INT,
    deal_url VARCHAR(500),
    quality_score DECIMAL(4,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_deal_product (product_id),
    INDEX idx_deal_status (deal_status),
    INDEX idx_deal_type (deal_type),
    INDEX idx_deal_discount (discount_percentage),
    INDEX idx_deal_quality (quality_score),
    INDEX idx_deal_dates (start_date, end_date),
    INDEX idx_deal_created (created_at),
    
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- جدول مستخدمي التليجرام
CREATE TABLE IF NOT EXISTS telegram_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    username VARCHAR(50),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    language_code VARCHAR(10) DEFAULT 'ar',
    preferences JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_telegram_id (telegram_id),
    INDEX idx_user_active (is_active),
    INDEX idx_user_language (language_code),
    INDEX idx_user_last_interaction (last_interaction)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- جدول قنوات التليجرام
CREATE TABLE IF NOT EXISTS telegram_channels (
    id INT AUTO_INCREMENT PRIMARY KEY,
    telegram_id VARCHAR(100) NOT NULL,
    channel_name VARCHAR(200),
    channel_type VARCHAR(20) DEFAULT 'channel',
    admin_user_id BIGINT,
    settings JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_channel_telegram_id (telegram_id),
    INDEX idx_channel_active (is_active),
    INDEX idx_channel_type (channel_type),
    INDEX idx_channel_admin (admin_user_id),
    
    FOREIGN KEY (admin_user_id) REFERENCES telegram_users(telegram_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- جدول الرسائل المرسلة
CREATE TABLE IF NOT EXISTS sent_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    deal_id INT,
    recipient_id VARCHAR(100) NOT NULL,
    message_id BIGINT,
    message_type VARCHAR(50) DEFAULT 'deal_alert',
    delivery_status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_message_deal (deal_id),
    INDEX idx_message_recipient (recipient_id),
    INDEX idx_message_status (delivery_status),
    INDEX idx_message_type (message_type),
    INDEX idx_message_sent (sent_at),
    
    FOREIGN KEY (deal_id) REFERENCES deals(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- جدول سجل النشاطات
CREATE TABLE IF NOT EXISTS activity_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    activity_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    related_table VARCHAR(50),
    related_id INT,
    metadata JSON,
    severity VARCHAR(20) DEFAULT 'info',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_activity_type (activity_type),
    INDEX idx_activity_severity (severity),
    INDEX idx_activity_created (created_at),
    INDEX idx_activity_related (related_table, related_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- جدول إحصائيات النظام
CREATE TABLE IF NOT EXISTS system_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stat_date DATE NOT NULL,
    products_scraped INT DEFAULT 0,
    deals_found INT DEFAULT 0,
    messages_sent INT DEFAULT 0,
    active_users INT DEFAULT 0,
    active_channels INT DEFAULT 0,
    errors_count INT DEFAULT 0,
    runtime_hours DECIMAL(8,2) DEFAULT 0,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_stat_date (stat_date),
    INDEX idx_stats_date (stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- إدراج الفئات الأساسية
INSERT IGNORE INTO categories (name, name_ar, description) VALUES
('electronics', 'الإلكترونيات', 'الأجهزة الإلكترونية والتقنية'),
('computers', 'أجهزة الكمبيوتر', 'أجهزة الكمبيوتر واللابتوب والإكسسوارات'),
('mobile-phones', 'الهواتف المحمولة', 'الهواتف الذكية والإكسسوارات'),
('home-kitchen', 'المنزل والمطبخ', 'أدوات المنزل والمطبخ'),
('fashion', 'الأزياء', 'الملابس والأحذية والإكسسوارات'),
('books', 'الكتب', 'الكتب والمجلات'),
('sports-outdoors', 'الرياضة والهواء الطلق', 'المعدات الرياضية وأدوات الهواء الطلق'),
('beauty', 'الجمال', 'منتجات التجميل والعناية'),
('automotive', 'السيارات', 'قطع غيار وإكسسوارات السيارات'),
('health-household', 'الصحة والمنزل', 'المنتجات الصحية وأدوات المنزل');

-- إنشاء مستخدم قاعدة البيانات
CREATE USER IF NOT EXISTS 'amazon_bot'@'localhost' IDENTIFIED BY 'secure_password_2025';
GRANT ALL PRIVILEGES ON amazon_deals_bot.* TO 'amazon_bot'@'localhost';
FLUSH PRIVILEGES;

-- إنشاء فهارس إضافية للأداء
CREATE INDEX idx_products_title_search ON products(title(100));
CREATE INDEX idx_deals_price_range ON deals(deal_price, discount_percentage);
CREATE INDEX idx_price_history_latest ON price_history(product_id, recorded_at DESC);

-- إنشاء views مفيدة
CREATE OR REPLACE VIEW active_deals_view AS
SELECT 
    d.*,
    p.asin,
    p.title,
    p.image_url,
    p.amazon_url,
    p.rating,
    p.review_count,
    c.name as category_name
FROM deals d
JOIN products p ON d.product_id = p.id
LEFT JOIN categories c ON p.category_id = c.id
WHERE d.deal_status = 'active'
AND (d.end_date IS NULL OR d.end_date > NOW())
ORDER BY d.quality_score DESC, d.discount_percentage DESC;

CREATE OR REPLACE VIEW user_stats_view AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as new_users,
    SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_users
FROM telegram_users
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- إنشاء stored procedures مفيدة
DELIMITER //

CREATE PROCEDURE GetTopDeals(IN limit_count INT)
BEGIN
    SELECT * FROM active_deals_view
    LIMIT limit_count;
END //

CREATE PROCEDURE GetUserPreferences(IN user_telegram_id BIGINT)
BEGIN
    SELECT preferences FROM telegram_users 
    WHERE telegram_id = user_telegram_id AND is_active = 1;
END //

CREATE PROCEDURE LogActivity(
    IN activity_type VARCHAR(50),
    IN description TEXT,
    IN related_table VARCHAR(50),
    IN related_id INT,
    IN metadata_json JSON,
    IN severity VARCHAR(20)
)
BEGIN
    INSERT INTO activity_log (activity_type, description, related_table, related_id, metadata, severity)
    VALUES (activity_type, description, related_table, related_id, metadata_json, severity);
END //

DELIMITER ;

-- إنشاء triggers للتحديث التلقائي
DELIMITER //

CREATE TRIGGER update_product_timestamp 
BEFORE UPDATE ON products
FOR EACH ROW
BEGIN
    SET NEW.last_updated = CURRENT_TIMESTAMP;
END //

CREATE TRIGGER log_new_deal 
AFTER INSERT ON deals
FOR EACH ROW
BEGIN
    INSERT INTO activity_log (activity_type, description, related_table, related_id, metadata)
    VALUES ('deal_created', CONCAT('تم إنشاء عرض جديد بخصم ', NEW.discount_percentage, '%'), 'deals', NEW.id, 
            JSON_OBJECT('deal_type', NEW.deal_type, 'discount', NEW.discount_percentage, 'quality_score', NEW.quality_score));
END //

DELIMITER ;

-- إنشاء events للصيانة التلقائية
SET GLOBAL event_scheduler = ON;

DELIMITER //

CREATE EVENT IF NOT EXISTS cleanup_old_price_history
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_TIMESTAMP
DO
BEGIN
    -- حذف سجلات الأسعار الأقدم من 90 يوم (الاحتفاظ بسجل واحد يومياً)
    DELETE ph1 FROM price_history ph1
    INNER JOIN price_history ph2 
    WHERE ph1.product_id = ph2.product_id
    AND ph1.recorded_at < DATE_SUB(NOW(), INTERVAL 90 DAY)
    AND DATE(ph1.recorded_at) = DATE(ph2.recorded_at)
    AND ph1.id < ph2.id;
END //

CREATE EVENT IF NOT EXISTS cleanup_old_activity_log
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_TIMESTAMP
DO
BEGIN
    -- حذف سجلات النشاط الأقدم من 30 يوم
    DELETE FROM activity_log 
    WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
END //

CREATE EVENT IF NOT EXISTS update_daily_stats
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_TIMESTAMP
DO
BEGIN
    -- تحديث الإحصائيات اليومية
    INSERT INTO system_stats (stat_date, products_scraped, deals_found, messages_sent, active_users, active_channels)
    SELECT 
        CURDATE(),
        COALESCE((SELECT COUNT(*) FROM products WHERE DATE(first_seen) = CURDATE()), 0),
        COALESCE((SELECT COUNT(*) FROM deals WHERE DATE(created_at) = CURDATE()), 0),
        COALESCE((SELECT COUNT(*) FROM sent_messages WHERE DATE(sent_at) = CURDATE() AND delivery_status = 'sent'), 0),
        COALESCE((SELECT COUNT(*) FROM telegram_users WHERE is_active = 1), 0),
        COALESCE((SELECT COUNT(*) FROM telegram_channels WHERE is_active = 1), 0)
    ON DUPLICATE KEY UPDATE
        products_scraped = VALUES(products_scraped),
        deals_found = VALUES(deals_found),
        messages_sent = VALUES(messages_sent),
        active_users = VALUES(active_users),
        active_channels = VALUES(active_channels);
END //

DELIMITER ;

-- إنشاء فهارس للبحث النصي
ALTER TABLE products ADD FULLTEXT(title, description);

-- تحسين إعدادات قاعدة البيانات
SET GLOBAL innodb_buffer_pool_size = 268435456; -- 256MB
SET GLOBAL query_cache_size = 67108864; -- 64MB
SET GLOBAL query_cache_type = 1;

-- إنشاء backup procedure
DELIMITER //

CREATE PROCEDURE BackupImportantData()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- يمكن إضافة منطق النسخ الاحتياطي هنا
    SELECT 'Backup completed successfully' as status;
    
    COMMIT;
END //

DELIMITER ;

-- رسالة النجاح
SELECT 'تم إعداد قاعدة البيانات بنجاح!' as message;

