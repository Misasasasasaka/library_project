import json

from django.core.management.base import BaseCommand

from books.admin_csv import import_books_from_csv, wrap_uploaded_file


class Command(BaseCommand):
    help = "Import books from CSV (upsert by isbn)."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="CSV 文件路径（UTF-8/UTF-8-BOM）")
        parser.add_argument("--dry-run", action="store_true", help="只校验不写入")
        parser.add_argument("--atomic", action="store_true", help="任一行失败则整批回滚")

    def handle(self, *args, **options):
        path = options["file"]
        dry_run = bool(options["dry_run"])
        atomic = bool(options["atomic"])

        with open(path, "rb") as bf:
            with wrap_uploaded_file(bf) as f:
                result = import_books_from_csv(f, dry_run=dry_run, atomic=atomic)

        self.stdout.write(json.dumps(result, ensure_ascii=False))

