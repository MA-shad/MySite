from website.models import *
from .forms import ContactForm
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from django.shortcuts import render, get_object_or_404


def home_view(request):
    if request.method == "POST":
        form = ContactForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "پیام شما با موفقیت ارسال شد.")
            return redirect(reverse("website:home") + "#contact")
    else:
        form = ContactForm()

    headlines = list(
        Headline.objects
        .order_by("order")
        .values_list("text", flat=True)
    )
    about_cards = AboutCard.objects.all().order_by("order")
    stats = Stat.objects.all().order_by("order")
    skills = Skill.objects.all().order_by("id")
    projects = Project.objects.all().prefetch_related("technologies").order_by("id")


    categories = Category.objects.all()
    selected_category_slug = request.GET.get("category")

    published_posts = BlogPost.objects.filter(status=BlogPost.PostStatus.PUBLISHED)
    if selected_category_slug:
        blogposts = published_posts.filter(category__slug=selected_category_slug).order_by("-published_at")
    else:
        blogposts = published_posts.order_by("-published_at")


    context = {
        "headlines": headlines,
        "stats": stats,
        "about_cards": about_cards,
        "skills": skills,
        "projects": projects,
        "blogposts": blogposts,
        "categories": categories,
        "selected_category_slug": selected_category_slug,
        "form": form,
    }

    return render(request, "home.html", context)


def blog_detail(request, id=None, slug=None):

    if id is not None:
        blogpost = get_object_or_404(
            BlogPost,
            id=id,
            status=BlogPost.PostStatus.PUBLISHED,
        )

    else:
        blogpost = get_object_or_404(
            BlogPost,
            slug=slug,
            status=BlogPost.PostStatus.PUBLISHED,
        )

    return render(
        request,
        "blog_detail.html",
        {
            "blogpost": blogpost
        }
    )


def test_view(request):

    if request.method == "POST":
        print(request.POST.get("name"))

    return render(request, "test.html")
