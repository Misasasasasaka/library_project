import csv

from django.utils import timezone

from .models import Borrow


BORROW_CSV_COLUMNS = [
    "id",
    "user_id",
    "username",
    "mail",
    "book_id",
    "copy_no",
    "copy_code",
    "title",
    "isbn",
    "borrow_date",
    "due_date",
    "return_date",
    "status",
    "is_overdue",
]


def _effective_status(borrow: Borrow) -> str:
    if borrow.status != Borrow.Status.RETURNED and borrow.is_overdue:
        return Borrow.Status.OVERDUE
    return borrow.status


def export_borrows_to_csv(qs, out) -> None:
    writer = csv.DictWriter(out, fieldnames=BORROW_CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()

    today = timezone.localdate()
    for borrow in qs.select_related("user", "book", "copy").order_by("id"):
        user = borrow.user
        book = borrow.book
        copy_no = getattr(getattr(borrow, "copy", None), "copy_no", None)
        writer.writerow(
            {
                "id": borrow.id,
                "user_id": borrow.user_id,
                "username": user.get_username(),
                "mail": getattr(user, "mail", "") or "",
                "book_id": borrow.book_id,
                "copy_no": copy_no if copy_no is not None else "",
                "copy_code": str(copy_no).zfill(3) if copy_no is not None else "",
                "title": book.title,
                "isbn": book.isbn,
                "borrow_date": borrow.borrow_date.isoformat() if borrow.borrow_date else "",
                "due_date": borrow.due_date.isoformat() if borrow.due_date else "",
                "return_date": borrow.return_date.isoformat() if borrow.return_date else "",
                "status": _effective_status(borrow),
                "is_overdue": 1 if (borrow.return_date is None and borrow.due_date and borrow.due_date < today) else 0,
            }
        )
