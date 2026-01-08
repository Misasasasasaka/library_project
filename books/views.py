import json
from datetime import date

from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_http_methods

from .admin_csv import export_books_to_csv, import_books_from_csv, wrap_uploaded_file
from .models import Book, BookCopy, Category
from borrows.models import Borrow


def _json_response(payload, *, status=200):
    return JsonResponse(payload, status=status, json_dumps_params={"ensure_ascii": False})


def _json_error(message, *, status=400):
    return _json_response({"ok": False, "message": message}, status=status)


def _parse_json(request):
    try:
        body = request.body.decode("utf-8") if request.body else ""
        return json.loads(body) if body else {}
    except json.JSONDecodeError:
        return None


def _is_admin(user) -> bool:
    if not user.is_authenticated:
        return False
    return getattr(user, "role", None) == "admin" or user.is_staff or user.is_superuser


def _truthy(value) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _serialize_book(book: Book, request=None):
    cover_url = None
    if book.cover:
        try:
            cover_url = book.cover.url
            if request is not None:
                cover_url = request.build_absolute_uri(cover_url)
        except Exception:
            cover_url = None

    category = None
    if book.category_id:
        category = {"id": book.category_id, "name": book.category.name}

    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "isbn": book.isbn,
        "publisher": book.publisher,
        "publish_date": book.publish_date.isoformat() if book.publish_date else None,
        "description": book.description,
        "category": category,
        "cover_url": cover_url,
        "total_copies": book.total_copies,
        "available_copies": book.available_copies,
        "location": book.location,
        "status": book.status,
    }


def _serialize_category(category: Category):
    return {
        "id": category.id,
        "name": category.name,
        "description": category.description,
    }


@require_http_methods(["GET", "POST"])
def categories_collection(request):
    if request.method == "GET":
        qs = Category.objects.all().order_by("name")
        kw = (request.GET.get("kw") or "").strip()
        if kw:
            qs = qs.filter(name__icontains=kw)
        results = [_serialize_category(cat) for cat in qs]
        return _json_response({"ok": True, "count": len(results), "results": results})

    if not _is_admin(request.user):
        return _json_error("无权限", status=403)

    data = _parse_json(request)
    if data is None:
        return _json_error("JSON 格式错误", status=400)

    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    if not name:
        return _json_error("name 不能为空", status=400)

    category = Category(name=name, description=description)
    try:
        category.full_clean()
        category.save()
    except Exception:
        return _json_error("创建失败：分类名称可能已存在", status=400)

    return _json_response({"ok": True, "category": _serialize_category(category)}, status=201)


@require_http_methods(["GET", "PATCH", "DELETE"])
def category_item(request, category_id: int):
    try:
        category = Category.objects.get(pk=category_id)
    except Category.DoesNotExist:
        return _json_error("分类不存在", status=404)

    if request.method == "GET":
        return _json_response({"ok": True, "category": _serialize_category(category)})

    if not _is_admin(request.user):
        return _json_error("无权限", status=403)

    if request.method == "DELETE":
        category.delete()
        return _json_response({"ok": True})

    data = _parse_json(request)
    if data is None:
        return _json_error("JSON 格式错误", status=400)

    if "name" in data:
        category.name = (data.get("name") or "").strip()
    if "description" in data:
        category.description = (data.get("description") or "").strip()
    if not category.name:
        return _json_error("name 不能为空", status=400)

    try:
        category.full_clean()
        category.save()
    except Exception:
        return _json_error("更新失败：分类名称可能已存在", status=400)

    return _json_response({"ok": True, "category": _serialize_category(category)})


