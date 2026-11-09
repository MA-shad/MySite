# معماری فنی پروژه مای‌سایت (MySite)

## ۱. معماری فعلی (Legacy Monolith)
- **بک‌اند**: جنگو با سیستم رندر تمپلیت داخلی (Jinja/Django Templates) در `templates/home.html`.
- **دیتابیس**: SQLite (`db.sqlite3`).
- **اپلیکیشن‌ها**:
  - `website`: مدل‌های اصلی پورتفولیو شامل `Profile`, `Skill`, `Project`, `BlogPost`, `ContactMessage`, `Category`, `AboutCard`, `Stat`, `Headline`.
  - `login`: احراز هویت ادمین و ورود.
  - `templatetags/website_tags.py`: تگ‌های سفارشی برای فیلتر و رندر محتوا.

## ۲. معماری هدف و در حال گذار (Decoupled Architecture)
- **بک‌اند API**: مهاجرت به Django REST Framework (DRF)؛ ارائه داده‌ها در قالب اندپوینت‌های JSON و حذف وابستگی به رندر تمپلیت‌تگ‌ها.
- **پایگاه داده**: مهاجرت از SQLite به PostgreSQL برای انطباق با استانداردهای پروداکشن.
- **فرانت‌اند**: رابط کاربری مستقل با Next.js یا React همراه با Tailwind CSS؛ بهره‌گیری از قابلیت‌های رندر سمت سرور (SSR/SSG) در Next.js جهت دستیابی به سئوی فوق‌العاده.
- **طراحی بصری**: زبان طراحی گلس‌مورفیسم (Glassmorphism) تیره، چشم‌نواز و حرفه‌ای با بازنگری در پالت رنگ‌های اولیه.
