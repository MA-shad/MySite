from django.test import TestCase, Client, TransactionTestCase
from django.urls import reverse
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import connection
from django.db.utils import IntegrityError
from django.db.migrations.executor import MigrationExecutor
from django.test.client import RequestFactory
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
from website.security import get_client_ip, generate_ip_hash


class ModelArchitectureTestCase(TestCase):
    def setUp(self):
        self.profile = Profile.objects.create(
            name_fa="هپی کد",
            name_en="HappyCode",
            headline="",
            bio_fa="شرح کوتاه بیوگرافی برای تست",
            email="test@example.com",
            is_available_for_hire=False,
        )
        self.tech, _ = Technology.objects.get_or_create(slug="django", defaults={"name": "Django"})
        self.skill = Skill.objects.create(
            name="Python Test Skill",
            percentage=85,
            category=SkillCategory.BACKEND,
        )

    def test_profile_singleton_real_creation_path(self):
        """اعتبارسنجی تک‌رکوردی بودن پروفایل در مسیرهای پایتونی (objects.create و save)"""
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

    def test_profile_singleton_bulk_create_bypass_prevented(self):
        """تضمین جلوگیری از دور زدن اعتبارسنجی تک‌رکوردی با bulk_create در لایه دیتابیس"""
        with self.assertRaises(IntegrityError):
            Profile.objects.bulk_create([
                Profile(
                    name_fa="مدیر دورزننده",
                    name_en="Bypass Admin",
                    bio_fa="تلاش برای درج رکورد دوم از طریق بالک",
                    email="bypass@example.com",
                    is_singleton=True,
                )
            ])

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
        """اعتبارسنجی سریالایزر و تضمین عدم تغییر کاراکترها در مرحله ذخیره‌سازی متن"""
        payload = {
            "name": "محمدرضا <توسعه‌دهنده>",
            "email": "test@example.com",
            "subject": "پرسش درباره \"معماری\" & جنگو",
            "message": "سلام، متن پیام شامل کاراکترهای خاص مانند < و > و \" بدون تغییر باید ذخیره شود.",
        }
        serializer = ContactMessageSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        instance = serializer.save()

        # متن خام باید بدون تبدیل به کاراکترهای اسکیپ شده در دیتابیس ثبت شود
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

        # درخواست فوری دوم با همان آی‌پی باید به علت محدودیت ضربانی با وضعیت ۴۲۹ رد شود
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


class SecurityAndIpExtractionTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_client_ip_direct_connection(self):
        """در اتصال مستقیم بدون پروکسی، نشانی اتصال مستقیم کلاینت بازگردانده می‌شود"""
        request = self.factory.get("/")
        request.META["REMOTE_ADDR"] = "192.0.2.1"
        self.assertEqual(get_client_ip(request), "192.0.2.1")

    def test_get_client_ip_render_reverse_proxy_trust(self):
        """اتکا به آخرین نشانی در زنجیره برای انطباق با لودبالانسر Render و جلوگیری از جعل آی‌پی"""
        request = self.factory.get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = "203.0.113.195, 70.41.3.18, 198.51.100.2"
        request.META["REMOTE_ADDR"] = "10.0.0.1"
        # آخرین آی‌پی زنجیره نشانی واقعی ثبت‌شده توسط نزدیک‌ترین پروکسی معتبر است
        self.assertEqual(get_client_ip(request), "198.51.100.2")

    def test_generate_ip_hash_hmac_sha256(self):
        """محاسبه هش یک‌طرفه امن نشانی آی‌پی با طول ۶۴ کاراکتر هگزادسیمال بر پایه اچ‌مک"""
        hash1 = generate_ip_hash("198.51.100.2")
        hash2 = generate_ip_hash("198.51.100.2")
        hash3 = generate_ip_hash("203.0.113.5")

        self.assertEqual(len(hash1), 64)
        self.assertEqual(hash1, hash2)
        self.assertNotEqual(hash1, hash3)
        self.assertEqual(generate_ip_hash(""), "")


