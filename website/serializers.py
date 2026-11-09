import re
import html
from rest_framework import serializers
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


class SocialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialLink
        fields = ["id", "url", "icon"]


class HeadlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Headline
        fields = ["id", "text", "order"]


class StatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stat
        fields = ["id", "value", "label", "order"]


class AboutCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutCard
        fields = ["id", "icon", "title", "description", "order"]


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "id",
            "name_fa",
            "name_en",
            "headline",
            "bio_fa",
            "current_status",
            "email",
            "avatar",
            "resume_file",
            "is_available_for_hire",
            "created_at",
            "updated_at",
        ]


class SkillSerializer(serializers.ModelSerializer):
    proficiency = serializers.IntegerField(source="percentage", read_only=True)
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = Skill
        fields = [
            "id",
            "name",
            "category",
            "category_display",
            "percentage",
            "proficiency",
            "order",
            "is_featured",
        ]


class TechnologySerializer(serializers.ModelSerializer):
    class Meta:
        model = Technology
        fields = ["id", "name", "slug"]


class ProjectSerializer(serializers.ModelSerializer):
    technologies = TechnologySerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "image",
            "tag",
            "technologies",
            "demo_url",
            "github_url",
            "order",
            "is_featured",
        ]


class CategorySerializer(serializers.ModelSerializer):
    posts_count = serializers.IntegerField(source="posts.count", read_only=True)

    class Meta:
        model = Category
        fields = ["id", "title", "slug", "posts_count"]


class BlogPostListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "category",
            "description",
            "cover_image",
            "reading_time",
            "published_at",
        ]


class BlogPostDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "category",
            "description",
            "content",
            "cover_image",
            "reading_time",
            "published_at",
            "updated_at",
        ]


class ContactMessageSerializer(serializers.ModelSerializer):
    # فیلد هانی‌پات برای به دام انداختن بات‌های هرزنامه‌ساز
    website_source_url = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        help_text="تله هرزنامه؛ باید خالی ارسال شود",
    )

    class Meta:
        model = ContactMessage
        fields = [
            "name",
            "email",
            "subject",
            "message",
            "website_source_url",
        ]

    def validate_name(self, value):
        cleaned = html.escape(value.strip())
        if len(cleaned) < 2:
            raise serializers.ValidationError("نام باید حداقل شامل ۲ کاراکتر باشد.")
        if len(cleaned) > 100:
            raise serializers.ValidationError("نام نمی‌تواند بیش از ۱۰۰ کاراکتر باشد.")
        return cleaned

    def validate_subject(self, value):
        cleaned = html.escape(value.strip())
        if len(cleaned) < 3:
            raise serializers.ValidationError("موضوع پیام باید حداقل شامل ۳ کاراکتر باشد.")
        if len(cleaned) > 150:
            raise serializers.ValidationError("موضوع پیام نمی‌تواند بیش از ۱۵۰ کاراکتر باشد.")
        return cleaned

    def validate_message(self, value):
        cleaned = html.escape(value.strip())
        if len(cleaned) < 10:
            raise serializers.ValidationError("متن پیام باید حداقل شامل ۱۰ کاراکتر باشد.")
        if len(cleaned) > 3000:
            raise serializers.ValidationError("متن پیام نمی‌تواند بیش از ۳۰۰۰ کاراکتر باشد.")
        return cleaned

    def create(self, validated_data):
        # حذف فیلد هانی‌پات پیش از ذخیره در دیتابیس
        validated_data.pop("website_source_url", None)
        return super().create(validated_data)
