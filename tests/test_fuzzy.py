"""测试模糊匹配。"""
import pytest
from agentpulse.setup_wizard import _fuzzy_match, _normalize


def test_normalize():
    assert _normalize("deepseek-v4-flash") == "deepseekv4flash"
    assert _normalize("MiMo-V2.5-Pro") == "mimov25pro"
    assert _normalize("GLM-4.7-Flash") == "glm47flash"
    assert _normalize("qwen3.6-max-preview") == "qwen36maxpreview"


def test_fuzzy_match_exact():
    """精确匹配。"""
    candidates = ["deepseek-v4-flash", "deepseek-v4-pro"]
    assert _fuzzy_match("deepseek-v4-flash", candidates) == "deepseek-v4-flash"


def test_fuzzy_match_case_insensitive():
    """大小写不敏感匹配。"""
    candidates = ["mimo-v2.5-pro", "mimo-v2-flash"]
    assert _fuzzy_match("MiMo-V2.5-Pro", candidates) == "mimo-v2.5-pro"


def test_fuzzy_match_partial():
    """部分匹配。"""
    candidates = ["deepseek-v4-flash", "deepseek-v4-pro"]
    assert _fuzzy_match("v4-flash", candidates) == "deepseek-v4-flash"
    assert _fuzzy_match("v4pro", candidates) == "deepseek-v4-pro"


def test_fuzzy_match_short_input():
    """短输入匹配。"""
    candidates = ["deepseek-v4-flash", "deepseek-v4-pro"]
    assert _fuzzy_match("flash", candidates) == "deepseek-v4-flash"


def test_fuzzy_match_mimo():
    """小米模型模糊匹配。"""
    candidates = ["mimo-v2.5-pro", "mimo-v2-flash", "mimo-v2.5"]
    assert _fuzzy_match("mimo2.5pro", candidates) == "mimo-v2.5-pro"
    assert _fuzzy_match("2.5-pro", candidates) == "mimo-v2.5-pro"
    assert _fuzzy_match("v2-flash", candidates) == "mimo-v2-flash"


def test_fuzzy_match_glm():
    """GLM 模型模糊匹配。"""
    candidates = ["GLM-5.1", "GLM-4.7-Flash", "GLM-4.6"]
    assert _fuzzy_match("glm5.1", candidates) == "GLM-5.1"
    assert _fuzzy_match("4.7flash", candidates) == "GLM-4.7-Flash"


def test_fuzzy_match_no_match():
    """完全不匹配时返回 None。"""
    candidates = ["deepseek-v4-flash", "mimo-v2.5-pro"]
    assert _fuzzy_match("gpt-4o", candidates) is None


def test_fuzzy_match_empty_input():
    """空输入返回 None。"""
    candidates = ["deepseek-v4-flash"]
    assert _fuzzy_match("", candidates) is None
    assert _fuzzy_match("  ", candidates) is None


def test_fuzzy_match_empty_candidates():
    """空候选列表返回 None。"""
    assert _fuzzy_match("flash", []) is None


def test_fuzzy_match_best_shortest():
    """多个匹配时选最短的（最精确的）。"""
    candidates = ["mimo-v2.5-pro", "mimo-v2.5-pro-tts"]
    assert _fuzzy_match("mimo-v2.5-pro", candidates) == "mimo-v2.5-pro"
