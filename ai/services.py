"""
AI 服务封装 - OpenAI 兼容 API 调用
"""
import json
try:
    import httpx
except ModuleNotFoundError:  # pragma: no cover
    httpx = None
from django.conf import settings


class AIService:
    """OpenAI 兼容 API 服务封装"""

    def __init__(self):
        self.api_key = settings.AI_API_KEY
        self.base_url = settings.AI_API_BASE_URL.rstrip('/')
        self.model = settings.AI_MODEL
        self.max_tokens = settings.AI_MAX_TOKENS
        self.temperature = settings.AI_TEMPERATURE

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _require_httpx(self):
        if httpx is None:
            raise RuntimeError("缺少依赖 httpx，请先执行 pip install -r requirements.txt")
        return httpx

    def chat(self, messages: list) -> str:
        """
        非流式调用
        :param messages: 消息列表 [{"role": "system/user/assistant", "content": "..."}]
        :return: AI 回复内容
        """
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        httpx_mod = self._require_httpx()
        with httpx_mod.Client(timeout=60.0) as client:
            response = client.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    def chat_stream(self, messages: list):
        """
        流式调用，返回生成器
        :param messages: 消息列表
        :yield: 文本片段
        """
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": True,
        }

        httpx_mod = self._require_httpx()
        with httpx_mod.Client(timeout=60.0) as client:
            with client.stream("POST", url, json=payload, headers=self._get_headers()) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    if isinstance(line, bytes):
                        line = line.decode("utf-8", errors="ignore")
                    if line.startswith("data: "):
                        data_str = line[6:]
                    elif line.startswith("data:"):
                        data_str = line[5:].lstrip()
                    else:
                        continue
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        content = data["choices"][0]["delta"].get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
