from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    class Role(models.TextChoices):
        USER = "user", _("普通用户")
        ADMIN = "admin", _("管理员")

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    mail = models.EmailField(_("邮箱"), unique=True, null=True, blank=True)

    def __str__(self) -> str:
        return self.get_username()
