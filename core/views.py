from django.shortcuts import render


def home(request):
    return render(request, "core/home.html")


def detail(request):
    """Unified About / FAQ / Contact page."""
    return render(request, "core/detail.html")


def about(request):
    return render(request, "core/detail.html")


def faq(request):
    return render(request, "core/detail.html")


def contact(request):
    return render(request, "core/detail.html")
