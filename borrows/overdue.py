from .models import Borrow


def overdue_borrows_qs(today):
    return (
        Borrow.objects.select_related("book", "user")
        .filter(return_date__isnull=True, due_date__lt=today)
        .exclude(status=Borrow.Status.RETURNED)
        .order_by("user_id", "due_date", "id")
    )


def serialize_overdue_item(borrow: Borrow, *, today):
    overdue_days = (today - borrow.due_date).days
    if overdue_days < 0:
        overdue_days = 0
    return {
        "id": borrow.id,
        "book": {"id": borrow.book_id, "title": borrow.book.title, "isbn": borrow.book.isbn},
        "due_date": borrow.due_date.isoformat(),
        "overdue_days": overdue_days,
    }


def build_overdue_email(user, items: list[Borrow], *, today):
    subject = f"图书逾期提醒（{today.isoformat()}）"
    lines = [
        f"{user.get_username()}，你好：",
        "",
        f"你有 {len(items)} 本书已逾期，请尽快归还：",
    ]
    for borrow in items:
        overdue_days = (today - borrow.due_date).days
        lines.append(
            f"- {borrow.book.title}（{borrow.book.isbn}），应还日期：{borrow.due_date.isoformat()}，逾期 {overdue_days} 天"
        )
    lines.extend(["", "如已归还请忽略本邮件。"])
    return subject, "\n".join(lines)
