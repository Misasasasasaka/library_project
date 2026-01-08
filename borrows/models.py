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
    copy = models.ForeignKey(
        "books.BookCopy",
        verbose_name=_("副本"),
        on_delete=models.PROTECT,
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
                fields=["copy"],
                condition=Q(return_date__isnull=True),
                name="borrow_unique_open_copy",
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

        if not self.copy_id:
            raise ValidationError({"copy": _("copy 为必填")})

        if self.copy_id and self.book_id and getattr(self, "copy", None):
            if self.copy.book_id != self.book_id:
                raise ValidationError({"copy": _("副本不属于该图书")})

        if self.return_date is None:
            qs = type(self).objects.filter(
                copy_id=self.copy_id, return_date__isnull=True
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(_("该副本未归还时只能有 1 条借阅记录"))

    def save(self, *args, **kwargs):  # type: ignore[override]
        Book = apps.get_model("books", "Book")
        BookCopy = apps.get_model("books", "BookCopy")

        with transaction.atomic():
            previous = None
            if self.pk:
                previous = (
                    type(self)
                    .objects.filter(pk=self.pk)
                    .values("status", "book_id", "copy_id")
                    .first()
                )

            if previous and previous["book_id"] != self.book_id:
                raise ValidationError(_("不允许修改借阅记录的图书"))
            if previous and previous["copy_id"] != self.copy_id:
                raise ValidationError(_("不允许修改借阅记录的副本"))

            is_creating = previous is None
            was_returned = bool(previous and previous["status"] == self.Status.RETURNED)
            will_be_returned = self.status == self.Status.RETURNED

            if is_creating and self.status != self.Status.RETURNED:
                copy = (
                    BookCopy.objects.select_related("book")
                    .filter(pk=self.copy_id, book_id=self.book_id, is_active=True)
                    .first()
                )
                if copy is None:
                    raise ValidationError(_("副本不存在或不可借"))

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
                copy = (
                    BookCopy.objects.select_related("book")
                    .filter(pk=self.copy_id, book_id=self.book_id, is_active=True)
                    .first()
                )
                if copy is None:
                    raise ValidationError(_("副本不存在或不可借"))
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


class OverdueMailLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("用户"),
        on_delete=models.CASCADE,
        related_name="overdue_mail_logs",
    )
    mail = models.EmailField(_("收件邮箱"), blank=True)
    sent_date = models.DateField(_("发送日期"))
    sent_at = models.DateTimeField(_("发送时间"), auto_now_add=True)
    borrow_count = models.PositiveIntegerField(_("逾期条数"), default=0)

    class Meta:
        verbose_name = _("逾期通知日志")
        verbose_name_plural = _("逾期通知日志")
        ordering = ["-sent_date", "-sent_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "sent_date"],
                name="overduemaillog_unique_user_sent_date",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} {self.sent_date} ({self.borrow_count})"
