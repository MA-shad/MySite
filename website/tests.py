from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status

from website.models import (
    Profile,
    Headline,
    Stat,
    AboutCard,
    Skill,
    SkillCategory,
    Technology,
    Project,
    Category,
    BlogPost,
    ContactMessage,
    SocialLink,
)
from website.serializers import ContactMessageSerializer


class ModelArchitectureTestCase(TestCase):
    def setUp(self):
        self.profile = Profile.objects.create(
            name_fa="هپی کد",
            name_en="HappyCode",
            headline="توسعه‌دهنده جنگو",
            bio_fa="شرح کوتاه بیوگرافی برای تست",
            email="test@example.com",
        )
        self.tech, _ = Technology.objects.get_or_create(slug="django", defaults={"name": "Django"})
        self.skill = Skill.objects.create(
            name="Python Test Skill",
            percentage=85,
            category=SkillCategory.BACKEND,
        )

    def test_profile_singleton_real_creation_path(self):
        """اعتبارسنجی تک‌رکوردی بودن پروفایل در مسیرهای واقعی ایجاد (objects.create و save)"""
        with self.assertRaises(ValidationError):
            Profile.objects.create(
                name_fa="مدیر دوم",
                name_en="Admin Two",
                headline="عنوان دیگر",
                bio_fa="بیوگرافی دوم",
                email="admin2@example.com",
            )

        second_profile = Profile(
            name_fa="مدیر سوم",
            name_en="Admin Three",
            bio_fa="بیوگرافی سوم",
            email="admin3@example.com",
        )
        with self.assertRaises(ValidationError):
            second_profile.save()

    def test_project_auto_slug_generation(self):
        """تولید خودکار اسلاگ معتبر و یکتا در صورت عدم ارسال اسلاگ"""
        project1 = Project.objects.create(
            title="سامانه مدیریت مالی",
            description="سامانه هوشمند مالی و حسابداری",
        )
        self.assertTrue(bool(project1.slug))

        # ساخت پروژه دوم با همان عنوان برای بررسی جلوگیری از تکراری شدن اسلاگ
        project2 = Project.objects.create(
            title="سامانه مدیریت مالی",
            description="نسخه دوم سامانه مالی",
        )
        self.assertNotEqual(project1.slug, project2.slug)
        self.assertTrue(project2.slug.startswith("سامانه-مدیریت-مالی-"))

    def test_skill_proficiency_property(self):
        """اعتبارسنجی پراپرتی تسلط و دسته‌بندی موضوعی مهارت"""
        self.assertEqual(self.skill.proficiency, 85)
        self.assertEqual(self.skill.category, SkillCategory.BACKEND)


class SerializerValidationTestCase(TestCase):
    def test_contact_serializer_valid_plain_text(self):
        """اعتبارسنجی سریالایزر و تضمین عدم HTML-escaping در مرحله ذخیره‌سازی متن"""
        payload = {
            "name": "محمدرضا <توسعه‌دهنده>",
            "email": "test@example.com",
            "subject": "پرسش درباره \"معماری\" & جنگو",
            "message": "سلام، متن پیام شامل کاراکترهای خاص مانند < و > و \" بدون تغییر باید ذخیره شود.",
        }
        serializer = ContactMessageSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        instance = serializer.save()

        # متن خام باید بدون تبدیل به &lt; و &gt; یا &quot; در دیتابیس ثبت شود
        self.assertEqual(instance.name, "محمدرضا <توسعه‌دهنده>")
        self.assertEqual(instance.subject, "پرسش درباره \"معماری\" & جنگو")
        self.assertIn("<", instance.message)
        self.assertIn(">", instance.message)

    def test_contact_serializer_length_constraints(self):
        """اعتبارسنجی محدودیت‌های طول فیلدها"""
        # نام کمتر از ۲ کاراکتر
        s1 = ContactMessageSerializer(data={"name": "A", "email": "a@b.com", "subject": "موضوع تست", "message": "متن پیام معتبر تست"})
        self.assertFalse(s1.is_valid())
        self.assertIn("name", s1.errors)

        # موضوع کمتر از ۳ کاراکتر
        s2 = ContactMessageSerializer(data={"name": "علی", "email": "a@b.com", "subject": "ab", "message": "متن پیام معتبر تست"})
        self.assertFalse(s2.is_valid())
        self.assertIn("subject", s2.errors)

        # پیام کمتر از ۱۰ کاراکتر
        s3 = ContactMessageSerializer(data={"name": "علی", "email": "a@b.com", "subject": "موضوع معتبر", "message": "کوتاه"})
        self.assertFalse(s3.is_valid())
        self.assertIn("message", s3.errors)

        # ایمیل نامعتبر
        s4 = ContactMessageSerializer(data={"name": "علی", "email": "invalid-email", "subject": "موضوع معتبر", "message": "متن پیام معتبر تست"})
        self.assertFalse(s4.is_valid())
        self.assertIn("email", s4.errors)


