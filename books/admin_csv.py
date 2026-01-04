import csv
import io
from dataclasses import dataclass
from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.dateparse import parse_date

from .models import Book, Category


CLEAR_TOKEN = "__CLEAR__"

BOOK_CSV_COLUMNS = [
    "isbn",
    "title",
    "author",
    "publisher",
    "publish_date",
    "description",
    "category_name",
    "total_copies",
    "available_copies",
    "location",
    "status",
]


@dataclass(slots=True)
class ImportErrorItem:
    row: int
    isbn: str | None
    message: str

    def to_dict(self) -> dict:
        return {"row": self.row, "isbn": self.isbn, "message": self.message}


def _normalize_cell(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def export_books_to_csv(qs, out) -> None:
    writer = csv.DictWriter(out, fieldnames=BOOK_CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()

    for book in qs.select_related("category").order_by("id"):
        writer.writerow(
            {
                "isbn": book.isbn,
                "title": book.title,
                "author": book.author,
                "publisher": book.publisher,
                "publish_date": book.publish_date.isoformat() if book.publish_date else "",
                "description": book.description,
                "category_name": book.category.name if book.category_id else "",
                "total_copies": book.total_copies,
                "available_copies": book.available_copies,
                "location": book.location,
                "status": book.status,
            }
        )


def _apply_clearable_text(book: Book, field: str, value: str) -> bool:
    if value == "":
        return False
    if value == CLEAR_TOKEN:
        if getattr(book, field) != "":
            setattr(book, field, "")
            return True
        return False
    if getattr(book, field) != value:
        setattr(book, field, value)
        return True
    return False


def _apply_clearable_optional_date(book: Book, field: str, value: str) -> bool:
    if value == "":
        return False
    if value == CLEAR_TOKEN:
        if getattr(book, field) is not None:
            setattr(book, field, None)
            return True
        return False

    parsed: date | None = parse_date(value)
    if parsed is None:
        raise ValidationError({field: f"{field} 格式应为 YYYY-MM-DD"})
    if getattr(book, field) != parsed:
        setattr(book, field, parsed)
        return True
    return False


def _apply_status(book: Book, value: str) -> bool:
    if value == "":
        return False
    if value == CLEAR_TOKEN:
        raise ValidationError({"status": "status 不支持清空"})
    if value not in {Book.Status.ON_SHELF, Book.Status.OFF_SHELF}:
        raise ValidationError({"status": "status 只能为 on_shelf/off_shelf"})
    if book.status != value:
        book.status = value
        return True
    return False


def _apply_required_text(book: Book, field: str, value: str, *, creating: bool) -> bool:
    if value == "":
        if creating:
            raise ValidationError({field: f"{field} 为必填"})
        return False
    if value == CLEAR_TOKEN:
        raise ValidationError({field: f"{field} 不支持清空"})
    if getattr(book, field) != value:
        setattr(book, field, value)
        return True
    return False


def _parse_int_field(value: str, *, field: str) -> int | None:
    if value == "":
        return None
    if value == CLEAR_TOKEN:
        raise ValidationError({field: f"{field} 不支持清空"})
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValidationError({field: f"{field} 必须是整数"}) from exc
    return parsed


def import_books_from_csv(
    uploaded,
    *,
    dry_run: bool = False,
    atomic: bool = False,
) -> dict:
    """
    规则：
    - 主键 isbn：存在则更新，不存在则创建
    - 空字段：保持原值
    - __CLEAR__：仅对允许清空的字段生效（publish_date/category/location/publisher/description）
    """

    errors: list[ImportErrorItem] = []
    created = 0
    updated = 0
    skipped = 0

    def process() -> None:
        nonlocal created, updated, skipped

        reader = csv.DictReader(uploaded)
        if not reader.fieldnames:
            errors.append(ImportErrorItem(row=1, isbn=None, message="CSV 表头缺失"))
            return

        for idx, row in enumerate(reader, start=2):
            if row is None:
                continue

            isbn = _normalize_cell(row.get("isbn"))
            if not isbn:
                skipped += 1
                errors.append(ImportErrorItem(row=idx, isbn=None, message="isbn 为必填"))
                continue

            try:
                book = Book.objects.select_related("category").filter(isbn=isbn).first()
                creating = book is None
                if creating:
                    book = Book(isbn=isbn)

                changed = False

                changed |= _apply_required_text(book, "title", _normalize_cell(row.get("title")), creating=creating)
                changed |= _apply_required_text(book, "author", _normalize_cell(row.get("author")), creating=creating)
                changed |= _apply_clearable_text(book, "publisher", _normalize_cell(row.get("publisher")))
                changed |= _apply_clearable_optional_date(
                    book, "publish_date", _normalize_cell(row.get("publish_date"))
                )
                changed |= _apply_clearable_text(book, "description", _normalize_cell(row.get("description")))

                category_name = _normalize_cell(row.get("category_name"))
                if category_name != "":
                    if category_name == CLEAR_TOKEN:
                        if book.category_id is not None:
                            book.category = None
                            changed = True
                    else:
                        if dry_run:
                            current_name = None
                            if book.category_id:
                                current_name = getattr(book.category, "name", None)
                            if current_name != category_name:
                                changed = True

                            category = Category.objects.filter(name=category_name).first()
                            if category and book.category_id != category.id:
                                book.category = category
                        else:
                            category, _ = Category.objects.get_or_create(name=category_name)
                            if book.category_id != category.id:
                                book.category = category
                                changed = True

                total_raw = _normalize_cell(row.get("total_copies"))
                available_raw = _normalize_cell(row.get("available_copies"))
                total_parsed = _parse_int_field(total_raw, field="total_copies")
                available_parsed = _parse_int_field(available_raw, field="available_copies")

                if creating:
                    if total_parsed is None:
                        total_parsed = 1
                    if total_parsed < 0:
                        raise ValidationError({"total_copies": "total_copies 不能为负数"})

                    if available_parsed is None:
                        available_parsed = total_parsed
                    if available_parsed < 0:
                        raise ValidationError({"available_copies": "available_copies 不能为负数"})
                    if available_parsed > total_parsed:
                        raise ValidationError({"available_copies": "available_copies 不能大于 total_copies"})

                    book.total_copies = total_parsed
                    book.available_copies = available_parsed
                    changed = True
                else:
                    if total_parsed is not None or available_parsed is not None:
                        borrowed_count = book.total_copies - book.available_copies
                        new_total = book.total_copies if total_parsed is None else total_parsed
                        new_available = (
                            book.available_copies
                            if available_parsed is None
                            else available_parsed
                        )

                        if total_parsed is not None and available_parsed is None:
                            new_available = new_total - borrowed_count

                        if new_total < 0:
                            raise ValidationError({"total_copies": "total_copies 不能为负数"})
                        if new_available < 0:
                            raise ValidationError({"available_copies": "available_copies 不能为负数"})
                        if new_available > new_total:
                            raise ValidationError({"available_copies": "available_copies 不能大于 total_copies"})
                        if new_total < borrowed_count:
                            raise ValidationError({"total_copies": "total_copies 不能小于已借出数量"})

                        if book.total_copies != new_total:
                            book.total_copies = new_total
                            changed = True
                        if book.available_copies != new_available:
                            book.available_copies = new_available
                            changed = True

                changed |= _apply_clearable_text(book, "location", _normalize_cell(row.get("location")))
                changed |= _apply_status(book, _normalize_cell(row.get("status")))

                if not creating and not changed:
                    skipped += 1
                    continue

                book.full_clean()

                if dry_run:
                    if creating:
                        created += 1
                    else:
                        updated += 1
                    continue

                book.save()

                if creating:
                    created += 1
                else:
                    updated += 1
            except ValidationError as exc:
                skipped += 1
                message = str(exc)
                errors.append(ImportErrorItem(row=idx, isbn=isbn, message=message))

    if atomic:
        with transaction.atomic():
            process()
            if errors:
                transaction.set_rollback(True)
    else:
        process()

    return {
        "ok": True,
        "has_errors": bool(errors),
        "dry_run": dry_run,
        "atomic": atomic,
        "applied": (not dry_run) and (not (atomic and errors)),
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "errors": [e.to_dict() for e in errors],
    }


def wrap_uploaded_file(file_obj) -> io.TextIOBase:
    """
    将上传的二进制文件包装为文本流（utf-8-sig），以兼容 Excel 导出的 UTF-8 BOM。
    """
    return io.TextIOWrapper(file_obj, encoding="utf-8-sig", newline="")
