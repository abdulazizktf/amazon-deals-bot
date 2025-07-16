#!/bin/bash

# ملف التشغيل السريع لنظام Amazon Deals Bot
# تاريخ الإنشاء: 11 يوليو 2025

set -e

# الألوان للإخراج
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# دوال المساعدة
print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    Amazon Deals Bot                          ║"
    echo "║              نظام AI للبحث عن العروض التلقائي              ║"
    echo "║                                                              ║"
    echo "║                   تاريخ الإنشاء: 11 يوليو 2025              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# فحص المتطلبات
check_requirements() {
    print_info "فحص المتطلبات..."
    
    # فحص Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 غير مثبت"
        exit 1
    fi
    
    # فحص pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 غير مثبت"
        exit 1
    fi
    
    # فحص Docker (اختياري)
    if command -v docker &> /dev/null; then
        print_success "Docker متوفر"
        DOCKER_AVAILABLE=true
    else
        print_warning "Docker غير متوفر - سيتم التشغيل المحلي فقط"
        DOCKER_AVAILABLE=false
    fi
    
    # فحص MySQL (للتشغيل المحلي)
    if command -v mysql &> /dev/null; then
        print_success "MySQL متوفر"
        MYSQL_AVAILABLE=true
    else
        print_warning "MySQL غير متوفر محلياً"
        MYSQL_AVAILABLE=false
    fi
    
    print_success "تم فحص المتطلبات"
}

# إعداد البيئة
setup_environment() {
    print_info "إعداد البيئة..."
    
    # إنشاء المجلدات المطلوبة
    mkdir -p logs data config tests
    
    # نسخ ملف البيئة إذا لم يكن موجوداً
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            print_warning "تم إنشاء ملف .env من المثال - يرجى تعديل القيم المطلوبة"
        else
            print_error "ملف .env.example غير موجود"
            exit 1
        fi
    fi
    
    # تثبيت المتطلبات Python
    if [ -f requirements.txt ]; then
        print_info "تثبيت متطلبات Python..."
        pip3 install -r requirements.txt
        print_success "تم تثبيت المتطلبات"
    else
        print_error "ملف requirements.txt غير موجود"
        exit 1
    fi
    
    print_success "تم إعداد البيئة"
}

# إعداد قاعدة البيانات
setup_database() {
    print_info "إعداد قاعدة البيانات..."
    
    if [ "$MYSQL_AVAILABLE" = true ]; then
        # إعداد قاعدة البيانات المحلية
        print_info "إعداد قاعدة البيانات المحلية..."
        
        # قراءة كلمة مرور MySQL
        read -s -p "أدخل كلمة مرور MySQL root: " MYSQL_ROOT_PASSWORD
        echo
        
        # تنفيذ ملف إعداد قاعدة البيانات
        if [ -f setup_database.sql ]; then
            mysql -u root -p"$MYSQL_ROOT_PASSWORD" < setup_database.sql
            print_success "تم إعداد قاعدة البيانات"
        else
            print_error "ملف setup_database.sql غير موجود"
            exit 1
        fi
    else
        print_warning "MySQL غير متوفر - يرجى إعداد قاعدة البيانات يدوياً"
    fi
}

# تشغيل الاختبارات
run_tests() {
    print_info "تشغيل الاختبارات..."
    
    if [ -f tests/test_system.py ]; then
        python3 -m pytest tests/ -v
        if [ $? -eq 0 ]; then
            print_success "نجحت جميع الاختبارات"
        else
            print_error "فشلت بعض الاختبارات"
            return 1
        fi
    else
        print_warning "ملفات الاختبار غير موجودة"
    fi
}

# تشغيل النظام
start_system() {
    print_info "بدء تشغيل النظام..."
    
    # فحص ملف الإعدادات
    if [ ! -f config/config.yaml ]; then
        print_error "ملف الإعدادات غير موجود: config/config.yaml"
        exit 1
    fi
    
    # تشغيل النظام
    python3 run.py start
}

# تشغيل النظام باستخدام Docker
start_with_docker() {
    print_info "تشغيل النظام باستخدام Docker..."
    
    if [ "$DOCKER_AVAILABLE" = false ]; then
        print_error "Docker غير متوفر"
        exit 1
    fi
    
    # بناء وتشغيل الحاويات
    docker-compose up --build -d
    
    print_success "تم تشغيل النظام باستخدام Docker"
    print_info "يمكنك مراقبة السجلات باستخدام: docker-compose logs -f"
}

# إيقاف النظام
stop_system() {
    print_info "إيقاف النظام..."
    
    if [ "$DOCKER_AVAILABLE" = true ] && [ -f docker-compose.yml ]; then
        docker-compose down
        print_success "تم إيقاف النظام"
    else
        print_warning "يرجى إيقاف النظام يدوياً"
    fi
}

# عرض الحالة
show_status() {
    print_info "حالة النظام:"
    
    if [ "$DOCKER_AVAILABLE" = true ] && [ -f docker-compose.yml ]; then
        docker-compose ps
    else
        print_info "التشغيل المحلي - فحص العمليات..."
        ps aux | grep -E "(python.*run.py|amazon.*bot)" | grep -v grep || print_warning "لا توجد عمليات قيد التشغيل"
    fi
}

# عرض السجلات
show_logs() {
    print_info "عرض السجلات..."
    
    if [ "$DOCKER_AVAILABLE" = true ] && [ -f docker-compose.yml ]; then
        docker-compose logs -f amazon_deals_bot
    else
        if [ -f logs/amazon_bot.log ]; then
            tail -f logs/amazon_bot.log
        else
            print_warning "ملف السجل غير موجود"
        fi
    fi
}

# عرض المساعدة
show_help() {
    echo "استخدام: $0 [COMMAND]"
    echo ""
    echo "الأوامر المتاحة:"
    echo "  setup       - إعداد النظام للمرة الأولى"
    echo "  start       - تشغيل النظام محلياً"
    echo "  docker      - تشغيل النظام باستخدام Docker"
    echo "  stop        - إيقاف النظام"
    echo "  status      - عرض حالة النظام"
    echo "  logs        - عرض السجلات"
    echo "  test        - تشغيل الاختبارات"
    echo "  help        - عرض هذه المساعدة"
    echo ""
    echo "أمثلة:"
    echo "  $0 setup     # إعداد النظام"
    echo "  $0 start     # تشغيل النظام"
    echo "  $0 docker    # تشغيل باستخدام Docker"
    echo "  $0 logs      # مراقبة السجلات"
}

# الدالة الرئيسية
main() {
    print_header
    
    # فحص المتطلبات
    check_requirements
    
    # تنفيذ الأمر المطلوب
    case "${1:-help}" in
        setup)
            setup_environment
            setup_database
            print_success "تم إعداد النظام بنجاح!"
            print_info "يمكنك الآن تشغيل النظام باستخدام: $0 start"
            ;;
        start)
            setup_environment
            run_tests
            start_system
            ;;
        docker)
            start_with_docker
            ;;
        stop)
            stop_system
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        test)
            setup_environment
            run_tests
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "أمر غير معروف: $1"
            show_help
            exit 1
            ;;
    esac
}

# تشغيل الدالة الرئيسية
main "$@"

