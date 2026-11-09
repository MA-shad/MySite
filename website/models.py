from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class Profile(models.Model):
    name_fa = models.CharField(max_length=50, verbose_name="نام فارسی")
    name_en = models.CharField(max_length=50, verbose_name="نام انگلیسی")
    headline = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name="عنوان حرفه‌ای ثابت",
    )
    bio_fa = models.TextField(verbose_name="شرح بیوگرافی")
    bio_login = models.TextField(blank=True, verbose_name="متن لاگین قدیمی")
    status_fa = models.CharField(max_length=100, blank=True, verbose_name="وضعیت قبلی")
    status_login = models.TextField(blank=True, verbose_name="پیام لاگین قدیمی")
    current_status = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name="وضعیت کاری جاری",
    )
    email = models.EmailField(verbose_name="رایانامه")
    github = models.URLField(blank=True, verbose_name="گیت‌هاب")
    linkedin = models.URLField(blank=True, verbose_name="لینکدین")
    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
        verbose_name="تصویر پرسنلی",
    )
    resume_file = models.FileField(
        upload_to="resumes/",
        blank=True,
        null=True,
        verbose_name="فایل رزومه",
    )
    is_available_for_hire = models.BooleanField(
        default=False,
        blank=True,
        verbose_name="آماده برای همکاری",
    )
    is_singleton = models.BooleanField(
        default=True,
        unique=True,
        editable=False,
        verbose_name="قید تک‌رکوردی دیتابیس",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="زمان به‌روزرسانی")

    class Meta:
        verbose_name = "پروفایل مدیر"
        verbose_name_plural = "پروفایل مدیر"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(is_singleton=True),
                name="profile_is_singleton_must_be_true",
            )
        ]

    def clean(self):
        if not self.pk and Profile.objects.exists():
            raise ValidationError("تنها یک رکورد پروفایل مجاز است.")

    def save(self, *args, **kwargs):
        self.is_singleton = True
        if not self.pk and Profile.objects.exists():
            raise ValidationError("تنها یک رکورد پروفایل مجاز است.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name_fa} ({self.name_en})"


class Headline(models.Model):
    """عبارت‌های متحرک برای انیمیشن تایپ در هدر سایت."""
    text = models.CharField(max_length=200, verbose_name="متن عنوان")
    order = models.IntegerField(default=0, verbose_name="ترتیب نمایش")

    class Meta:
        verbose_name = "عنوان متحرک هدر"
        verbose_name_plural = "عناوین متحرک هدر"
        ordering = ["order"]

    def __str__(self):
        return self.text


class Stat(models.Model):
    value = models.CharField(max_length=20, verbose_name="مقدار آماری")
    label = models.CharField(max_length=100, verbose_name="عنوان آمار")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")

    class Meta:
        verbose_name = "آمار دستاورد"
        verbose_name_plural = "آمارهای دستاوردها"
        ordering = ["order"]

    def __str__(self):
        return f"{self.label}: {self.value}"


class AboutCard(models.Model):
    icon = models.CharField(max_length=100, verbose_name="کلاس آیکون")
    title = models.CharField(max_length=100, verbose_name="عنوان کارت")
    description = models.TextField(verbose_name="توضیحات")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")

    class Meta:
        verbose_name = "کارت درباره من"
        verbose_name_plural = "کارت‌های درباره من"
        ordering = ["order"]

    def __str__(self):
        return self.title


class SkillCategory(models.TextChoices):
    BACKEND = "backend", "بک‌اند"
    FRONTEND = "frontend", "فرانت‌اند"
    DATABASE = "database", "پایگاه داده"
    TOOLS = "tools", "ابزارها و دوآپس"
    NETWORK = "network", "شبکه و زیرساخت"


class Skill(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام مهارت")
    category = models.CharField(
        max_length=20,
        choices=SkillCategory.choices,
        default=SkillCategory.BACKEND,
        verbose_name="دسته‌بندی موضوعی",
    )
    percentage = models.IntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
        verbose_name="درصد تسلط",
    )
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")
    is_featured = models.BooleanField(default=True, verbose_name="مهارت شاخص")

    class Meta:
        verbose_name = "مهارت فردی"
        verbose_name_plural = "مهارت‌های فردی"
        ordering = ["order", "-percentage"]

    @property
    def proficiency(self):
        return self.percentage

    def __str__(self):
        return f"{self.name} ({self.percentage}%)"


class Technology(models.Model):
    """فناوری‌های پروژه‌محور مستقل از مهارت‌های فردی."""
    name = models.CharField(max_length=50, unique=True, verbose_name="نام فناوری")
    slug = models.SlugField(max_length=50, unique=True, allow_unicode=True, verbose_name="اسلاگ")

    class Meta:
        verbose_name = "فناوری پروژه"
        verbose_name_plural = "فناوری‌های پروژه‌ها"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Project(models.Model):
    title = models.CharField(max_length=100, verbose_name="عنوان پروژه")
    slug = models.SlugField(
        max_length=120,
        unique=True,
        null=True,
        blank=True,
        allow_unicode=True,
        verbose_name="اسلاگ یکتا",
    )
    description = models.TextField(verbose_name="شرح پروژه")
    image = models.ImageField(
        upload_to="images/",
        default="images/default_image.jpg",
        verbose_name="تصویر پیش‌نمایش",
    )
    tag = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="برچسب متنی قدیمی",
        help_text="جهت حفظ سازگاری قالب‌های قدیمی",
    )
    technologies = models.ManyToManyField(
        Technology,
        blank=True,
        related_name="projects",
        verbose_name="فناوری‌های پروژه",
    )
    url = models.URLField(
        blank=True,
        verbose_name="لینک عمومی قدیمی",
        help_text="جهت حفظ سازگاری قالب‌های قدیمی",
    )
    demo_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="پیوند نسخه زنده",
    )
    github_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="پیوند مخزن کد گیت‌هاب",
    )
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")
    is_featured = models.BooleanField(default=False, verbose_name="پروژه ویژه")

    class Meta:
        verbose_name = "پروژه نمونه‌کار"
        verbose_name_plural = "پروژه‌ها"
        ordering = ["order", "id"]

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            from django.utils.text import slugify
            base_slug = slugify(self.title, allow_unicode=True) or f"project-{self.pk or 'new'}"
            slug = base_slug
            counter = 1
            while Project.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Category(models.Model):
    title = models.CharField(max_length=100, verbose_name="عنوان دسته")
    slug = models.SlugField(max_length=100, unique=True, allow_unicode=True, verbose_name="اسلاگ")

    class Meta:
        verbose_name = "دسته‌بندی وبلاگ"
        verbose_name_plural = "دسته‌بندی‌های وبلاگ"
        ordering = ["title"]

    def __str__(self):
        return self.title


