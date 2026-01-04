import json
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_http_methods

from books.models import Book

from .admin_csv import export_borrows_to_csv
from .models import Borrow, OverdueMailLog
from .overdue import build_overdue_email, overdue_borrows_qs, serialize_overdue_item


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


def _effective_status(borrow: Borrow) -> str:
    if borrow.status != Borrow.Status.RETURNED and borrow.is_overdue:
        return Borrow.Status.OVERDUE
    return borrow.status


def _serialize_borrow(borrow: Borrow):
    return {
        "id": borrow.id,
        "user": {"id": borrow.user_id, "username": borrow.user.get_username()},
        "book": {
            "id": borrow.book_id,
            "title": borrow.book.title,
            "isbn": borrow.book.isbn,
        },
        "borrow_date": borrow.borrow_date.isoformat() if borrow.borrow_date else None,
        "due_date": borrow.due_date.isoformat() if borrow.due_date else None,
        "return_date": borrow.return_date.isoformat() if borrow.return_date else None,
        "status": _effective_status(borrow),
        "is_overdue": borrow.is_overdue,
    }


@require_http_methods(["GET", "POST"])
def borrows_collection(request):
    if not request.user.is_authenticated:
        return _json_error("未登录", status=401)

    if request.method == "GET":
        qs = Borrow.objects.select_related("book", "user").order_by("-borrow_date")

        if not _is_admin(request.user):
            qs = qs.filter(user_id=request.user.id)
        else:
            user_id = (request.GET.get("user_id") or "").strip()
            if user_id.isdigit():
                qs = qs.filter(user_id=int(user_id))

        status = (request.GET.get("status") or "").strip()
        if status:
            if status == Borrow.Status.OVERDUE:
                today = timezone.localdate()
                qs = qs.filter(return_date__isnull=True, due_date__lt=today).exclude(
                    status=Borrow.Status.RETURNED
                )
            else:
                qs = qs.filter(status=status)

        results = [_serialize_borrow(b) for b in qs]
        return _json_response({"ok": True, "count": len(results), "results": results})

    data = _parse_json(request)
    if data is None:
        return _json_error("JSON 格式错误", status=400)

    book_id = data.get("book_id")
    if book_id is None:
        return _json_error("book_id 为必填", status=400)

    try:
        book = Book.objects.get(pk=int(book_id))
    except Exception:
        return _json_error("book_id 不存在", status=400)

    due_date = None
    if data.get("due_date"):
        due_date = parse_date(str(data.get("due_date")))
        if due_date is None:
            return _json_error("due_date 格式应为 YYYY-MM-DD", status=400)
    else:
        due_date = timezone.localdate() + timedelta(days=14)

    if due_date < timezone.localdate():
        return _json_error("due_date 不能早于今天", status=400)

    borrow = Borrow(user=request.user, book=book, due_date=due_date, status=Borrow.Status.BORROWED)
    try:
        borrow.full_clean()
        borrow.save()
    except Exception as exc:
        message = str(exc) or "借阅失败"
        return _json_error(message, status=400)

    borrow = Borrow.objects.select_related("book", "user").get(pk=borrow.pk)
    return _json_response({"ok": True, "borrow": _serialize_borrow(borrow)}, status=201)


@require_http_methods(["POST"])
def return_borrow(request, borrow_id: int):
    if not request.user.is_authenticated:
        return _json_error("未登录", status=401)

    try:
        borrow = Borrow.objects.select_related("book", "user").get(pk=borrow_id)
    except Borrow.DoesNotExist:
        return _json_error("借阅记录不存在", status=404)

    if not _is_admin(request.user) and borrow.user_id != request.user.id:
        return _json_error("无权限", status=403)

    if borrow.status == Borrow.Status.RETURNED:
        return _json_response({"ok": True, "borrow": _serialize_borrow(borrow)})

    borrow.status = Borrow.Status.RETURNED
    borrow.return_date = timezone.now()
    try:
        borrow.full_clean()
        borrow.save()
    except Exception as exc:
        message = str(exc) or "归还失败"
        return _json_error(message, status=400)

    borrow = Borrow.objects.select_related("book", "user").get(pk=borrow.pk)
    return _json_response({"ok": True, "borrow": _serialize_borrow(borrow)})


