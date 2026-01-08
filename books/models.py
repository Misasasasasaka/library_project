from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import F, Max, Q
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

    def _sync_copies_and_inventory(self) -> None:
        BookCopy = apps.get_model("books", "BookCopy")
        Borrow = apps.get_model("borrows", "Borrow")

        desired_total = int(self.total_copies or 0)
        if desired_total < 0:
            raise ValidationError({"total_copies": _("total_copies 不能为负数")})

        with transaction.atomic():
            borrowed_count = Borrow.objects.filter(
                book_id=self.id, return_date__isnull=True
            ).count()
            if desired_total < borrowed_count:
                raise ValidationError({"total_copies": _("total_copies 不能小于已借出数量")})

            active_qs = BookCopy.objects.filter(book_id=self.id, is_active=True)
            active_count = active_qs.count()

            if desired_total > active_count:
                max_copy_no = (
                    BookCopy.objects.filter(book_id=self.id).aggregate(max_no=Max("copy_no"))[
                        "max_no"
                    ]
                    or 0
                )
                to_create = []
                for copy_no in range(max_copy_no + 1, max_copy_no + 1 + (desired_total - active_count)):
                    to_create.append(BookCopy(book_id=self.id, copy_no=copy_no, is_active=True))
                BookCopy.objects.bulk_create(to_create)

            if desired_total < active_count:
                borrowed_copy_ids = set(
                    Borrow.objects.filter(book_id=self.id, return_date__isnull=True).values_list(
                        "copy_id", flat=True
                    )
                )
                need_deactivate = active_count - desired_total
                candidates = list(
                    BookCopy.objects.filter(book_id=self.id, is_active=True)
                    .exclude(id__in=borrowed_copy_ids)
                    .order_by("-copy_no")
                    .values_list("id", flat=True)[:need_deactivate]
                )
                if len(candidates) < need_deactivate:
                    raise ValidationError({"total_copies": _("total_copies 不能小于已借出数量")})
                BookCopy.objects.filter(id__in=candidates).update(is_active=False)

            # Recompute totals from source of truth (active copies + open borrows)
            total_active = BookCopy.objects.filter(book_id=self.id, is_active=True).count()
            borrowed_count = Borrow.objects.filter(book_id=self.id, return_date__isnull=True).count()
            available = total_active - borrowed_count
            type(self).objects.filter(pk=self.id).update(
                total_copies=total_active,
                available_copies=available,
            )
            self.total_copies = total_active
            self.available_copies = available

    def save(self, *args, **kwargs):  # type: ignore[override]
        creating = self.pk is None
        previous_total = None
        if not creating:
            previous_total = (
                type(self).objects.filter(pk=self.pk).values_list("total_copies", flat=True).first()
            )

        super().save(*args, **kwargs)

        if creating or (previous_total is not None and previous_total != self.total_copies):
            self._sync_copies_and_inventory()

    def __str__(self) -> str:
        return f"{self.title} ({self.isbn})"


class BookCopy(models.Model):
    book = models.ForeignKey(
        Book,
        verbose_name=_("图书"),
        on_delete=models.CASCADE,
        related_name="copies",
    )
    copy_no = models.PositiveIntegerField(_("副本编号"))
    is_active = models.BooleanField(_("在馆"), default=True)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _("馆藏副本")
        verbose_name_plural = _("馆藏副本")
        ordering = ["book_id", "copy_no"]
        constraints = [
            models.UniqueConstraint(
                fields=["book", "copy_no"],
                name="bookcopy_unique_book_copy_no",
            )
        ]
        indexes = [
            models.Index(fields=["book", "is_active", "copy_no"], name="bookcopy_book_active_no_idx")
        ]

    @property
    def code(self) -> str:
        return str(self.copy_no).zfill(3)

    def __str__(self) -> str:
        return f"{self.book_id}#{self.code}"
