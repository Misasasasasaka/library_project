import json
import random
import time
from html import escape

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

CAPTCHA_SESSION_KEY = "auth_captcha"
CAPTCHA_TTL_SECONDS = 5 * 60
CAPTCHA_MAX_ATTEMPTS = 5

EMAIL_CODE_SESSION_KEY = "auth_email_code"
EMAIL_CODE_TTL_SECONDS = 10 * 60
EMAIL_CODE_COOLDOWN_SECONDS = 60
EMAIL_CODE_MAX_ATTEMPTS = 5


def _json_response(payload, *, status=200):
    return JsonResponse(payload, status=status, json_dumps_params={"ensure_ascii": False})


def _json_error(message, *, status=400):
    return _json_response({"ok": False, "message": message}, status=status)


def _now_ts() -> int:
    return int(time.time())


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


def _generate_captcha_text(length=5) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choice(alphabet) for _ in range(length))


def _render_captcha_svg(text: str, *, width=140, height=48) -> str:
    bg_colors = ["#F8FAFC", "#F1F5F9", "#EFF6FF", "#F5F3FF", "#FDF2F8"]
    fg_colors = ["#0F172A", "#1E293B", "#334155", "#0F766E", "#7C3AED", "#B91C1C"]
    noise_colors = ["#CBD5E1", "#94A3B8", "#A5B4FC", "#C4B5FD", "#FDA4AF"]

    bg = random.choice(bg_colors)
    chars = []
    padding_x = 14
    step = (width - 2 * padding_x) / max(len(text), 1)

    for idx, ch in enumerate(text):
        x = int(padding_x + idx * step + random.randint(-2, 2))
        y = int(height * 0.72 + random.randint(-4, 4))
        rotate = random.randint(-20, 20)
        size = random.randint(24, 28)
        fill = random.choice(fg_colors)
        chars.append(
            f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" '
            f'font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, Courier New, monospace" '
            f'text-anchor="middle" transform="rotate({rotate} {x} {y})">{escape(ch)}</text>'
        )

    lines = []
    for _ in range(6):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        color = random.choice(noise_colors)
        lines.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1" />')

    dots = []
    for _ in range(24):
        cx = random.randint(0, width)
        cy = random.randint(0, height)
        r = random.randint(1, 2)
        color = random.choice(noise_colors)
        dots.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" fill-opacity="0.8" />')

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="12" ry="12" fill="{bg}" />'
        + "".join(lines)
        + "".join(dots)
        + "".join(chars)
        + "</svg>"
    )
    return svg


def _validate_captcha(request, value: str, *, consume: bool) -> tuple[bool, str]:
    value = (value or "").strip()
    if not value:
        return False, "验证码不能为空"

    record = request.session.get(CAPTCHA_SESSION_KEY)
    if not record:
        return False, "请先获取验证码"

    now = _now_ts()
    ts = int(record.get("ts") or 0)
    if not ts or now - ts > CAPTCHA_TTL_SECONDS:
        request.session.pop(CAPTCHA_SESSION_KEY, None)
        return False, "验证码已过期，请刷新"

    attempts = int(record.get("attempts") or 0)
    if attempts >= CAPTCHA_MAX_ATTEMPTS:
        request.session.pop(CAPTCHA_SESSION_KEY, None)
        return False, "验证码已失效，请刷新"

    expected = str(record.get("text") or "")
    if value.lower() != expected.lower():
        attempts += 1
        record["attempts"] = attempts
        if attempts >= CAPTCHA_MAX_ATTEMPTS:
            request.session.pop(CAPTCHA_SESSION_KEY, None)
            return False, "验证码错误次数过多，请刷新"
        request.session[CAPTCHA_SESSION_KEY] = record
        return False, "验证码错误"

    if consume:
        request.session.pop(CAPTCHA_SESSION_KEY, None)
    else:
        record["attempts"] = 0
        request.session[CAPTCHA_SESSION_KEY] = record

    return True, ""


def _validate_email_code(request, mail: str, code: str, *, consume: bool) -> tuple[bool, str]:
    code = (code or "").strip()
    if not code:
        return False, "邮箱验证码不能为空"

    record = request.session.get(EMAIL_CODE_SESSION_KEY)
    if not record:
        return False, "请先获取邮箱验证码"

    record_mail = (record.get("mail") or "").strip()
    if record_mail.lower() != (mail or "").strip().lower():
        return False, "邮箱验证码与邮箱不匹配，请重新获取"

    now = _now_ts()
    ts = int(record.get("ts") or 0)
    if not ts or now - ts > EMAIL_CODE_TTL_SECONDS:
        request.session.pop(EMAIL_CODE_SESSION_KEY, None)
        return False, "邮箱验证码已过期，请重新获取"

    attempts = int(record.get("attempts") or 0)
    if attempts >= EMAIL_CODE_MAX_ATTEMPTS:
        request.session.pop(EMAIL_CODE_SESSION_KEY, None)
        return False, "邮箱验证码已失效，请重新获取"

    expected = str(record.get("code") or "")
    if code != expected:
        attempts += 1
        record["attempts"] = attempts
        if attempts >= EMAIL_CODE_MAX_ATTEMPTS:
            request.session.pop(EMAIL_CODE_SESSION_KEY, None)
            return False, "邮箱验证码错误次数过多，请重新获取"
        request.session[EMAIL_CODE_SESSION_KEY] = record
        return False, "邮箱验证码错误"

    if consume:
        request.session.pop(EMAIL_CODE_SESSION_KEY, None)
    else:
        record["attempts"] = 0
        request.session[EMAIL_CODE_SESSION_KEY] = record

    return True, ""


