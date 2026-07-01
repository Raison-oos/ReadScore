from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('teacher-panel/', views.teacher_panel_view, name='teacher_panel'),
    path('student-panel/', views.student_panel_view, name='student_panel'),
]