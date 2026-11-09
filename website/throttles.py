from rest_framework.throttling import AnonRateThrottle


class ContactRateThrottle(AnonRateThrottle):
    """محدودکننده نرخ ثبت پیام برای جلوگیری از ارسال هرزنامه."""
    scope = "contact_submission"
    rate = "5/hour"


class ContactBurstThrottle(AnonRateThrottle):
    """محدودکننده ضربانی برای جلوگیری از ثبت متوالی زیر ۱ دقیقه."""
    scope = "contact_burst"
    rate = "1/minute"
