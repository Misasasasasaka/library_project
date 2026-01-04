from django.core.management.base import BaseCommand

from borrows.admin_csv import export_borrows_to_csv
from borrows.models import Borrow


class Command(BaseCommand):
    help = "Export borrows as CSV (utf-8-sig)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default="-",
            help="输出文件路径，默认 '-' 表示输出到 stdout",
        )

    def handle(self, *args, **options):
        import sys

        output = options["output"]
        qs = Borrow.objects.all()

        if output == "-":
            sys.stdout.write("\ufeff")
            export_borrows_to_csv(qs, sys.stdout)
            return

        with open(output, "w", encoding="utf-8-sig", newline="") as f:
            export_borrows_to_csv(qs, f)

        self.stdout.write(f"已导出 {qs.count()} 条 Borrow 到 {output}")
