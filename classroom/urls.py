from django.urls import path
from . import views

app_name = 'classroom'

urlpatterns = [
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("", views.classroom_view, name="classroom"),
    #path("", views.test_code_entry, name="test_code_entry"),
    path("take-test/<str:test_code>/", views.take_test, name="take_test"),
]