class RateLimitingTestCase(APITestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse("website_api:contact")

    def test_contact_submission_rate_limiting(self):
        """اعتبارسنجی تراتلینگ و بازگشت خطای ۴۲۹ پس از نقض سقف درخواست"""
        payload = {
            "name": "فرستنده تست",
            "email": "user@example.com",
            "subject": "موضوع بررسی تراتل",
            "message": "متن پیام آزمایشی برای اعتبارسنجی محدودکننده نرخ درخواست",
        }
        # اولین درخواست باید موفق باشد
        r1 = self.client.post(self.url, payload, format="json")
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)

        # درخواست فوری دوم با همان آی‌پی باید به علت محدودیت ضربانی (Burst Rate) با وضعیت ۴۲۹ رد شود
        r2 = self.client.post(self.url, payload, format="json")
        self.assertEqual(r2.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class ProjectViewSetErrorHandlingTestCase(APITestCase):
    def setUp(self):
        self.project = Project.objects.create(
            title="پروژه تست خطایابی",
            slug="error-handling-project",
            description="توضیحات تست",
        )

    def test_existing_project_by_slug(self):
        """واکشی پروژه موجود بر اساس اسلاگ با پاسخ ۲۰۰"""
        url = reverse("website_api:project-detail", kwargs={"slug": "error-handling-project"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "پروژه تست خطایابی")

    def test_existing_project_by_numeric_id(self):
        """واکشی پروژه موجود بر اساس شناسه عددی با پاسخ ۲۰۰"""
        url = reverse("website_api:project-detail", kwargs={"slug": str(self.project.id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_existent_project_slug_returns_404(self):
        """پروژه ناموجود بر اساس اسلاگ باید پاسخ استاندارد ۴۰۴ بدهد (نه خطای ۵۰۰)"""
        url = reverse("website_api:project-detail", kwargs={"slug": "non-existent-slug-404"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_non_existent_project_id_returns_404(self):
        """پروژه ناموجود بر اساس شناسه عددی باید پاسخ استاندارد ۴۰۴ بدهد (نه خطای ۵۰۰)"""
        url = reverse("website_api:project-detail", kwargs={"slug": "999999"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class DataMigrationAndIntegrityTestCase(TestCase):
    def test_legacy_data_migration_associations(self):
        """اعتبارسنجی تبدیل برچسب‌های قدیمی به مدل فناوری و انتساب دسته‌بندی مهارت‌ها"""
        # ایجاد یا واکشی فناوری‌ها
        t_django, _ = Technology.objects.get_or_create(slug="django", defaults={"name": "Django"})
        t_python, _ = Technology.objects.get_or_create(slug="python", defaults={"name": "Python"})

        project = Project.objects.create(
            title="پروژه تست مایگریشن",
            tag="Django",
            url="http://example.com/demo",
        )
        project.technologies.add(t_django)
        project.demo_url = project.url
        project.save()

        self.assertIn(t_django, project.technologies.all())
        self.assertEqual(project.demo_url, "http://example.com/demo")
        self.assertTrue(bool(project.slug))

        # بررسی دسته‌بندی مهارتی
        skill_py, _ = Skill.objects.get_or_create(name="Python", defaults={"percentage": 80, "category": SkillCategory.BACKEND})
        skill_html, _ = Skill.objects.get_or_create(name="HTML", defaults={"percentage": 60, "category": SkillCategory.FRONTEND})
        skill_git, _ = Skill.objects.get_or_create(name="Git", defaults={"percentage": 50, "category": SkillCategory.TOOLS})

        self.assertEqual(skill_py.category, SkillCategory.BACKEND)
        self.assertEqual(skill_html.category, SkillCategory.FRONTEND)
        self.assertEqual(skill_git.category, SkillCategory.TOOLS)


class ApiEndpointsTestCase(APITestCase):
    def setUp(self):
        cache.clear()
        self.profile = Profile.objects.create(
            name_fa="محمدعلی",
            name_en="MohammadAli",
            headline="توسعه‌دهنده بک‌اند",
            bio_fa="بیوگرافی کامل",
            email="admin@example.com",
        )
        self.tech_django, _ = Technology.objects.get_or_create(slug="django", defaults={"name": "Django"})
        self.tech_react, _ = Technology.objects.get_or_create(slug="react", defaults={"name": "React"})

        self.skill_backend, _ = Skill.objects.get_or_create(
            name="Python Backend Skill",
            defaults={"percentage": 90, "category": SkillCategory.BACKEND, "is_featured": True},
        )
        self.skill_frontend, _ = Skill.objects.get_or_create(
            name="HTML Frontend Skill",
            defaults={"percentage": 70, "category": SkillCategory.FRONTEND, "is_featured": False},
        )

        self.project = Project.objects.create(
            title="پرتفولیو شخصی",
            slug="my-portfolio",
            description="پروژه پورتفولیو نمونه",
            is_featured=True,
        )
        self.project.technologies.add(self.tech_django)

        self.category = Category.objects.create(
            title="جنگو",
            slug="django-cat",
        )
        self.blog_post = BlogPost.objects.create(
            title="آشنایی با DRF",
            slug="intro-to-drf",
            category=self.category,
            description="چکیده مقاله برای تست",
            content="متن کامل مقاله آموزشی...",
            status=BlogPost.PostStatus.PUBLISHED,
        )

    def test_init_endpoint(self):
        """تست اندپوینت تجمیعی /api/v1/init/"""
        url = reverse("website_api:init")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("profile", response.data)
        self.assertIn("headlines", response.data)
        self.assertIn("featured_skills", response.data)
        self.assertIn("featured_projects", response.data)
        self.assertEqual(response.data["profile"]["name_fa"], "محمدعلی")

    def test_skills_filtering(self):
        """تست فیلترینگ مهارت‌ها بر اساس دسته‌بندی موضوعی"""
        url = reverse("website_api:skill-list")
        response = self.client.get(url, {"category": "backend"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)
        self.assertTrue(all(item["category"] == "backend" for item in response.data["results"]))

    def test_blog_published_posts(self):
        """تست لیست مقالات و صفحه جزئیات مقاله"""
        url = reverse("website_api:blog-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        detail_url = reverse("website_api:blog-detail", kwargs={"slug": "intro-to-drf"})
        detail_resp = self.client.get(detail_url)
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_resp.data["title"], "آشنایی با DRF")

    def test_contact_honeypot_bot_defense(self):
        """تست دفاع در برابر بات‌های هرزنامه‌ساز با فیلد هانی‌پات"""
        cache.clear()
        url = reverse("website_api:contact")
        payload = {
            "name": "Spam Bot",
            "email": "bot@spam.com",
            "subject": "تبلیغات اسپم",
            "message": "متن هرزنامه ارسالی ربات اینترنتی",
            "website_source_url": "http://spamsite.com",  # بات این فیلد را پر می‌کند
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # پیام نباید در دیتابیس ذخیره شده باشد
        self.assertFalse(ContactMessage.objects.filter(email="bot@spam.com").exists())

    def test_api_permission_read_only_for_public(self):
        """کاربران عمومی نباید بتوانند متدهای ویرایشی نظیر DELETE را اجرا کنند"""
        url = reverse("website_api:project-detail", kwargs={"slug": "my-portfolio"})
        delete_resp = self.client.delete(url)
        self.assertEqual(delete_resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class LegacyFrontendCompatibilityTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.profile = Profile.objects.create(
            name_fa="هپی کد",
            name_en="HappyCode",
            headline="توسعه‌دهنده جنگو",
            bio_fa="بیوگرافی برای رندر تمپلیت",
            email="admin@example.com",
        )
        self.category = Category.objects.create(title="آموزش", slug="learn")
        self.blog_post = BlogPost.objects.create(
            title="پست اول",
            slug="first-post",
            category=self.category,
            description="توضیح پست اول",
            content="محتوا",
        )

    def test_home_page_renders_cleanly(self):
        """صفحه اصلی تمپلیت موجود باید با وضعیت ۲۰۰ رندر شود"""
        response = self.client.get(reverse("website:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")
        self.assertContains(response, "هپی کد")

    def test_blog_detail_page_renders_cleanly(self):
        """صفحه جزئیات مقاله وبلاگ تمپلیت باید با وضعیت ۲۰۰ رندر شود"""
        response = self.client.get(reverse("website:blog_detail_by_slug", kwargs={"slug": "first-post"}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog_detail.html")
        self.assertContains(response, "پست اول")
