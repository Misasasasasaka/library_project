from django.urls import path

from . import views


urlpatterns = [
    path("csrf", views.csrf, name="csrf"),
    path("captcha", views.captcha, name="captcha"),
    path("email-code", views.send_email_code, name="email-code"),
    path("register", views.register, name="register"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("me", views.me, name="me"),
]