class RealDataMigrationTestCase(TransactionTestCase):
    def test_migration_0019_real_execution(self):
        """
        اجرای واقعی مایگریشن 0019 روی داده‌های قدیمی از طریق MigrationExecutor:
        ۱. بازگردانی دیتابیس به مایگریشن 0018
        ۲. ایجاد داده‌های قدیمی با تگ‌های متنی و پیوندهای لوکال‌هاست
        ۳. اعمال مایگریشن 0019 رو به جلو
        ۴. اعتبارسنجی عدم ایجاد Technology به نام Front-End
        ۵. اعتبارسنجی اتصال چندبه‌چند HTML, CSS, JavaScript برای پروژه فرانت‌اند
        ۶. اعتبارسنجی باقی‌ماندن demo_url به صورت خالی و حفظ آدرس قدیمی در فیلد url
        ۷. اعتبارسنجی تولید اسلاگ‌های یکتا و دسته‌بندی مهارتی دقیق
        ۸. اعتبارسنجی عملیات برگشت مایگریشن
        ۹. مهاجرت مجدد دیتابیس به آخرین مایگریشن برای پایداری وضعیت سیستم
        """
        executor = MigrationExecutor(connection)
        migrate_0018 = [("website", "0018_technology_alter_aboutcard_options_and_more")]
        migrate_0019 = [("website", "0019_migrate_legacy_data")]

        try:
            # ۱. عقب‌گرد به مایگریشن 0018
            executor.migrate(migrate_0018)
            old_state = executor.loader.project_state(migrate_0018)
            OldProject = old_state.apps.get_model("website", "Project")
            OldSkill = old_state.apps.get_model("website", "Skill")

            # ۲. درج داده‌های سنتی متناظر با وضعیت اولیه پروژه
            p_front = OldProject.objects.create(
                title="قالب مدرن رابط کاربری",
                tag="Front-End",
                url="http://127.0.0.1:8080/#legacy-demo",
                description="پروژه رابط کاربری بدون اسلاگ",
            )
            p_backend = OldProject.objects.create(
                title="سیستم جامع مدیریت",
                tag="Django",
                url="http://localhost:8000/app",
                description="پروژه جنگو با آدرس توسعه محلی",
            )

            s_py = OldSkill.objects.create(name="Python", percentage=90)
            s_dj = OldSkill.objects.create(name="Django", percentage=85)
            s_html = OldSkill.objects.create(name="HTML", percentage=80)
            s_css = OldSkill.objects.create(name="CSS", percentage=75)
            s_js = OldSkill.objects.create(name="JavaScript", percentage=70)
            s_git = OldSkill.objects.create(name="Git", percentage=65)

            # ۳. اجرای پیش‌رونده مایگریشن 0019
            executor.loader.build_graph()
            executor.migrate(migrate_0019)
            new_state = executor.loader.project_state(migrate_0019)

            NewProject = new_state.apps.get_model("website", "Project")
            NewSkill = new_state.apps.get_model("website", "Skill")
            NewTech = new_state.apps.get_model("website", "Technology")

            # ۴. بررسی عدم ثبت Front-End به عنوان مدل فناوری مستقل
            self.assertFalse(NewTech.objects.filter(name__iexact="Front-End").exists())
            self.assertFalse(NewTech.objects.filter(slug__iexact="front-end").exists())

            # ۵. بررسی انتساب فناوری‌های تشکیل‌دهنده فرانت‌اند (HTML, CSS, JS) به پروژه
            p_front_migrated = NewProject.objects.get(id=p_front.id)
            front_tech_slugs = set(p_front_migrated.technologies.values_list("slug", flat=True))
            self.assertTrue({"html", "css", "javascript"}.issubset(front_tech_slugs))

            # ۶. بررسی عدم کپی لوکال‌هاست به demo_url و حفظ url قدیمی
            self.assertIsNone(p_front_migrated.demo_url)
            self.assertEqual(p_front_migrated.url, "http://127.0.0.1:8080/#legacy-demo")

            p_backend_migrated = NewProject.objects.get(id=p_backend.id)
            self.assertIsNone(p_backend_migrated.demo_url)
            self.assertEqual(p_backend_migrated.url, "http://localhost:8000/app")
            self.assertTrue(p_backend_migrated.technologies.filter(slug="django").exists())

            # ۷. بررسی تولید اسلاگ‌های معتبر
            self.assertTrue(bool(p_front_migrated.slug))
            self.assertTrue(bool(p_backend_migrated.slug))

            # ۸. بررسی دسته‌بندی مهارتی دقیق
            self.assertEqual(NewSkill.objects.get(id=s_py.id).category, "backend")
            self.assertEqual(NewSkill.objects.get(id=s_dj.id).category, "backend")
            self.assertEqual(NewSkill.objects.get(id=s_html.id).category, "frontend")
            self.assertEqual(NewSkill.objects.get(id=s_css.id).category, "frontend")
            self.assertEqual(NewSkill.objects.get(id=s_js.id).category, "frontend")
            self.assertEqual(NewSkill.objects.get(id=s_git.id).category, "tools")

            # ۹. بررسی بازگشت‌پذیری مایگریشن به 0018
            executor.loader.build_graph()
            executor.migrate(migrate_0018)
            rev_state = executor.loader.project_state(migrate_0018)
            RevProject = rev_state.apps.get_model("website", "Project")
            RevSkill = rev_state.apps.get_model("website", "Skill")

            p_rev = RevProject.objects.get(id=p_front.id)
            self.assertEqual(p_rev.technologies.count(), 0)
            self.assertIsNone(p_rev.demo_url)
            self.assertEqual(RevSkill.objects.get(id=s_html.id).category, "backend")

        finally:
            # ۱۰. بازگردانی کامل ساختار پایگاه داده به آخرین مایگریشن
            executor.loader.build_graph()
            executor.migrate(executor.loader.graph.leaf_nodes())


