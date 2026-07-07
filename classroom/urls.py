from django.urls import path
from . import views

app_name = 'classroom'

urlpatterns = [
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("", views.classroom_view, name="classroom"),
    #path("", views.test_code_entry, name="test_code_entry"),
    path("test/<str:test_code>/", views.take_test, name="take_test"),
    path("/delete/<str:test_code>/", views.delete_test, name="delete_test"),
    path("result/<str:test_code>/", views.student_result, name="student_result"),
]