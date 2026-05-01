"""测试模型检测器。"""
import pytest
from unittest.mock import patch, MagicMock
import httpx

from agentpulse.detector import ModelStatus, detect_model


def test_model_status_dataclass():
    status = ModelStatus(
        model="test-model",
        provider="test",
        available=True,
        latency_ms=100.0,
    )
    assert status.available is True
    assert status.latency_ms == 100.0
    assert status.error is None
    assert status.attempts == 1


def test_detect_model_with_invalid_url():
    """无效 URL 应该返回不可用。"""
    status = detect_model(
        base_url="http://localhost:99999/v1",
        api_key="fake-key",
        model="test-model",
        timeout=2.0,
        max_retries=0,  # 不重试，加快测试
    )
    assert status.available is False
    assert status.error is not None


def test_detect_model_401_no_retry():
    """401 认证失败不应该重试。"""
    mock_resp = MagicMock()
    mock_resp.status_code = 401

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__ = MagicMock(
            return_value=MagicMock(post=MagicMock(return_value=mock_resp))
        )
        mock_client.return_value.__exit__ = MagicMock(return_value=False)

        status = detect_model(
            base_url="https://api.example.com/v1",
            api_key="bad-key",
            model="test-model",
            max_retries=2,
        )

    assert status.available is False
    assert "认证失败" in status.error
    assert status.attempts == 1  # 没有重试


def test_detect_model_500_retries():
    """500 服务端错误应该重试。"""
    mock_resp = MagicMock()
    mock_resp.status_code = 500

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__ = MagicMock(
            return_value=MagicMock(post=MagicMock(return_value=mock_resp))
        )
        mock_client.return_value.__exit__ = MagicMock(return_value=False)

        status = detect_model(
            base_url="https://api.example.com/v1",
            api_key="key",
            model="test-model",
            max_retries=2,
            retry_delay=0.01,  # 极短延迟，加速测试
        )

    assert status.available is False
    assert status.attempts == 3  # 首次 + 2 次重试


def test_detect_model_success():
    """200 成功应该返回可用。"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__ = MagicMock(
            return_value=MagicMock(post=MagicMock(return_value=mock_resp))
        )
        mock_client.return_value.__exit__ = MagicMock(return_value=False)

        status = detect_model(
            base_url="https://api.example.com/v1",
            api_key="good-key",
            model="test-model",
        )

    assert status.available is True
    assert status.error is None


def test_detect_model_429_no_retry():
    """429 限流不应该重试。"""
    mock_resp = MagicMock()
    mock_resp.status_code = 429

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__ = MagicMock(
            return_value=MagicMock(post=MagicMock(return_value=mock_resp))
        )
        mock_client.return_value.__exit__ = MagicMock(return_value=False)

        status = detect_model(
            base_url="https://api.example.com/v1",
            api_key="key",
            model="test-model",
            max_retries=2,
        )

    assert status.available is False
    assert "限流" in status.error
    assert status.attempts == 1  # 没有重试


def test_detect_model_timeout_retries():
    """超时应该重试。"""
    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__ = MagicMock(
            return_value=MagicMock(
                post=MagicMock(side_effect=httpx.TimeoutException("timeout"))
            )
        )
        mock_client.return_value.__exit__ = MagicMock(return_value=False)

        status = detect_model(
            base_url="https://api.example.com/v1",
            api_key="key",
            model="test-model",
            timeout=1.0,
            max_retries=1,
            retry_delay=0.01,
        )

    assert status.available is False
    assert "超时" in status.error
    assert status.attempts == 2  # 首次 + 1 次重试
