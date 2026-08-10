from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("detail/", views.detail, name="detail"),
    path("about/", views.about, name="about"),
    path("faq/", views.faq, name="faq"),
    path("contact/", views.contact, name="contact"),
]