@require_http_methods(["POST"])
def renew_borrow(request, borrow_id: int):
    if not request.user.is_authenticated:
        return _json_error("未登录", status=401)

    try:
        borrow = Borrow.objects.select_related("book", "user").get(pk=borrow_id)
    except Borrow.DoesNotExist:
        return _json_error("借阅记录不存在", status=404)

    if not _is_admin(request.user) and borrow.user_id != request.user.id:
        return _json_error("无权限", status=403)

    if borrow.status == Borrow.Status.RETURNED:
        return _json_error("已归还记录不能续借", status=400)

    data = _parse_json(request)
    if data is None:
        return _json_error("JSON 格式错误", status=400)

    due_date = parse_date(str(data.get("due_date") or ""))
    if due_date is None:
        return _json_error("due_date 为必填，格式 YYYY-MM-DD", status=400)
    if due_date < timezone.localdate():
        return _json_error("due_date 不能早于今天", status=400)

    borrow.due_date = due_date
    if borrow.status == Borrow.Status.OVERDUE and not borrow.is_overdue:
        borrow.status = Borrow.Status.BORROWED

    try:
        borrow.full_clean()
        borrow.save()
    except Exception as exc:
        message = str(exc) or "续借失败"
        return _json_error(message, status=400)

    borrow = Borrow.objects.select_related("book", "user").get(pk=borrow.pk)
    return _json_response({"ok": True, "borrow": _serialize_borrow(borrow)})


@require_http_methods(["GET"])
def admin_borrows_export(request):
    if not request.user.is_authenticated:
        return _json_error("未登录", status=401)
    if not _is_admin(request.user):
        return _json_error("无权限", status=403)

    today = timezone.localdate().isoformat()
    filename = f"borrows_{today}.csv"

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")

    export_borrows_to_csv(Borrow.objects.all(), response)
    return response


@require_http_methods(["GET"])
def admin_overdue_preview(request):
    if not request.user.is_authenticated:
        return _json_error("未登录", status=401)
    if not _is_admin(request.user):
        return _json_error("无权限", status=403)

    today = timezone.localdate()
    sent_user_ids = set(
        OverdueMailLog.objects.filter(sent_date=today).values_list("user_id", flat=True)
    )

    groups: dict[int, dict] = {}
    for borrow in overdue_borrows_qs(today):
        user = borrow.user
        group = groups.get(user.id)
        if group is None:
            group = {
                "user": {"id": user.id, "username": user.get_username(), "mail": getattr(user, "mail", None)},
                "already_sent": user.id in sent_user_ids,
                "items": [],
            }
            groups[user.id] = group
        group["items"].append(serialize_overdue_item(borrow, today=today))

    results = []
    for group in groups.values():
        results.append(
            {
                "user": group["user"],
                "already_sent": group["already_sent"],
                "borrow_count": len(group["items"]),
                "items": group["items"],
            }
        )

    return _json_response(
        {"ok": True, "date": today.isoformat(), "user_count": len(results), "results": results}
    )


@require_http_methods(["POST"])
def admin_overdue_send(request):
    if not request.user.is_authenticated:
        return _json_error("未登录", status=401)
    if not _is_admin(request.user):
        return _json_error("无权限", status=403)

    dry_run = _truthy(request.GET.get("dry_run"))
    force = _truthy(request.GET.get("force"))

    today = timezone.localdate()
    existing_user_ids = set(
        OverdueMailLog.objects.filter(sent_date=today).values_list("user_id", flat=True)
    )
    grouped: dict[int, list[Borrow]] = {}
    users: dict[int, object] = {}
    for borrow in overdue_borrows_qs(today):
        grouped.setdefault(borrow.user_id, []).append(borrow)
        users[borrow.user_id] = borrow.user

    sent = 0
    skipped_no_mail = 0
    skipped_already_sent = 0
    failed = 0
    details: list[dict] = []

    for user_id, items in grouped.items():
        user = users[user_id]
        mail = (getattr(user, "mail", None) or "").strip()
        if not mail:
            skipped_no_mail += 1
            details.append({"user_id": user_id, "status": "skipped_no_mail", "borrow_count": len(items)})
            continue

        if (not force) and (user_id in existing_user_ids):
            skipped_already_sent += 1
            details.append(
                {"user_id": user_id, "mail": mail, "status": "skipped_already_sent", "borrow_count": len(items)}
            )
            continue

        if dry_run:
            details.append({"user_id": user_id, "mail": mail, "status": "dry_run", "borrow_count": len(items)})
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
                details.append(
                    {
                        "user_id": user_id,
                        "mail": mail,
                        "status": "skipped_already_sent",
                        "borrow_count": len(items),
                    }
                )
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
            details.append({"user_id": user_id, "mail": mail, "status": "sent", "borrow_count": len(items)})
        except Exception as exc:
            if log is not None:
                OverdueMailLog.objects.filter(pk=log.pk).delete()
            failed += 1
            details.append(
                {
                    "user_id": user_id,
                    "mail": mail,
                    "status": "failed",
                    "borrow_count": len(items),
                    "message": str(exc),
                }
            )

    return _json_response(
        {
            "ok": True,
            "dry_run": dry_run,
            "date": today.isoformat(),
            "sent": sent,
            "skipped_no_mail": skipped_no_mail,
            "skipped_already_sent": skipped_already_sent,
            "failed": failed,
            "details": details,
        }
    )
