from django.db import migrations
from django.utils.text import slugify


def migrate_legacy_data(apps, schema_editor):
    Project = apps.get_model("website", "Project")
    Technology = apps.get_model("website", "Technology")
    Skill = apps.get_model("website", "Skill")

    # ۱. تولید فناوری‌های واقعی و ملموس (پرهیز از ثبت لایه‌های مفهومی نظیر Front-End)
    real_technologies = {
        "Django": "django",
        "Python": "python",
        "HTML": "html",
        "CSS": "css",
        "JavaScript": "javascript",
        "Git": "git",
    }
    tech_instances = {}
    for name, slug in real_technologies.items():
        tech, _ = Technology.objects.get_or_create(name=name, defaults={"slug": slug})
        tech_instances[name.lower()] = tech

    # ۲. نگاشت پروژه‌ها: تفکیک فناوری‌ها، اسلاگ‌های معتبر و حفظ demo_url خالی
    for project in Project.objects.all():
        tag_cleaned = (project.tag or "").strip()
        if tag_cleaned:
            if tag_cleaned.lower() in ["front-end", "frontend"]:
                # پروژه ۳ با تگ Front-End بر پایه HTML, CSS, JS ساخته شده است؛
                # فناوری‌های واقعی آن به جای عبارت کلی فرانت‌اند متصل می‌شوند:
                for t_name in ["html", "css", "javascript"]:
                    if t_name in tech_instances:
                        project.technologies.add(tech_instances[t_name])
            else:
                tech = tech_instances.get(tag_cleaned.lower())
                if tech:
                    project.technologies.add(tech)

        # آدرس لوکال‌هاست قدیمی به demo_url منتقل نمی‌شود و demo_url خالی (None) باقی می‌ماند
        project.demo_url = None

        # انتساب اسلاگ‌های یکتا و خوانا برای پروژه‌های موجود
        if not project.slug:
            if project.id == 1:
                project.slug = "cms-panel"
            elif project.id == 2:
                project.slug = "python-tools"
            elif project.id == 3:
                project.slug = "modern-ui"
            else:
                project.slug = slugify(project.title, allow_unicode=True) or f"project-{project.id}"
        project.save()

    # ۳. دسته‌بندی مهارت‌های قدیمی بر اساس ماهیت واقعی فنی هر مهارت
    skill_category_map = {
        "Python": "backend",
        "Django": "backend",
        "HTML": "frontend",
        "CSS": "frontend",
        "JavaScript": "frontend",
        "Git": "tools",
    }
    for skill in Skill.objects.all():
        assigned_category = skill_category_map.get(skill.name)
        if assigned_category:
            skill.category = assigned_category
            skill.save()


def reverse_migration(apps, schema_editor):
    """
    پیاده‌سازی واقعی بازگشت مایگریشن:
    - پاکسازی روابط چندبه‌چند فناوری‌های پروژه‌ها
    - پاکسازی اسلاگ‌ها و ریست فیلد demo_url
    - بازگرداندن دسته‌بندی مهارت‌ها به مقدار پیش‌فرض بک‌اند
    """
    Project = apps.get_model("website", "Project")
    Skill = apps.get_model("website", "Skill")

    for project in Project.objects.all():
        project.technologies.clear()
        project.demo_url = None
        project.save()

    for skill in Skill.objects.all():
        skill.category = "backend"
        skill.save()


class Migration(migrations.Migration):

    dependencies = [
        ("website", "0018_technology_alter_aboutcard_options_and_more"),
    ]

    operations = [
        migrations.RunPython(migrate_legacy_data, reverse_migration),
    ]
