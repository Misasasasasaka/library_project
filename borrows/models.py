from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import F, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Borrow(models.Model):
    class Status(models.TextChoices):
        BORROWED = "borrowed", _("借阅中")
        RETURNED = "returned", _("已归还")
        OVERDUE = "overdue", _("已逾期")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("用户"),
        on_delete=models.CASCADE,
        related_name="borrows",
    )
    book = models.ForeignKey(
        "books.Book",
        verbose_name=_("图书"),
        on_delete=models.CASCADE,
        related_name="borrows",
    )
    borrow_date = models.DateTimeField(_("借阅时间"), auto_now_add=True)
    due_date = models.DateField(_("应还日期"))
    return_date = models.DateTimeField(_("实际归还时间"), null=True, blank=True)
    status = models.CharField(
        _("状态"), max_length=10, choices=Status.choices, default=Status.BORROWED
    )
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _("借阅记录")
        verbose_name_plural = _("借阅记录")
        ordering = ["-borrow_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "book"],
                condition=Q(return_date__isnull=True),
                name="borrow_unique_open_user_book",
            ),
            models.CheckConstraint(
                check=~Q(status="returned") | Q(return_date__isnull=False),
                name="borrow_returned_requires_return_date",
            ),
        ]


    @property
    def is_overdue(self) -> bool:
        if self.status == self.Status.RETURNED:
            return False
        return timezone.localdate() > self.due_date

    def clean(self) -> None:
        if self.status == self.Status.RETURNED and not self.return_date:
            raise ValidationError({"return_date": _("已归还时必须填写实际归还时间")})

        if self.return_date is None:
            qs = type(self).objects.filter(
                user_id=self.user_id, book_id=self.book_id, return_date__isnull=True
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(_("同一用户对同一本书未归还时只能有 1 条借阅记录"))

    def save(self, *args, **kwargs):  # type: ignore[override]
        Book = apps.get_model("books", "Book")

        with transaction.atomic():
            previous = None
            if self.pk:
                previous = (
                    type(self)
                    .objects.filter(pk=self.pk)
                    .values("status", "book_id")
                    .first()
                )

            if previous and previous["book_id"] != self.book_id:
                raise ValidationError(_("不允许修改借阅记录的图书"))

            is_creating = previous is None
            was_returned = bool(previous and previous["status"] == self.Status.RETURNED)
            will_be_returned = self.status == self.Status.RETURNED

            if is_creating and self.status != self.Status.RETURNED:
                updated = (
                    Book.objects.filter(
                        pk=self.book_id,
                        status=Book.Status.ON_SHELF,
                        available_copies__gt=0,
                    )
                    .update(available_copies=F("available_copies") - 1)
                )
                if updated == 0:
                    raise ValidationError(_("该图书不可借或库存不足"))

            if not is_creating and (not was_returned) and will_be_returned:
                if not self.return_date:
                    self.return_date = timezone.now()
                Book.objects.filter(pk=self.book_id).update(
                    available_copies=F("available_copies") + 1
                )

            if not is_creating and was_returned and (not will_be_returned):
                self.return_date = None
                updated = (
                    Book.objects.filter(
                        pk=self.book_id,
                        status=Book.Status.ON_SHELF,
                        available_copies__gt=0,
                    )
                    .update(available_copies=F("available_copies") - 1)
                )
                if updated == 0:
                    raise ValidationError(_("该图书不可借或库存不足"))

            super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.user_id} - {self.book_id} ({self.status})"
