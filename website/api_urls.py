from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api_views import (
    InitialDataAPIView,
    SkillViewSet,
    TechnologyViewSet,
    ProjectViewSet,
    CategoryViewSet,
    BlogPostViewSet,
    ContactCreateAPIView,
)

app_name = "website_api"

router = DefaultRouter()
router.register("skills", SkillViewSet, basename="skill")
router.register("technologies", TechnologyViewSet, basename="technology")
router.register("projects", ProjectViewSet, basename="project")
router.register("categories", CategoryViewSet, basename="category")
router.register("blog", BlogPostViewSet, basename="blog")

urlpatterns = [
    path("init/", InitialDataAPIView.as_view(), name="init"),
    path("contact/", ContactCreateAPIView.as_view(), name="contact"),
    path("", include(router.urls)),
]