@require_http_methods(["GET", "POST"])
def books_collection(request):
    if request.method == "GET":
        qs = Book.objects.select_related("category")

        kw = (request.GET.get("kw") or "").strip()
        if kw:
            qs = qs.filter(
                Q(title__icontains=kw)
                | Q(author__icontains=kw)
                | Q(isbn__icontains=kw)
                | Q(publisher__icontains=kw)
            )

        category_id = (request.GET.get("category") or "").strip()
        if category_id.isdigit():
            qs = qs.filter(category_id=int(category_id))

        if not _is_admin(request.user):
            qs = qs.filter(status=Book.Status.ON_SHELF)
        else:
            status = (request.GET.get("status") or "").strip()
            if status:
                qs = qs.filter(status=status)

        qs = qs.order_by("-updated_at")
        results = [_serialize_book(book, request=request) for book in qs]
        return _json_response({"ok": True, "count": len(results), "results": results})

    if not _is_admin(request.user):
        return _json_error("无权限", status=403)

    data = _parse_json(request)
    if data is None:
        return _json_error("JSON 格式错误", status=400)

    title = (data.get("title") or "").strip()
    author = (data.get("author") or "").strip()
    isbn = (data.get("isbn") or "").strip()

    if not title or not author or not isbn:
        return _json_error("title/author/isbn 为必填", status=400)

    publish_date: date | None = None
    if data.get("publish_date"):
        publish_date = parse_date(str(data.get("publish_date")))
        if publish_date is None:
            return _json_error("publish_date 格式应为 YYYY-MM-DD", status=400)

    category = None
    if data.get("category_id") is not None:
        try:
            category = Category.objects.get(pk=int(data["category_id"]))
        except Exception:
            return _json_error("category_id 不存在", status=400)

    total_copies = int(data.get("total_copies") or 1)
    if total_copies < 0:
        return _json_error("total_copies 不能为负数", status=400)

    available_copies = total_copies

    status = (data.get("status") or Book.Status.ON_SHELF).strip()

    book = Book(
        title=title,
        author=author,
        isbn=isbn,
        publisher=(data.get("publisher") or "").strip(),
        publish_date=publish_date,
        description=(data.get("description") or "").strip(),
        category=category,
        total_copies=total_copies,
        available_copies=available_copies,
        location=(data.get("location") or "").strip(),
        status=status,
    )

    try:
        book.full_clean()
        book.save()
    except Exception:
        return _json_error("创建失败：请检查字段/ISBN 是否重复", status=400)

    return _json_response({"ok": True, "book": _serialize_book(book, request=request)}, status=201)


@require_http_methods(["GET", "PATCH", "DELETE"])
def book_item(request, book_id: int):
    try:
        book = Book.objects.select_related("category").get(pk=book_id)
    except Book.DoesNotExist:
        return _json_error("图书不存在", status=404)

    if request.method == "GET":
        if not _is_admin(request.user) and book.status != Book.Status.ON_SHELF:
            return _json_error("图书不存在", status=404)
        return _json_response({"ok": True, "book": _serialize_book(book, request=request)})

    if not _is_admin(request.user):
        return _json_error("无权限", status=403)

    if request.method == "DELETE":
        book.delete()
        return _json_response({"ok": True})

    data = _parse_json(request)
    if data is None:
        return _json_error("JSON 格式错误", status=400)

    if "title" in data:
        book.title = (data.get("title") or "").strip()
    if "author" in data:
        book.author = (data.get("author") or "").strip()
    if "isbn" in data:
        book.isbn = (data.get("isbn") or "").strip()
    if "publisher" in data:
        book.publisher = (data.get("publisher") or "").strip()
    if "description" in data:
        book.description = (data.get("description") or "").strip()
    if "location" in data:
        book.location = (data.get("location") or "").strip()
    if "status" in data:
        book.status = (data.get("status") or "").strip()

    if "publish_date" in data:
        if data.get("publish_date") in ("", None):
            book.publish_date = None
        else:
            publish_date = parse_date(str(data.get("publish_date")))
            if publish_date is None:
                return _json_error("publish_date 格式应为 YYYY-MM-DD", status=400)
            book.publish_date = publish_date

    if "category_id" in data:
        if data.get("category_id") in ("", None):
            book.category = None
        else:
            try:
                book.category = Category.objects.get(pk=int(data["category_id"]))
            except Exception:
                return _json_error("category_id 不存在", status=400)

    if "total_copies" in data or "available_copies" in data:
        if "available_copies" in data and "total_copies" not in data:
            return _json_error("available_copies 不支持直接修改", status=400)

        if "total_copies" in data:
            new_total = int(data.get("total_copies") or 0)
            if new_total < 0:
                return _json_error("total_copies 不能为负数", status=400)

            borrowed_count = Borrow.objects.filter(
                book_id=book.id, return_date__isnull=True
            ).count()
            if new_total < borrowed_count:
                return _json_error("total_copies 不能小于已借出数量", status=400)

            book.total_copies = new_total
            book.available_copies = new_total - borrowed_count

    try:
        book.full_clean()
        book.save()
    except Exception:
        return _json_error("更新失败：请检查字段/ISBN 是否重复", status=400)

    return _json_response({"ok": True, "book": _serialize_book(book, request=request)})


