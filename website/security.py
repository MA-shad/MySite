import hmac
import hashlib
from django.conf import settings


def get_client_ip(request) -> str:
    """
    استخراج نشانی IP واقعی کلاینت با پشتیبانی از هدرهای پروکسی سرور معتبر.

    در محیط‌های ابری مانند Render یا سرورهای پشت پروکسی معکوس (Reverse Proxy):
    - در صورتی که هدر HTTP_X_FORWARDED_FOR موجود باشد، اولین نشانی در زنجیره،
      نشانی واقعی کلاینت است.
    - در غیر این صورت، از نشانی مستقیم اتصال (REMOTE_ADDR) استفاده می‌شود.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR", "")
    return ip


def generate_ip_hash(ip: str) -> str:
    """
    محاسبه هش رمزنگاری‌شده نشانی آی‌پی با الگوریتم HMAC-SHA256 و کلید محرمانه جنگو.

    این روش تضمین می‌کند که:
    ۱. نشانی خام آی‌پی در پایگاه داده ذخیره نمی‌شود (حفظ حریم خصوصی).
    ۲. امکان بازتولید هش یا حمله جدول رنگین‌کمانی بدون کلید SECRET_KEY برای مهاجم ناممکن است.
    """
    if not ip:
        return ""
    secret_key = settings.SECRET_KEY.encode("utf-8")
    ip_bytes = ip.encode("utf-8")
    return hmac.new(secret_key, ip_bytes, hashlib.sha256).hexdigest()
