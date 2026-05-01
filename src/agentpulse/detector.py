"""模型可用性检测。"""
import time
from dataclasses import dataclass

import httpx


@dataclass
class ModelStatus:
    """单个模型的检测结果。"""
    model: str
    provider: str
    available: bool
    latency_ms: float = 0.0
    error: str | None = None


def detect_model(
    base_url: str,
    api_key: str,
    model: str,
    timeout: float = 10.0,
) -> ModelStatus:
    """检测单个模型是否可用。

    通过发送一个最小的 chat/completions 请求来判断：
    - 200 → 可用
    - 401 → 认证失败
    - 404 → 模型不存在
    - 429 → 限流
    - 其他 → 具体错误码
    """
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1,
    }

    start = time.monotonic()
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=payload, headers=headers)
        elapsed = (time.monotonic() - start) * 1000

        if resp.status_code == 200:
            return ModelStatus(
                model=model, provider="", available=True,
                latency_ms=round(elapsed, 1),
            )
        error_map = {
            401: "认证失败 (401)",
            403: "权限不足 (403)",
            404: "模型不存在 (404)",
            429: "限流 (429)",
        }
        return ModelStatus(
            model=model, provider="", available=False,
            error=error_map.get(resp.status_code, f"HTTP {resp.status_code}"),
        )
    except httpx.ConnectError:
        return ModelStatus(model=model, provider="", available=False, error="连接失败")
    except httpx.TimeoutException:
        return ModelStatus(model=model, provider="", available=False, error="超时")
    except Exception as e:
        return ModelStatus(model=model, provider="", available=False, error=str(e))
