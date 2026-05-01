"""测试配置写入器。"""
import pytest
from agentpulse.config_writer import build_hermes_fallback, build_hermes_provider_block


def test_build_hermes_provider_block():
    entry = {
        "provider_id": "deepseek",
        "provider_name": "DeepSeek",
        "model": "deepseek-v4-flash",
        "base_url": "https://api.deepseek.com/v1",
        "api_key": "sk-test",
        "latency_ms": 200,
    }
    key, cfg = build_hermes_provider_block(entry)
    assert key == "deepseek_ap"
    assert cfg["type"] == "openai"
    assert cfg["base_url"] == "https://api.deepseek.com/v1"
    assert cfg["api_key"] == "sk-test"
    assert cfg["models"] == ["deepseek-v4-flash"]


def test_build_hermes_provider_block_custom():
    """自定义提供商也应该生成 _ap 后缀。"""
    entry = {
        "provider_id": "my-local",
        "provider_name": "My Local",
        "model": "qwen2.5:7b",
        "base_url": "http://localhost:11434/v1",
        "api_key": "",
        "latency_ms": 50,
    }
    key, cfg = build_hermes_provider_block(entry)
    assert key == "my-local_ap"
    assert cfg["base_url"] == "http://localhost:11434/v1"
    assert cfg["api_key"] == ""


def test_build_hermes_fallback_single():
    models = [
        {"provider_id": "deepseek", "model": "deepseek-v4-flash",
         "base_url": "https://api.deepseek.com/v1", "api_key": "sk-test",
         "latency_ms": 200, "provider_name": "DeepSeek"},
    ]
    fb = build_hermes_fallback(models)
    assert fb["primary"] == "deepseek_ap/deepseek-v4-flash"
    assert fb["chain"] == []


def test_build_hermes_fallback_chain():
    models = [
        {"provider_id": "deepseek", "model": "deepseek-v4-flash",
         "base_url": "https://api.deepseek.com/v1", "api_key": "sk-test",
         "latency_ms": 200, "provider_name": "DeepSeek"},
        {"provider_id": "xiaomi", "model": "mimo-v2-flash",
         "base_url": "https://api.xiaomi.com/v1", "api_key": "sk-test2",
         "latency_ms": 150, "provider_name": "Xiaomi"},
        {"provider_id": "openrouter", "model": "gpt-4o",
         "base_url": "https://openrouter.ai/api/v1", "api_key": "sk-or",
         "latency_ms": 300, "provider_name": "OpenRouter"},
    ]
    fb = build_hermes_fallback(models)
    assert fb["primary"] == "deepseek_ap/deepseek-v4-flash"
    assert fb["chain"] == ["xiaomi_ap/mimo-v2-flash", "openrouter_ap/gpt-4o"]


def test_build_hermes_fallback_empty():
    """空列表应该返回空字典。"""
    fb = build_hermes_fallback([])
    assert fb == {}
