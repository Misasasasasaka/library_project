from datetime import timedelta
import io

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core import mail
from django.test import TestCase
from django.test import override_settings
from django.utils import timezone

from books.models import Book

from .models import Borrow, OverdueMailLog


class BorrowModelTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="user1", password="pass12345")
        self.book = Book.objects.create(
            title="Test Book",
            author="Author",
            isbn="ISBN-0001",
            total_copies=2,
            available_copies=2,
            status=Book.Status.ON_SHELF,
        )
        self.copy1 = self.book.copies.get(copy_no=1)
        self.copy2 = self.book.copies.get(copy_no=2)

    def test_borrow_decrements_available_copies(self):
        borrow = Borrow(
            user=self.user,
            book=self.book,
            copy=self.copy1,
            due_date=timezone.localdate() + timedelta(days=14),
        )
        borrow.full_clean()
        borrow.save()

        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 1)

    def test_return_increments_available_copies(self):
        borrow = Borrow.objects.create(
            user=self.user,
            book=self.book,
            copy=self.copy1,
            due_date=timezone.localdate() + timedelta(days=14),
            status=Borrow.Status.BORROWED,
        )
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 1)

        borrow.status = Borrow.Status.RETURNED
        borrow.return_date = timezone.now()
        borrow.full_clean()
        borrow.save()

        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 2)

    def test_user_can_borrow_multiple_copies_of_same_book(self):
        Borrow.objects.create(
            user=self.user,
            book=self.book,
            copy=self.copy1,
            due_date=timezone.localdate() + timedelta(days=14),
            status=Borrow.Status.BORROWED,
        )

        borrow2 = Borrow(
            user=self.user,
            book=self.book,
            copy=self.copy2,
            due_date=timezone.localdate() + timedelta(days=14),
            status=Borrow.Status.BORROWED,
        )
        borrow2.full_clean()
        borrow2.save()

        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 0)

    def test_unique_open_borrow_per_copy(self):
        Borrow.objects.create(
            user=self.user,
            book=self.book,
            copy=self.copy1,
            due_date=timezone.localdate() + timedelta(days=14),
            status=Borrow.Status.BORROWED,
        )

        User = get_user_model()
        user2 = User.objects.create_user(username="user2", password="pass12345")
        borrow = Borrow(
            user=user2,
            book=self.book,
            copy=self.copy1,
            due_date=timezone.localdate() + timedelta(days=14),
            status=Borrow.Status.BORROWED,
        )
        with self.assertRaises(ValidationError):
            borrow.full_clean()


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="no-reply@example.com",
)
class OverdueEmailCommandTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="overdue_user",
            password="pass12345",
            mail="overdue@example.com",
        )
        self.book = Book.objects.create(
            title="Overdue Book",
            author="Author",
            isbn="ISBN-OVERDUE-0001",
            total_copies=1,
            available_copies=1,
            status=Book.Status.ON_SHELF,
        )
        self.copy1 = self.book.copies.get(copy_no=1)

    def test_send_overdue_emails_creates_log_and_dedupes(self):
        Borrow.objects.create(
            user=self.user,
            book=self.book,
            copy=self.copy1,
            due_date=timezone.localdate() - timedelta(days=1),
            status=Borrow.Status.BORROWED,
        )

        call_command("send_overdue_emails", verbosity=0, stdout=io.StringIO())
        self.assertEqual(OverdueMailLog.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

        call_command("send_overdue_emails", verbosity=0, stdout=io.StringIO())
        self.assertEqual(OverdueMailLog.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_send_overdue_emails_dry_run_does_not_persist(self):
        Borrow.objects.create(
            user=self.user,
            book=self.book,
            copy=self.copy1,
            due_date=timezone.localdate() - timedelta(days=1),
            status=Borrow.Status.BORROWED,
        )

        call_command("send_overdue_emails", "--dry-run", verbosity=0, stdout=io.StringIO())
        self.assertEqual(OverdueMailLog.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)
