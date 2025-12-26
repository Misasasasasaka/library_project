from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "mail", "role", "is_staff", "is_superuser", "is_active")
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "mail", "email")

    fieldsets = DjangoUserAdmin.fieldsets + (
        (_("角色信息"), {"fields": ("role", "mail")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (None, {"fields": ("role", "mail")}),
    )
