"""提供商注册表 — 预设 + 自定义支持。"""
from dataclasses import dataclass, field


@dataclass
class ProviderURL:
    """一个提供商的 URL 渠道。"""
    url: str
    label: str           # 如 "按量付费" / "Token 计费" / "官方"
    description: str     # 如 "DeepSeek 官方 base_url (OpenAI 兼容)"


@dataclass
class ProviderInfo:
    """一个模型提供商的配置信息。"""
    id: str
    name: str
    urls: list[ProviderURL]
    default_models: list[str] = field(default_factory=list)
    deprecated_models: list[str] = field(default_factory=list)
    key_env: str = ""
    key_placeholder: str = "sk-xxx"
    requires_key: bool = True
    models_auto_discover: bool = True  # 是否支持 /v1/models 自动发现


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 预设提供商 = 快捷选项
# 核心能力是"自定义"：任何 OpenAI 兼容 API 填 URL+Key+模型名就能用
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROVIDERS: dict[str, ProviderInfo] = {
    "deepseek": ProviderInfo(
        id="deepseek",
        name="DeepSeek",
        urls=[
            ProviderURL(
                url="https://api.deepseek.com/v1",
                label="官方",
                description="DeepSeek 官方 base_url (OpenAI 兼容)",
            ),
        ],
        default_models=[
            "deepseek-v4-flash",
            "deepseek-v4-pro",
        ],
        deprecated_models=[
            "deepseek-chat (将于 2026/07/24 弃用)",
            "deepseek-reasoner (将于 2026/07/24 弃用)",
        ],
        key_env="DEEPSEEK_API_KEY",
    ),
    "xiaomi": ProviderInfo(
        id="xiaomi",
        name="小米 MiMo",
        urls=[
            ProviderURL(
                url="https://token-plan-cn.xiaomimimo.com/v1",
                label="Token 计费",
                description="小米 MiMo Token 计费渠道 (OpenAI 兼容)",
            ),
            ProviderURL(
                url="https://api.xiaomimimo.com/v1",
                label="按量付费",
                description="小米 MiMo 按量付费渠道 (OpenAI 兼容)",
            ),
        ],
        default_models=[
            "MiMo-V2.5-Pro",
            "MiMo-V2.5",
            "MiMo-V2-Pro",
            "MiMo-V2-Omni",
        ],
        deprecated_models=[
            "MiMo-V2.5-TTS-VoiceClone",
            "MiMo-V2.5-TTS-VoiceDesign",
            "MiMo-V2.5-TTS",
            "MiMo-V2-TTS",
        ],
        key_env="XIAOMI_API_KEY",
    ),
    "openrouter": ProviderInfo(
        id="openrouter",
        name="OpenRouter",
        urls=[
            ProviderURL(
                url="https://openrouter.ai/api/v1",
                label="官方",
                description="OpenRouter 官方网关 (100+ 模型，OpenAI 兼容)",
            ),
        ],
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
        urls=[
            ProviderURL(
                url="https://api.openai.com/v1",
                label="官方",
                description="OpenAI 官方 API",
            ),
        ],
        default_models=["gpt-4o", "gpt-4-turbo", "gpt-4o-mini"],
        key_env="OPENAI_API_KEY",
    ),
    "anthropic": ProviderInfo(
        id="anthropic",
        name="Anthropic",
        urls=[
            ProviderURL(
                url="https://api.anthropic.com/v1",
                label="官方",
                description="Anthropic 官方 API",
            ),
        ],
        default_models=["claude-sonnet-4", "claude-haiku"],
        key_env="ANTHROPIC_API_KEY",
        key_placeholder="sk-ant-xxx",
    ),
    "zhipu": ProviderInfo(
        id="zhipu",
        name="GLM / 智谱",
        urls=[
            ProviderURL(
                url="https://open.bigmodel.cn/api/paas/v4",
                label="官方",
                description="智谱 GLM 官方 API (OpenAI 兼容)",
            ),
        ],
        default_models=[
            "GLM-5.1",
            "GLM-5",
            "GLM-5-Turbo",
            "GLM-4.7",
            "GLM-4.7-FlashX",
            "GLM-4.6",
            "GLM-4.5-Air",
            "GLM-4.5-AirX",
            "GLM-4-Long",
            "GLM-4.7-Flash (免费)",
            "GLM-4.5-Flash (免费)",
            "GLM-4-Flash-250414 (免费)",
        ],
        deprecated_models=[
            "GLM-4.5-Flash (即将弃用)",
        ],
        key_env="ZHIPU_API_KEY",
    ),
    "kimi": ProviderInfo(
        id="kimi",
        name="Kimi / Moonshot",
        urls=[
            ProviderURL(
                url="https://api.moonshot.cn/v1",
                label="官方",
                description="Kimi / Moonshot 官方 API (OpenAI 兼容)",
            ),
        ],
        default_models=[
            "kimi-k2.6",
            "kimi-k2.5",
            "moonshot-v1-128k",
            "moonshot-v1-32k",
            "moonshot-v1-8k",
        ],
        deprecated_models=[
            "kimi-k2-0905-preview (将于 2026/05/25 弃用)",
            "kimi-k2-0711-preview (将于 2026/05/25 弃用)",
            "kimi-k2-turbo-preview (将于 2026/05/25 弃用)",
        ],
        key_env="KIMI_API_KEY",
    ),
    "qwen": ProviderInfo(
        id="qwen",
        name="通义千问",
        urls=[
            ProviderURL(
                url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                label="按量付费",
                description="阿里云百炼 按量付费 (OpenAI 兼容)",
            ),
            ProviderURL(
                url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                label="Token 计费",
                description="阿里云百炼 Token 计费 (同一 URL，不同计费方式)",
            ),
        ],
        default_models=[
            "qwen3.6-max-preview",
            "qwen3.6-plus",
            "qwen3.6-flash",
            "qwen3.5-plus",
        ],
        deprecated_models=[
            "qwen-max (旧版，建议升级到 qwen3.6 系列)",
            "qwen-plus (旧版)",
            "qwen-turbo (旧版)",
        ],
        key_env="QWEN_API_KEY",
    ),
}


def get_provider(provider_id: str) -> ProviderInfo | None:
    return PROVIDERS.get(provider_id)


def list_providers() -> list[ProviderInfo]:
    return list(PROVIDERS.values())