@ensure_csrf_cookie
@require_http_methods(["GET"])
def csrf(request):
    return _json_response({"ok": True})


@require_http_methods(["GET"])
def captcha(request):
    text = _generate_captcha_text()
    request.session[CAPTCHA_SESSION_KEY] = {"text": text, "ts": _now_ts(), "attempts": 0}

    response = HttpResponse(_render_captcha_svg(text), content_type="image/svg+xml; charset=utf-8")
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response


@require_http_methods(["POST"])
def send_email_code(request):
    data = _parse_json(request)
    if data is None:
        return _json_error("JSON 格式错误", status=400)

    mail = (data.get("mail") or "").strip()
    captcha_value = (data.get("captcha") or "").strip()

    if not mail:
        return _json_error("mail 不能为空", status=400)
    try:
        validate_email(mail)
    except ValidationError:
        return _json_error("邮箱格式不正确", status=400)

    captcha_ok, captcha_msg = _validate_captcha(request, captcha_value, consume=False)
    if not captcha_ok:
        return _json_error(captcha_msg, status=400)

    User = get_user_model()
    if User.objects.filter(mail=mail).exists():
        return _json_error("该邮箱已被注册", status=400)

    now = _now_ts()
    existing = request.session.get(EMAIL_CODE_SESSION_KEY) or {}
    if (existing.get("mail") or "").strip().lower() == mail.lower():
        sent_ts = int(existing.get("sent_ts") or existing.get("ts") or 0)
        if sent_ts and now - sent_ts < EMAIL_CODE_COOLDOWN_SECONDS:
            return _json_error("验证码发送过于频繁，请稍后再试", status=429)

    code = f"{random.randint(0, 999999):06d}"
    request.session[EMAIL_CODE_SESSION_KEY] = {
        "mail": mail,
        "code": code,
        "ts": now,
        "sent_ts": now,
        "attempts": 0,
    }

    subject = "图书馆注册验证码"
    message = f"您的验证码是：{code}\n\n有效期：10 分钟\n如非本人操作，请忽略本邮件。"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or None
    try:
        send_mail(subject, message, from_email, [mail], fail_silently=False)
    except Exception as exc:
        return _json_error(f"发送失败：{exc}", status=500)

    return _json_response({"ok": True})


@require_http_methods(["POST"])
def register(request):
    data = _parse_json(request)
    if data is None:
        return _json_error("JSON 格式错误", status=400)

    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    mail = (data.get("mail") or "").strip()
    email_code = (data.get("email_code") or "").strip()
    captcha_value = (data.get("captcha") or "").strip()

    if not username:
        return _json_error("username 不能为空", status=400)
    if not password:
        return _json_error("password 不能为空", status=400)
    if not mail:
        return _json_error("mail 不能为空", status=400)
    try:
        validate_email(mail)
    except ValidationError:
        return _json_error("邮箱格式不正确", status=400)

    captcha_ok, captcha_msg = _validate_captcha(request, captcha_value, consume=False)
    if not captcha_ok:
        return _json_error(captcha_msg, status=400)

    code_ok, code_msg = _validate_email_code(request, mail, email_code, consume=False)
    if not code_ok:
        return _json_error(code_msg, status=400)

    User = get_user_model()
    try:
        user = User.objects.create_user(username=username, password=password, mail=mail)
    except Exception:
        return _json_error("注册失败：用户名或邮箱可能已存在", status=400)

    request.session.pop(CAPTCHA_SESSION_KEY, None)
    request.session.pop(EMAIL_CODE_SESSION_KEY, None)
    login(request, user)
    return _json_response({"ok": True, "user": _serialize_user(user)}, status=201)


@require_http_methods(["POST"])
def login_view(request):
    data = _parse_json(request)
    if data is None:
        return _json_error("JSON 格式错误", status=400)

    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    captcha_value = (data.get("captcha") or "").strip()
    if not username or not password:
        return _json_error("username/password 不能为空", status=400)

    captcha_ok, captcha_msg = _validate_captcha(request, captcha_value, consume=True)
    if not captcha_ok:
        return _json_error(captcha_msg, status=400)

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
