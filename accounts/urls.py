from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('forgot-password/sent/', views.forgot_password_sent_view, name='forgot_password_sent'),
    path('reset-password/<uidb64>/<token>/', views.reset_password_confirm_view, name='reset_password_confirm'),
    path('reset-password/complete/', views.reset_password_complete_view, name='reset_password_complete'),
]