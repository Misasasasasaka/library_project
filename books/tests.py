import io

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from books.admin_csv import import_books_from_csv
from books.models import Book
from borrows.models import Borrow


class BookCsvImportTests(TestCase):
    def test_available_copies_endpoint_includes_never_borrowed_copies(self):
        book = Book.objects.create(
            title="Avail Book",
            author="Author",
            isbn="ISBN-AVAIL-0001",
            total_copies=3,
            available_copies=3,
            status=Book.Status.ON_SHELF,
        )

        resp = self.client.get(f"/api/books/{book.id}/available-copies")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("count"), 3)
        codes = [row.get("code") for row in (data.get("results") or [])]
        self.assertEqual(codes, ["001", "002", "003"])

    def test_import_upsert_keeps_empty_fields(self):
        Book.objects.create(
            title="Old Title",
            author="Old Author",
            isbn="ISBN-CSV-0001",
            publisher="Old Publisher",
            total_copies=3,
            available_copies=3,
            status=Book.Status.ON_SHELF,
        )

        csv_content = (
            "isbn,title,author,publisher,publish_date,description,category_name,total_copies,available_copies,location,status\n"
            "ISBN-CSV-0001,,New Author,,,,,,,\n"
        )
        result = import_books_from_csv(io.StringIO(csv_content))
        self.assertTrue(result["ok"])
        self.assertFalse(result["has_errors"])
        self.assertTrue(result["applied"])
        self.assertEqual(result["updated"], 1)

        book = Book.objects.get(isbn="ISBN-CSV-0001")
        self.assertEqual(book.title, "Old Title")
        self.assertEqual(book.author, "New Author")
        self.assertEqual(book.publisher, "Old Publisher")

    def test_import_total_copies_preserves_borrowed_count(self):
        User = get_user_model()
        user = User.objects.create_user(username="user1", password="pass12345")
        book = Book.objects.create(
            title="Title",
            author="Author",
            isbn="ISBN-CSV-0002",
            total_copies=5,
            available_copies=5,
            status=Book.Status.ON_SHELF,
        )

        copy1 = book.copies.get(copy_no=1)
        copy2 = book.copies.get(copy_no=2)
        Borrow.objects.create(
            user=user,
            book=book,
            copy=copy1,
            due_date=timezone.localdate() + timedelta(days=14),
            status=Borrow.Status.BORROWED,
        )
        Borrow.objects.create(
            user=user,
            book=book,
            copy=copy2,
            due_date=timezone.localdate() + timedelta(days=14),
            status=Borrow.Status.BORROWED,
        )

        book.refresh_from_db()
        self.assertEqual(book.total_copies - book.available_copies, 2)

        csv_content = (
            "isbn,title,author,publisher,publish_date,description,category_name,total_copies,available_copies,location,status\n"
            "ISBN-CSV-0002,,,,,,,6,,,\n"
        )
        result = import_books_from_csv(io.StringIO(csv_content))
        self.assertTrue(result["ok"])
        self.assertFalse(result["has_errors"])

        book.refresh_from_db()
        self.assertEqual(book.total_copies, 6)
        self.assertEqual(book.available_copies, 4)

    def test_import_status_accepts_chinese_values(self):
        csv_content = (
            "isbn,title,author,publisher,publish_date,description,category_name,total_copies,available_copies,location,status\n"
            "ISBN-CSV-0003,Title,Author,,,,,,,,下架\n"
        )
        result = import_books_from_csv(io.StringIO(csv_content))
        self.assertTrue(result["ok"])
        self.assertFalse(result["has_errors"])

        book = Book.objects.get(isbn="ISBN-CSV-0003")
        self.assertEqual(book.status, Book.Status.OFF_SHELF)

    def test_import_invalid_status_error_is_human_readable(self):
        csv_content = (
            "isbn,title,author,publisher,publish_date,description,category_name,total_copies,available_copies,location,status\n"
            "ISBN-CSV-0004,Title,Author,,,,,,,,bad_status\n"
        )
        result = import_books_from_csv(io.StringIO(csv_content))
        self.assertTrue(result["ok"])
        self.assertTrue(result["has_errors"])
        self.assertEqual(result["created"], 0)

        msg = (result.get("errors") or [{}])[0].get("message") or ""
        self.assertIn("status", msg)
        self.assertNotIn("{", msg)

    def test_can_delete_book_even_with_borrow_history(self):
        User = get_user_model()
        user = User.objects.create_user(username="user1", password="pass12345")
        book = Book.objects.create(
            title="Delete Title",
            author="Delete Author",
            isbn="ISBN-DELETE-0001",
            total_copies=1,
            available_copies=1,
            status=Book.Status.ON_SHELF,
        )
        copy = book.copies.get(copy_no=1)

        Borrow.objects.create(
            user=user,
            book=book,
            copy=copy,
            due_date=timezone.localdate() + timedelta(days=14),
            return_date=timezone.now(),
            status=Borrow.Status.RETURNED,
        )

        book.delete()

        self.assertFalse(Book.objects.filter(pk=book.id).exists())
        self.assertFalse(Borrow.objects.filter(book_id=book.id).exists())
