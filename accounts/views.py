from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .forms import ForgotPasswordForm, LoginForm, RegisterForm, SetNewPasswordForm
from .models import User


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully.")
            return redirect('accounts:login')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('classroom:classroom')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            if request.POST.get('remember_me'):
                # Persist the session cookie for SESSION_COOKIE_AGE
                # instead of expiring it when the browser closes.
                request.session.set_expiry(settings.SESSION_COOKIE_AGE)
            else:
                request.session.set_expiry(0)
            return redirect('classroom:classroom')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('accounts:login')


def forgot_password_view(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            for user in form.get_users():
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                reset_url = request.build_absolute_uri(
                    reverse('accounts:reset_password_confirm', args=[uid, token])
                )
                send_mail(
                    subject="Reset your READScore password",
                    message=(
                        f"Hi {user.get_full_name() or user.username},\n\n"
                        "You (or someone else) requested a password reset for your "
                        "READScore account. Click the link below to choose a new "
                        "password. This link can only be used once and will expire "
                        "after a few days.\n\n"
                        f"{reset_url}\n\n"
                        "If you didn't request this, you can safely ignore this email."
                    ),
                    from_email=None,
                    recipient_list=[user.email],
                )
            # Always show the same confirmation, whether or not the email
            # matched an account — this avoids leaking which emails are
            # registered.
            return redirect('accounts:forgot_password_sent')
    else:
        form = ForgotPasswordForm()
    return render(request, 'accounts/forgot_password.html', {'form': form})


def forgot_password_sent_view(request):
    return render(request, 'accounts/forgot_password_sent.html')


def reset_password_confirm_view(request, uidb64, token):
    user = None
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    token_valid = user is not None and default_token_generator.check_token(user, token)

    if not token_valid:
        return render(request, 'accounts/reset_password_confirm.html', {
            'token_valid': False,
        })

    if request.method == 'POST':
        form = SetNewPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your password has been reset. You can now log in.")
            return redirect('accounts:reset_password_complete')
    else:
        form = SetNewPasswordForm(user)

    return render(request, 'accounts/reset_password_confirm.html', {
        'token_valid': True,
        'form': form,
    })


def reset_password_complete_view(request):
    return render(request, 'accounts/reset_password_complete.html')