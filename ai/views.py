"""
AI 推荐 API 视图
"""
import json
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings

from books.models import Book
from .services import AIService
from .prompts import build_system_prompt


def _json_response(payload, *, status=200):
    """统一 JSON 响应格式"""
    return JsonResponse(payload, status=status, json_dumps_params={"ensure_ascii": False})


def _json_error(message, *, status=400):
    """统一错误响应"""
    return _json_response({"ok": False, "message": message}, status=status)


def _parse_json(request):
    """解析请求体 JSON"""
    try:
        body = request.body.decode("utf-8") if request.body else ""
        return json.loads(body) if body else {}
    except json.JSONDecodeError:
        return None


def _get_library_context(limit=100):
    """获取馆藏书籍上下文信息"""
    books = Book.objects.filter(
        status=Book.Status.ON_SHELF
    ).select_related("category").order_by("-updated_at")[:limit]

    book_list = []
    for book in books:
        book_info = {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "category": book.category.name if book.category else "未分类",
            "description": (book.description[:200] + "...") if book.description and len(book.description) > 200 else (book.description or ""),
            "available": book.available_copies > 0,
        }
        book_list.append(book_info)

    return book_list


@require_http_methods(["POST"])
def chat_view(request):
    """非流式聊天接口"""
    if not request.user.is_authenticated:
        return _json_error("请先登录", status=401)

    # 检查 API Key 是否配置
    if not settings.AI_API_KEY:
        return _json_error("AI 服务未配置", status=503)

    data = _parse_json(request)
    if data is None:
        return _json_error("JSON 格式错误", status=400)

    user_message = (data.get("message") or "").strip()
    history = data.get("history", [])  # 对话历史

    if not user_message:
        return _json_error("message 不能为空", status=400)

    # 获取馆藏书籍信息
    library_books = _get_library_context()
    system_prompt = build_system_prompt(library_books)

    # 构建消息列表
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-10:]:  # 最多保留10轮历史
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})

    try:
        ai_service = AIService()
        response_text = ai_service.chat(messages)
        return _json_response({
            "ok": True,
            "reply": response_text
        })
    except RuntimeError as e:
        return _json_error(str(e), status=503)
    except Exception as e:
        return _json_error(f"AI 服务异常: {str(e)}", status=500)


@require_http_methods(["POST"])
def chat_stream_view(request):
    """流式聊天接口 (SSE)"""
    if not request.user.is_authenticated:
        return _json_error("请先登录", status=401)

    # 检查 API Key 是否配置
    if not settings.AI_API_KEY:
        return _json_error("AI 服务未配置", status=503)

    data = _parse_json(request)
    if data is None:
        return _json_error("JSON 格式错误", status=400)

    user_message = (data.get("message") or "").strip()
    history = data.get("history", [])

    if not user_message:
        return _json_error("message 不能为空", status=400)

    library_books = _get_library_context()
    system_prompt = build_system_prompt(library_books)

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-10:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})

    try:
        ai_service = AIService()
        ai_service._require_httpx()
    except RuntimeError as e:
        return _json_error(str(e), status=503)

    def event_stream():
        try:
            for chunk in ai_service.chat_stream(messages):
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    response = StreamingHttpResponse(
        event_stream(),
        content_type="text/event-stream"
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
