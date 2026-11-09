from django.contrib import admin
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


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name_fa",
        "name_en",
        "headline",
        "email",
        "is_available_for_hire",
        "updated_at",
    )
    search_fields = ("name_fa", "name_en", "email", "headline")


@admin.register(Headline)
class HeadlineAdmin(admin.ModelAdmin):
    list_display = ("id", "text", "order")
    list_editable = ("order",)
    ordering = ("order",)
    search_fields = ("text",)


@admin.register(Stat)
class StatAdmin(admin.ModelAdmin):
    list_display = ("id", "label", "value", "order")
    list_editable = ("order",)
    ordering = ("order",)
    search_fields = ("label", "value")


@admin.register(AboutCard)
class AboutCardAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "icon", "order")
    list_editable = ("order",)
    ordering = ("order",)
    search_fields = ("title", "description")


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "percentage", "order", "is_featured")
    list_editable = ("percentage", "order", "is_featured")
    list_filter = ("category", "is_featured")
    search_fields = ("name",)
    ordering = ("order", "-percentage")


@admin.register(Technology)
class TechnologyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "slug",
        "demo_url",
        "github_url",
        "order",
        "is_featured",
    )
    list_editable = ("order", "is_featured")
    list_filter = ("is_featured", "technologies")
    search_fields = ("title", "description")
    filter_horizontal = ("technologies",)
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "slug")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "slug",
        "category",
        "status",
        "reading_time",
        "published_at",
    )
    list_filter = ("status", "category", "published_at")
    list_editable = ("status", "reading_time")
    search_fields = ("title", "description", "content")
    date_hierarchy = "published_at"
    prepopulated_fields = {"slug": ("title",)}


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "subject", "is_read", "created_at")
    list_editable = ("is_read",)
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("name", "email", "subject", "message", "ip_hash", "created_at")
    date_hierarchy = "created_at"


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ("id", "url", "icon")
    search_fields = ("url", "icon")
