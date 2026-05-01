"""写入 Hermes 和 AgentPulse 配置。"""
import shutil
import time
from pathlib import Path

import yaml

HERMES_CONFIG = Path.home() / ".hermes" / "config.yaml"
AGENTPULSE_DIR = Path.home() / ".agentpulse"
AGENTPULSE_CONFIG = AGENTPULSE_DIR / "config.yaml"


def build_hermes_provider_block(model_entry: dict) -> tuple[str, dict]:
    """为一个模型条目生成 Hermes provider 配置块。

    返回 (provider_key, provider_config_dict)。
    """
    pid = model_entry["provider_id"]
    provider_key = f"{pid}_ap"  # ap = agentpulse，避免覆盖用户已有配置
    return provider_key, {
        "type": "openai",
        "base_url": model_entry["base_url"],
        "api_key": model_entry["api_key"],
        "models": [model_entry["model"]],
    }


def build_hermes_fallback(models: list[dict]) -> dict:
    """构建 Hermes fallback 配置。"""
    entries = []
    for m in models:
        pid = m["provider_id"]
        key = f"{pid}_ap"
        entries.append(f"{key}/{m['model']}")

    if not entries:
        return {}
    return {
        "primary": entries[0],
        "chain": entries[1:] if len(entries) > 1 else [],
    }


def write_hermes_config(models: list[dict]):
    """写入 Hermes 配置（合并已有，不覆盖用户原有设置）。"""
    new_providers = {}
    for m in models:
        key, cfg = build_hermes_provider_block(m)
        new_providers[key] = cfg

    fallback = build_hermes_fallback(models)

    # 备份
    if HERMES_CONFIG.exists():
        backup_dir = AGENTPULSE_DIR / "backup"
        backup_dir.mkdir(parents=True, exist_ok=True)
        ts = int(time.time())
        shutil.copy2(HERMES_CONFIG, backup_dir / f"config-{ts}.yaml.bak")

        # 合并
        with open(HERMES_CONFIG) as f:
            existing = yaml.safe_load(f) or {}

        if "providers" not in existing:
            existing["providers"] = {}
        existing["providers"].update(new_providers)
        existing["fallback"] = fallback

        with open(HERMES_CONFIG, "w") as f:
            yaml.dump(existing, f, default_flow_style=False, allow_unicode=True)
    else:
        HERMES_CONFIG.parent.mkdir(parents=True, exist_ok=True)
        with open(HERMES_CONFIG, "w") as f:
            yaml.dump(
                {"providers": new_providers, "fallback": fallback},
                f, default_flow_style=False, allow_unicode=True,
            )


def write_agentpulse_config(models: list[dict]):
    """写入 AgentPulse 自己的配置。"""
    AGENTPULSE_DIR.mkdir(parents=True, exist_ok=True)

    config = {
        "agentpulse": {
            "version": "0.1.0",
            "models": [
                {
                    "provider_id": m["provider_id"],
                    "provider_name": m["provider_name"],
                    "model": m["model"],
                    "base_url": m["base_url"],
                    "api_key": m["api_key"],
                    "latency_ms": m["latency_ms"],
                }
                for m in models
            ],
            "fallback_chain": [
                f"{m['provider_id']}/{m['model']}" for m in models
            ],
        }
    }

    with open(AGENTPULSE_CONFIG, "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
