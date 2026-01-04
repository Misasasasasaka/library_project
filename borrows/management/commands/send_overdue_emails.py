from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.utils import timezone
from django.utils.dateparse import parse_date

from borrows.models import OverdueMailLog
from borrows.overdue import build_overdue_email, overdue_borrows_qs


class Command(BaseCommand):
    help = "Send daily overdue reminder emails (merged per user)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="只预览不发送/不落库")
        parser.add_argument("--force", action="store_true", help="忽略当日去重日志，强制发送")
        parser.add_argument("--date", help="指定日期 YYYY-MM-DD（默认 today）")

    def handle(self, *args, **options):
        dry_run = bool(options["dry_run"])
        force = bool(options["force"])

        if options.get("date"):
            today = parse_date(str(options["date"]))
            if today is None:
                raise ValueError("date 格式应为 YYYY-MM-DD")
        else:
            today = timezone.localdate()

        existing_user_ids = set(
            OverdueMailLog.objects.filter(sent_date=today).values_list("user_id", flat=True)
        )

        grouped = {}
        users = {}
        for borrow in overdue_borrows_qs(today):
            grouped.setdefault(borrow.user_id, []).append(borrow)
            users[borrow.user_id] = borrow.user

        if not grouped:
            self.stdout.write("无逾期记录")
            return

        sent = 0
        skipped_no_mail = 0
        skipped_already_sent = 0
        failed = 0

        for user_id, items in grouped.items():
            user = users[user_id]
            mail = (getattr(user, "mail", None) or "").strip()
            if not mail:
                skipped_no_mail += 1
                continue

            if (not force) and (user_id in existing_user_ids):
                skipped_already_sent += 1
                continue

            if dry_run:
                sent += 1
                continue

            log = None
            if not force:
                try:
                    log, created_log = OverdueMailLog.objects.get_or_create(
                        user=user,
                        sent_date=today,
                        defaults={"mail": mail, "borrow_count": len(items)},
                    )
                except IntegrityError:
                    created_log = False

                if not created_log:
                    skipped_already_sent += 1
                    existing_user_ids.add(user_id)
                    continue
                existing_user_ids.add(user_id)

            subject, message = build_overdue_email(user, items, today=today)
            try:
                from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or None
                send_mail(subject, message, from_email, [mail], fail_silently=False)
                if force:
                    OverdueMailLog.objects.update_or_create(
                        user=user,
                        sent_date=today,
                        defaults={
                            "mail": mail,
                            "borrow_count": len(items),
                            "sent_at": timezone.now(),
                        },
                    )
                sent += 1
            except Exception:
                if log is not None:
                    OverdueMailLog.objects.filter(pk=log.pk).delete()
                failed += 1

        self.stdout.write(
            f"date={today.isoformat()} dry_run={dry_run} sent={sent} "
            f"skipped_no_mail={skipped_no_mail} skipped_already_sent={skipped_already_sent} failed={failed}"
        )
