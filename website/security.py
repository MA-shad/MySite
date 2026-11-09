import hmac
import hashlib
from django.conf import settings


def get_client_ip(request) -> str:
    """
    استخراج نشانی IP واقعی کلاینت با انطباق بر معماری پروکسی معکوس در Render.

    تحلیل امنیتی هدر X-Forwarded-For در محیط سرور ابری Render:
    - کلاینت‌های مهاجم می‌توانند یک هدر جعلی X-Forwarded-For ارسال کنند (مانند X-Forwarded-For: 1.1.1.1).
    - پروکسی معکوس معتبر سرور ابری Render (Envoy/Load Balancer) نشانی واقعی کلاینت متصل‌شونده
      را به انتهای زنجیره هدر اضافه می‌کند: [spoofed_ip, real_client_ip].
    - بنابراین:
      - اتکا به اولین نشانی (سمت چپ) در محیط‌های پشت پروکسی خطر جعل نشانی (IP Spoofing) دارد.
      - آخرین نشانی در این زنجیره (سمت راست)، نشانی واقعی اضافه شده توسط لودبالانسر مورد اعتماد Render است.
    - در محیط‌های توسعه محلی بدون پروکسی، از REMOTE_ADDR به عنوان نشانی اتصال مستقیم استفاده می‌شود.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip_chain = [ip.strip() for ip in x_forwarded_for.split(",") if ip.strip()]
        if ip_chain:
            # آخرین نشانی در زنجیره توسط نزدیک‌ترین پروکسی معتبر (Render Load Balancer) ثبت شده است
            return ip_chain[-1]
    return request.META.get("REMOTE_ADDR", "")


def generate_ip_hash(ip: str) -> str:
    """
    محاسبه هش رمزنگاری‌شده یک‌طرفه نشانی آی‌پی با الگوریتم HMAC-SHA256 و کلید محرمانه جنگو.

    این روش تضمین می‌کند که:
    ۱. نشانی خام آی‌پی در دیتابیس ذخیره نمی‌شود و حریم خصوصی کلاینت حفظ می‌گردد.
    ۲. بدون دسترسی مستقیم به SECRET_KEY جنگو، مهندسی معکوس یا جستجوی جدول رنگین‌کمانی ناممکن است.
    """
    if not ip:
        return ""
    secret_key = settings.SECRET_KEY.encode("utf-8")
    ip_bytes = ip.encode("utf-8")
    return hmac.new(secret_key, ip_bytes, hashlib.sha256).hexdigest()
