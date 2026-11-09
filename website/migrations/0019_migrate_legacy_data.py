from django.db import migrations
from django.utils.text import slugify


def migrate_legacy_data(apps, schema_editor):
    Project = apps.get_model("website", "Project")
    Technology = apps.get_model("website", "Technology")
    Skill = apps.get_model("website", "Skill")

    # ۱. تولید و نگاشت فناوری‌های پایه
    tech_slug_map = {
        "Django": "django",
        "Python": "python",
        "Front-End": "front-end",
        "HTML": "html",
        "CSS": "css",
        "JavaScript": "javascript",
        "Git": "git",
    }
    created_techs = {}
    for name, slug in tech_slug_map.items():
        tech, _ = Technology.objects.get_or_create(name=name, defaults={"slug": slug})
        created_techs[name.lower()] = tech

    # ۲. تبدیل تگ‌های قدیمی پروژه‌ها به مدل فناوری و انتساب اسلاگ معتبر
    for project in Project.objects.all():
        if project.tag:
            tag_name = project.tag.strip()
            tech = created_techs.get(tag_name.lower())
            if not tech:
                tech, _ = Technology.objects.get_or_create(
                    name=tag_name,
                    defaults={"slug": slugify(tag_name, allow_unicode=True) or f"tech-{project.id}"},
                )
            project.technologies.add(tech)

        if not project.demo_url and project.url:
            project.demo_url = project.url

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

    # ۳. دسته‌بندی مهارت‌های قدیمی بر اساس ماهیت تخصصی و واقعی هر مهارت
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
    # این عملیات برای برگشت‌پذیری ساختار نیازی به حذف فیزیکی داده‌ها ندارد
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("website", "0018_technology_alter_aboutcard_options_and_more"),
    ]

    operations = [
        migrations.RunPython(migrate_legacy_data, reverse_migration),
    ]
