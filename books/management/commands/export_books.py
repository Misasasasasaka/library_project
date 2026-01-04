from django.core.management.base import BaseCommand

from books.admin_csv import export_books_to_csv
from books.models import Book


class Command(BaseCommand):
    help = "Export books as CSV (utf-8-sig)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default="-",
            help="输出文件路径，默认 '-' 表示输出到 stdout",
        )

    def handle(self, *args, **options):
        import sys

        output = options["output"]
        qs = Book.objects.all()

        if output == "-":
            sys.stdout.write("\ufeff")
            export_books_to_csv(qs, sys.stdout)
            return

        with open(output, "w", encoding="utf-8-sig", newline="") as f:
            export_books_to_csv(qs, f)

        self.stdout.write(f"已导出 {qs.count()} 条 Book 到 {output}")