class ApiEndpointsTestCase(APITestCase):
    def setUp(self):
        cache.clear()
        self.profile = Profile.objects.create(
            name_fa="محمدعلی",
            name_en="MohammadAli",
            headline="",
            bio_fa="بیوگرافی کامل",
            email="admin@example.com",
            is_available_for_hire=False,
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
            headline="",
            bio_fa="بیوگرافی برای رندر تمپلیت",
            email="admin@example.com",
            is_available_for_hire=False,
        )
        self.category = Category.objects.create(title="آموزش", slug="learn")
        self.blog_post = BlogPost.objects.create(
            title="پست اول",
            slug="first-post",
            category=self.category,
            description="توضیح پست اول",
            content="محتوا",
            status=BlogPost.PostStatus.PUBLISHED,
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

    def test_draft_blog_posts_hidden_from_public_views(self):
        """مقالات در وضعیت پیش‌نویس (Draft) نباید در صفحه اصلی نمایش داده شوند و در صفحه جزئیات پاسخ ۴۰۴ می‌دهند"""
        draft_post = BlogPost.objects.create(
            title="مقاله پیش‌نویس محرمانه",
            slug="secret-draft-post",
            category=self.category,
            description="این مقاله نباید در دید عموم باشد",
            content="محتوای پیش‌نویس محرمانه...",
            status=BlogPost.PostStatus.DRAFT,
        )

        # ۱. عدم نمایش در صفحه اصلی
        home_resp = self.client.get(reverse("website:home"))
        self.assertEqual(home_resp.status_code, 200)
        self.assertContains(home_resp, "پست اول")
        self.assertNotContains(home_resp, "مقاله پیش‌نویس محرمانه")

        # ۲. بازگشت وضعیت ۴۰۴ در واکشی مستقیم با اسلاگ
        detail_slug_resp = self.client.get(reverse("website:blog_detail_by_slug", kwargs={"slug": "secret-draft-post"}))
        self.assertEqual(detail_slug_resp.status_code, 404)

        # ۳. بازگشت وضعیت ۴۰۴ در واکشی مستقیم با شناسه عددی
        detail_id_resp = self.client.get(reverse("website:blog_detail_by_id", kwargs={"id": draft_post.id}))
        self.assertEqual(detail_id_resp.status_code, 404)
