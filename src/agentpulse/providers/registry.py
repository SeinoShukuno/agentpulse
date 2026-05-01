"""提供商注册表 — 预设 + 自定义支持。"""
from dataclasses import dataclass, field


@dataclass
class ProviderInfo:
    """一个模型提供商的配置信息。"""
    id: str
    name: str
    base_url: str
    default_models: list[str] = field(default_factory=list)
    key_env: str = ""
    key_placeholder: str = "sk-xxx"
    requires_key: bool = True


# 预设提供商 = 快捷选项，帮用户省去查 URL 的麻烦
# 核心能力是"自定义"：任何 OpenAI 兼容 API 填 URL+Key+模型名就能用
PROVIDERS: dict[str, ProviderInfo] = {
    "deepseek": ProviderInfo(
        id="deepseek",
        name="DeepSeek",
        base_url="https://api.deepseek.com/v1",
        default_models=["deepseek-v4-flash", "deepseek-v3", "deepseek-r1"],
        key_env="DEEPSEEK_API_KEY",
    ),
    "xiaomi": ProviderInfo(
        id="xiaomi",
        name="小米 MiMo",
        base_url="https://api.xiaomi.com/v1",
        default_models=["mimo-v2-flash", "mimo-v2.5-pro"],
        key_env="XIAOMI_API_KEY",
    ),
    "openrouter": ProviderInfo(
        id="openrouter",
        name="OpenRouter",
        base_url="https://openrouter.ai/api/v1",
        default_models=[
            "anthropic/claude-sonnet-4",
            "openai/gpt-4o",
            "deepseek/deepseek-v4-flash",
        ],
        key_env="OPENROUTER_API_KEY",
    ),
    "openai": ProviderInfo(
        id="openai",
        name="OpenAI",
        base_url="https://api.openai.com/v1",
        default_models=["gpt-4o", "gpt-4-turbo", "gpt-4o-mini"],
        key_env="OPENAI_API_KEY",
    ),
    "anthropic": ProviderInfo(
        id="anthropic",
        name="Anthropic",
        base_url="https://api.anthropic.com/v1",
        default_models=["claude-sonnet-4", "claude-haiku"],
        key_env="ANTHROPIC_API_KEY",
        key_placeholder="sk-ant-xxx",
    ),
    "zhipu": ProviderInfo(
        id="zhipu",
        name="GLM / 智谱",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        default_models=["glm-5.1", "glm-4-flash", "glm-4"],
        key_env="ZHIPU_API_KEY",
    ),
    "kimi": ProviderInfo(
        id="kimi",
        name="Kimi / Moonshot",
        base_url="https://api.moonshot.cn/v1",
        default_models=["moonshot-v1-128k", "moonshot-v1-32k"],
        key_env="KIMI_API_KEY",
    ),
    "qwen": ProviderInfo(
        id="qwen",
        name="通义千问",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        default_models=["qwen-max", "qwen-plus", "qwen-turbo"],
        key_env="QWEN_API_KEY",
    ),
}


def get_provider(provider_id: str) -> ProviderInfo | None:
    return PROVIDERS.get(provider_id)


def list_providers() -> list[ProviderInfo]:
    return list(PROVIDERS.values())
