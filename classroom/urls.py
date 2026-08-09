from django.urls import path
from . import views

app_name = 'classroom'

urlpatterns = [
    path("", views.classroom_view, name="classroom"),
    path("class/<str:class_code>/", views.class_detail, name="class_detail"),
    path("class/<str:class_code>/delete/", views.delete_class, name="delete_class"),
    path("class/<str:class_code>/unenroll/", views.unenroll_class, name="unenroll_class"),
    path("class/<str:class_code>/remove-student/<int:student_id>/", views.remove_student, name="remove_student"),
    path("class/<str:class_code>/dashboard/", views.dashboard_view, name="dashboard"),
    path("test/<str:test_code>/", views.take_test, name="take_test"),
    path("test/<str:test_code>/passage/", views.passage_intro, name="passage_intro"),
    path("delete/<str:test_code>/", views.delete_test, name="delete_test"),
    path("result/<str:test_code>/", views.student_result, name="student_result"),
    path("test/<str:test_code>/results/", views.teacher_test_results, name="teacher_test_results"),
    path("test/<str:test_code>/results/export/", views.export_test_results, name="export_test_results"),
]