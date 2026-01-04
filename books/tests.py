import io

from django.test import TestCase

from books.admin_csv import import_books_from_csv
from books.models import Book


class BookCsvImportTests(TestCase):
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
        book = Book.objects.create(
            title="Title",
            author="Author",
            isbn="ISBN-CSV-0002",
            total_copies=5,
            available_copies=3,
            status=Book.Status.ON_SHELF,
        )
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
