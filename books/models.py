from django.db import models
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    name = models.CharField(_("分类名称"), max_length=100, unique=True)
    description = models.TextField(_("简介"), blank=True)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _("分类")
        verbose_name_plural = _("分类")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Book(models.Model):
    class Status(models.TextChoices):
        ON_SHELF = "on_shelf", _("上架")
        OFF_SHELF = "off_shelf", _("下架")

    title = models.CharField(_("书名"), max_length=200, db_index=True)
    author = models.CharField(_("作者"), max_length=100, db_index=True)
    isbn = models.CharField(_("ISBN"), max_length=32, unique=True, db_index=True)
    publisher = models.CharField(_("出版社"), max_length=200, blank=True)
    publish_date = models.DateField(_("出版日期"), null=True, blank=True)
    description = models.TextField(_("简介"), blank=True)
    category = models.ForeignKey(
        Category,
        verbose_name=_("分类"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="books",
    )
    cover = models.FileField(_("封面"), upload_to="covers/", null=True, blank=True)
    total_copies = models.PositiveIntegerField(_("总数量"), default=1)
    available_copies = models.PositiveIntegerField(_("可借数量"), default=1)
    location = models.CharField(_("书架位置"), max_length=100, blank=True)
    status = models.CharField(
        _("状态"), max_length=20, choices=Status.choices, default=Status.ON_SHELF
    )
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _("图书")
        verbose_name_plural = _("图书")
        constraints = [
            models.CheckConstraint(
                check=Q(available_copies__lte=F("total_copies")),
                name="book_available_lte_total",
            ),
        ]

    @property
    def can_borrow(self) -> bool:
        return self.status == self.Status.ON_SHELF and self.available_copies > 0

    def __str__(self) -> str:
        return f"{self.title} ({self.isbn})"
