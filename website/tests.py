from django.test import TestCase, Client, override_settings
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


class ModelArchitectureTestCase(TestCase):
    def setUp(self):
        self.profile = Profile.objects.create(
            name_fa="هپی کد",
            name_en="HappyCode",
            headline="توسعه‌دهنده جنگو",
            bio_fa="شرح کوتاه بیوگرافی برای تست",
            email="test@example.com",
        )
        self.tech = Technology.objects.create(name="Django", slug="django")
        self.skill = Skill.objects.create(
            name="Python",
            percentage=85,
            category=SkillCategory.BACKEND,
        )

    def test_profile_singleton_clean(self):
        """اعتبارسنجی تک‌رکوردی بودن پروفایل"""
        second_profile = Profile(
            name_fa="تست ۲",
            name_en="Test 2",
            bio_fa="بیوگرافی دوم",
            email="test2@example.com",
        )
        with self.assertRaises(ValidationError):
            second_profile.clean()

    def test_skill_proficiency_property(self):
        """اعتبارسنجی پراپرتی proficiency معادل percentage"""
        self.assertEqual(self.skill.proficiency, 85)
        self.assertEqual(self.skill.category, SkillCategory.BACKEND)

    def test_project_technology_many_to_many(self):
        """اعتبارسنجی ارتباط چندبه‌چند میان پروژه و فناوری"""
        project = Project.objects.create(
            title="پروژه تست",
            slug="test-project",
            description="توضیحات پروژه تست",
        )
        project.technologies.add(self.tech)
        self.assertIn(self.tech, project.technologies.all())
        self.assertEqual(self.tech.projects.first(), project)


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
        self.tech_django = Technology.objects.create(name="Django", slug="django")
        self.tech_react = Technology.objects.create(name="React", slug="react")

        self.skill_backend = Skill.objects.create(
            name="Python",
            percentage=90,
            category=SkillCategory.BACKEND,
            is_featured=True,
        )
        self.skill_frontend = Skill.objects.create(
            name="HTML",
            percentage=70,
            category=SkillCategory.FRONTEND,
            is_featured=False,
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
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Python")

    def test_projects_list_and_detail(self):
        """تست فهرست پروژه‌ها و واکشی بر اساس اسلاگ"""
        list_url = reverse("website_api:project-list")
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["technologies"][0]["name"], "Django")

        detail_url = reverse("website_api:project-detail", kwargs={"slug": "my-portfolio"})
        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data["title"], "پرتفولیو شخصی")

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

    def test_contact_submission_valid(self):
        """تست ثبت پیام مخاطب معتبر"""
        cache.clear()
        url = reverse("website_api:contact")
        payload = {
            "name": "علی محمدی",
            "email": "ali@example.com",
            "subject": "همکاری در پروژه",
            "message": "سلام، علاقه‌مند به همکاری در پروژه جدید جنگو هستم.",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ContactMessage.objects.filter(email="ali@example.com").exists())

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
        # ReadOnlyModelViewSet متد DELETE را مسدود می‌کند (۴۰۵ Method Not Allowed)
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
