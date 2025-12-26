import json

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods


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


def _serialize_user(user):
    return {
        "id": user.id,
        "username": user.get_username(),
        "role": getattr(user, "role", None),
        "mail": getattr(user, "mail", None),
    }


@ensure_csrf_cookie
@require_http_methods(["GET"])
def csrf(request):
    return _json_response({"ok": True})


@require_http_methods(["POST"])
def register(request):
    data = _parse_json(request)
    if data is None:
        return _json_error("JSON 格式错误", status=400)

    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    mail = (data.get("mail") or "").strip() or None

    if not username:
        return _json_error("username 不能为空", status=400)
    if not password:
        return _json_error("password 不能为空", status=400)

    User = get_user_model()
    try:
        user = User.objects.create_user(username=username, password=password, mail=mail)
    except Exception:
        return _json_error("注册失败：用户名或邮箱可能已存在", status=400)

    login(request, user)
    return _json_response({"ok": True, "user": _serialize_user(user)}, status=201)


@require_http_methods(["POST"])
def login_view(request):
    data = _parse_json(request)
    if data is None:
        return _json_error("JSON 格式错误", status=400)

    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return _json_error("username/password 不能为空", status=400)

    user = authenticate(request, username=username, password=password)
    if user is None:
        return _json_error("用户名或密码错误", status=401)
    if not user.is_active:
        return _json_error("用户已被禁用", status=403)

    login(request, user)
    return _json_response({"ok": True, "user": _serialize_user(user)})


@require_http_methods(["POST"])
def logout_view(request):
    logout(request)
    return _json_response({"ok": True})


@require_http_methods(["GET"])
def me(request):
    if not request.user.is_authenticated:
        return _json_error("未登录", status=401)
    return _json_response({"ok": True, "user": _serialize_user(request.user)})
