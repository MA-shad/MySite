import hashlib
from rest_framework import viewsets, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from django.db.models import Prefetch

from .models import (
    Profile,
    Headline,
    Stat,
    AboutCard,
    Skill,
    Technology,
    Project,
    Category,
    BlogPost,
    ContactMessage,
    SocialLink,
)
from .serializers import (
    ProfileSerializer,
    HeadlineSerializer,
    StatSerializer,
    AboutCardSerializer,
    SocialLinkSerializer,
    SkillSerializer,
    TechnologySerializer,
    ProjectSerializer,
    CategorySerializer,
    BlogPostListSerializer,
    BlogPostDetailSerializer,
    ContactMessageSerializer,
)
from .throttles import ContactRateThrottle, ContactBurstThrottle


class InitialDataAPIView(APIView):
    """
    اندپوینت تجمیعی برای بارگذاری اولیه پورتفولیو در قالب یک درخواست بهینه.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        profile = Profile.objects.first()
        headlines = Headline.objects.all().order_by("order")
        stats = Stat.objects.all().order_by("order")
        about_cards = AboutCard.objects.all().order_by("order")
        social_links = SocialLink.objects.all()
        featured_skills = Skill.objects.filter(is_featured=True).order_by("order", "-percentage")
        featured_projects = (
            Project.objects.prefetch_related("technologies")
            .filter(is_featured=True)
            .order_by("order")
        )
        if not featured_projects.exists():
            # در صورت عدم انتخاب پروژه شاخص، ۳ پروژه اول نمایش داده می‌شوند
            featured_projects = (
                Project.objects.prefetch_related("technologies")
                .all()
                .order_by("order")[:3]
            )

        data = {
            "profile": ProfileSerializer(profile).data if profile else None,
            "headlines": HeadlineSerializer(headlines, many=True).data,
            "stats": StatSerializer(stats, many=True).data,
            "about_cards": AboutCardSerializer(about_cards, many=True).data,
            "social_links": SocialLinkSerializer(social_links, many=True).data,
            "featured_skills": SkillSerializer(featured_skills, many=True).data,
            "featured_projects": ProjectSerializer(featured_projects, many=True).data,
        }
        return Response(data, status=status.HTTP_200_OK)


class SkillViewSet(viewsets.ReadOnlyModelViewSet):
    """
    فهرست مهارت‌ها با قابلیت فیلتر بر اساس دسته‌بندی موضوعی.
    مثال: /api/v1/skills/?category=backend
    """
    queryset = Skill.objects.all().order_by("order", "-percentage")
    serializer_class = SkillSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category.lower())
        return qs


class TechnologyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    فهرست فناوری‌های پروژه‌محور.
    """
    queryset = Technology.objects.all()
    serializer_class = TechnologySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"


class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    فهرست پروژه‌ها همراه با پشته فناوری بهینه‌شده با prefetch_related.
    فیلترها:
      ?technology=django
      ?featured=true
    """
    queryset = Project.objects.prefetch_related("technologies").all().order_by("order", "id")
    serializer_class = ProjectSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

    def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]
        # در صورتی که پارامتر ارسالی عدد باشد بر اساس id و در غیر این صورت بر اساس slug واکشی می‌شود
        if lookup_value.isdigit():
            return Project.objects.prefetch_related("technologies").get(id=int(lookup_value))
        return super().get_object()

    def get_queryset(self):
        qs = super().get_queryset()
        tech_slug = self.request.query_params.get("technology")
        if tech_slug:
            qs = qs.filter(technologies__slug=tech_slug)
        featured = self.request.query_params.get("featured")
        if featured is not None:
            if featured.lower() in ["true", "1"]:
                qs = qs.filter(is_featured=True)
            elif featured.lower() in ["false", "0"]:
                qs = qs.filter(is_featured=False)
        return qs.distinct()


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    دسته‌بندی‌های وبلاگ.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"


class BlogPostViewSet(viewsets.ReadOnlyModelViewSet):
    """
    فهرست و متن کامل مقالات منتشرشده وبلاگ.
    فیلترها:
      ?category=slug
    """
    queryset = (
        BlogPost.objects.select_related("category")
        .filter(status=BlogPost.PostStatus.PUBLISHED)
        .order_by("-published_at")
    )
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return BlogPostDetailSerializer
        return BlogPostListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        category_slug = self.request.query_params.get("category")
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        return qs


class ContactCreateAPIView(CreateAPIView):
    """
    ثبت پیام مخاطبان با پشتیبانی از تراتلینگ، هانی‌پات و هش نشانی آی‌پی.
    """
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ContactRateThrottle, ContactBurstThrottle]

    def create(self, request, *args, **kwargs):
        # ۱. بررسی تله هرزنامه (Honeypot)
        honeypot = request.data.get("website_source_url")
        if honeypot:
            # بات شناسایی شد؛ بدون ذخیره در دیتابیس پیام ساختگی موفق ارسال می‌شود
            return Response(
                {"detail": "پیام شما دریافت شد."},
                status=status.HTTP_201_CREATED,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # ۲. محاسبه هش نشانی آی‌پی برای حفظ حریم خصوصی
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "")

        ip_hash = hashlib.sha256(ip.encode("utf-8")).hexdigest() if ip else ""

        # ۳. ذخیره ایمن
        contact_message = serializer.save(ip_hash=ip_hash)

        return Response(
            {
                "detail": "پیام شما با موفقیت ثبت شد و در اولین فرصت بررسی خواهد شد.",
                "id": contact_message.id,
            },
            status=status.HTTP_201_CREATED,
        )
