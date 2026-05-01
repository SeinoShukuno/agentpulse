"""模型可用性检测。

支持自动重试、超时处理、详细错误分类。
"""
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
    attempts: int = 1


def detect_model(
    base_url: str,
    api_key: str,
    model: str,
    timeout: float = 10.0,
    max_retries: int = 2,
    retry_delay: float = 1.0,
) -> ModelStatus:
    """检测单个模型是否可用。

    通过发送一个最小的 chat/completions 请求来判断。
    支持自动重试（网络异常时重试，HTTP 错误不重试）。

    Args:
        base_url: API 基础 URL
        api_key: API Key
        model: 模型名
        timeout: 请求超时（秒）
        max_retries: 最大重试次数（不含首次尝试）
        retry_delay: 重试间隔（秒），指数退避
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

    last_error = None
    total_attempts = 0

    for attempt in range(max_retries + 1):
        total_attempts += 1
        start = time.monotonic()

        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(url, json=payload, headers=headers)
            elapsed = (time.monotonic() - start) * 1000

            if resp.status_code == 200:
                return ModelStatus(
                    model=model, provider="", available=True,
                    latency_ms=round(elapsed, 1),
                    attempts=total_attempts,
                )

            # HTTP 错误不重试（401/404/429 等是确定性错误）
            error_map = {
                401: "认证失败 (401)",
                403: "权限不足 (403)",
                404: "模型不存在 (404)",
                429: "限流 (429)",
                500: "服务端错误 (500)",
                502: "网关错误 (502)",
                503: "服务不可用 (503)",
            }
            error_msg = error_map.get(resp.status_code, f"HTTP {resp.status_code}")

            # 5xx 错误可以重试
            if resp.status_code >= 500 and attempt < max_retries:
                last_error = error_msg
                time.sleep(retry_delay * (2 ** attempt))  # 指数退避
                continue

            return ModelStatus(
                model=model, provider="", available=False,
                error=error_msg,
                attempts=total_attempts,
            )

        except httpx.ConnectError:
            last_error = "连接失败"
            if attempt < max_retries:
                time.sleep(retry_delay * (2 ** attempt))
                continue
            return ModelStatus(
                model=model, provider="", available=False,
                error="连接失败",
                attempts=total_attempts,
            )

        except httpx.TimeoutException:
            last_error = "超时"
            if attempt < max_retries:
                time.sleep(retry_delay * (2 ** attempt))
                continue
            return ModelStatus(
                model=model, provider="", available=False,
                error=f"超时 ({timeout}s)",
                attempts=total_attempts,
            )

        except httpx.ReadError:
            last_error = "读取失败"
            if attempt < max_retries:
                time.sleep(retry_delay * (2 ** attempt))
                continue
            return ModelStatus(
                model=model, provider="", available=False,
                error="读取失败",
                attempts=total_attempts,
            )

        except Exception as e:
            return ModelStatus(
                model=model, provider="", available=False,
                error=str(e),
                attempts=total_attempts,
            )

    # 所有重试都失败
    return ModelStatus(
        model=model, provider="", available=False,
        error=f"{last_error} (重试 {max_retries} 次)",
        attempts=total_attempts,
    )