@require_http_methods(["GET"])
def book_available_copies(request, book_id: int):
    try:
        book = Book.objects.get(pk=book_id)
    except Book.DoesNotExist:
        return _json_error("图书不存在", status=404)

    if not _is_admin(request.user) and book.status != Book.Status.ON_SHELF:
        return _json_error("图书不存在", status=404)

    open_copy_ids = Borrow.objects.filter(
        book_id=book.id,
        return_date__isnull=True,
        copy_id__isnull=False,
    ).values_list("copy_id", flat=True)
    qs = (
        BookCopy.objects.filter(book_id=book.id, is_active=True)
        .exclude(id__in=open_copy_ids)
        .order_by("copy_no")
    )
    results = [{"copy_no": c.copy_no, "code": str(c.copy_no).zfill(3)} for c in qs]
    return _json_response({"ok": True, "book_id": book.id, "count": len(results), "results": results})


@require_http_methods(["POST", "DELETE"])
def book_cover(request, book_id: int):
    try:
        book = Book.objects.select_related("category").get(pk=book_id)
    except Book.DoesNotExist:
        return _json_error("图书不存在", status=404)

    if not _is_admin(request.user):
        return _json_error("无权限", status=403)

    if request.method == "DELETE":
        if book.cover:
            try:
                book.cover.delete(save=False)
            except Exception:
                pass
            book.cover = None
            book.save()
        return _json_response({"ok": True, "book": _serialize_book(book, request=request)})

    uploaded = request.FILES.get("cover") or request.FILES.get("file")
    if not uploaded:
        return _json_error("cover 为必填", status=400)

    content_type = (getattr(uploaded, "content_type", None) or "").lower()
    if content_type and not content_type.startswith("image/"):
        return _json_error("仅支持图片文件", status=400)

    max_size = 5 * 1024 * 1024
    if getattr(uploaded, "size", 0) and uploaded.size > max_size:
        return _json_error("图片大小不能超过 5MB", status=400)

    if book.cover:
        try:
            book.cover.delete(save=False)
        except Exception:
            pass

    book.cover = uploaded
    try:
        book.save()
    except Exception:
        return _json_error("上传失败", status=400)

    return _json_response({"ok": True, "book": _serialize_book(book, request=request)})


@require_http_methods(["GET"])
def admin_books_export(request):
    if not request.user.is_authenticated:
        return _json_error("未登录", status=401)
    if not _is_admin(request.user):
        return _json_error("无权限", status=403)

    today = timezone.localdate().isoformat()
    filename = f"books_{today}.csv"

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")

    export_books_to_csv(Book.objects.all(), response)
    return response


@require_http_methods(["POST"])
def admin_books_import(request):
    if not request.user.is_authenticated:
        return _json_error("未登录", status=401)
    if not _is_admin(request.user):
        return _json_error("无权限", status=403)

    uploaded = request.FILES.get("file")
    if not uploaded:
        return _json_error("file 为必填", status=400)

    dry_run = _truthy(request.GET.get("dry_run"))
    atomic = _truthy(request.GET.get("atomic"))

    try:
        try:
            uploaded.file.seek(0)
        except Exception:
            pass
        with wrap_uploaded_file(uploaded.file) as f:
            result = import_books_from_csv(f, dry_run=dry_run, atomic=atomic)
    except Exception as exc:
        return _json_error(f"导入失败：{exc}", status=400)

    return _json_response(result)
