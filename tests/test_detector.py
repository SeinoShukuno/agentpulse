"""测试模型检测器。"""
import pytest
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


def test_detect_model_with_invalid_url():
    """无效 URL 应该返回不可用。"""
    status = detect_model(
        base_url="http://localhost:99999/v1",
        api_key="fake-key",
        model="test-model",
        timeout=3.0,
    )
    assert status.available is False
    assert status.error is not None