class BlogPost(models.Model):
    class PostStatus(models.TextChoices):
        DRAFT = "draft", "پیش‌نویس"
        PUBLISHED = "published", "منتشر شده"

    title = models.CharField(max_length=200, verbose_name="عنوان مقاله")
    slug = models.SlugField(
        max_length=220,
        unique=True,
        allow_unicode=True,
        verbose_name="اسلاگ یکتا",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
        verbose_name="دسته‌بندی",
    )
    description = models.TextField(verbose_name="چکیده کوتاه")
    content = models.TextField(verbose_name="متن کامل مقاله")
    cover_image = models.ImageField(
        upload_to="blog_covers/",
        blank=True,
        null=True,
        verbose_name="تصویر شاخص",
    )
    reading_time = models.PositiveIntegerField(
        default=5,
        verbose_name="زمان تخمینی مطالعه (دقیقه)",
    )
    status = models.CharField(
        max_length=10,
        choices=PostStatus.choices,
        default=PostStatus.PUBLISHED,
        verbose_name="وضعیت انتشار",
    )
    published_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان انتشار")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="زمان آخرین به‌روزرسانی")

    class Meta:
        verbose_name = "مقاله وبلاگ"
        verbose_name_plural = "مقالات وبلاگ"
        ordering = ["-published_at"]

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام فرستنده")
    email = models.EmailField(verbose_name="رایانامه")
    subject = models.CharField(max_length=100, verbose_name="موضوع پیام")
    message = models.TextField(verbose_name="متن پیام")
    is_read = models.BooleanField(default=False, verbose_name="خوانده شده")
    ip_hash = models.CharField(max_length=64, blank=True, verbose_name="هش شناسه کاربر")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ثبت")

    class Meta:
        verbose_name = "پیام مخاطب"
        verbose_name_plural = "پیام‌های مخاطبان"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.subject}"


class SocialLink(models.Model):
    url = models.URLField(verbose_name="پیوند اینترنتی")
    icon = models.CharField(max_length=100, verbose_name="کلاس آیکون")

    class Meta:
        verbose_name = "پیوند شبکه اجتماعی"
        verbose_name_plural = "پیوندهای شبکه‌های اجتماعی"

    def __str__(self):
        return self.url
