"""交互式配置向导 — AgentPulse 的核心。"""
import difflib
import re

import click
import httpx
from rich.console import Console
from rich.prompt import Confirm, Prompt

from .detector import detect_model
from .providers import ProviderInfo, list_providers

console = Console()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 模型名模糊匹配
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _normalize(name: str) -> str:
    """标准化模型名：小写、去空格、去连字符/下划线/点。"""
    return re.sub(r"[\s\-_\.]", "", name.lower())


def _fuzzy_match(user_input: str, candidates: list[str]) -> str | None:
    """模糊匹配模型名。

    匹配规则（按优先级）：
    1. 精确匹配
    2. 标准化后完全匹配
    3. 标准化后包含匹配（用户输入是候选的子串）
    4. difflib 相似度 > 0.6
    """
    user_input = user_input.strip()
    if not user_input or not candidates:
        return None

    # 1. 精确匹配
    for c in candidates:
        if c == user_input:
            return c

    norm_input = _normalize(user_input)

    # 2. 标准化后完全匹配
    for c in candidates:
        if _normalize(c) == norm_input:
            return c

    # 3. 包含匹配
    matches = []
    for c in candidates:
        norm_c = _normalize(c)
        if norm_input in norm_c or norm_c in norm_input:
            matches.append(c)
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        # 选最短的（最精确的）
        return min(matches, key=len)

    # 4. difflib 相似度
    best = None
    best_ratio = 0.0
    for c in candidates:
        ratio = difflib.SequenceMatcher(None, norm_input, _normalize(c)).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best = c
    if best_ratio > 0.6:
        return best

    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 自动发现模型（调用 /v1/models）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _discover_models(base_url: str, api_key: str, timeout: float = 10.0) -> list[str]:
    """通过 /v1/models 端点自动发现可用模型。"""
    url = f"{base_url.rstrip('/')}/models"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            models = data.get("data", [])
            return [m["id"] for m in models if "id" in m]
    except Exception:
        pass
    return []


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 扫描检测模型
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _scan_models(
    base_url: str, api_key: str, models: list[str]
) -> list[dict]:
    """扫描一组模型，返回可用的列表。"""
    available = []
    for model_name in models:
        status = detect_model(base_url, api_key, model_name)
        if status.available:
            console.print(
                f"    ✓ [green]{model_name}[/green]  ({status.latency_ms}ms)"
            )
            available.append({
                "model": model_name,
                "latency_ms": status.latency_ms,
            })
        else:
            console.print(
                f"    ✗ [red]{model_name}[/red]  ({status.error})"
            )
    return available


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 选择 URL 渠道
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _select_url(provider: ProviderInfo) -> tuple[str, str]:
    """让用户选择 URL 渠道，返回 (url, label)。"""
    if len(provider.urls) == 1:
        url_info = provider.urls[0]
        console.print(f"  URL: [dim]{url_info.url}[/dim]")
        console.print(f"  渠道: [cyan]{url_info.description}[/cyan]")
        return url_info.url, url_info.label

    console.print("  可用渠道:")
    for i, u in enumerate(provider.urls, 1):
        console.print(f"    {i}) [{u.label}] {u.url}")
        console.print(f"       [dim]{u.description}[/dim]")

    choice = Prompt.ask(
        "  选择渠道",
        default="1",
    )
    idx = int(choice) - 1
    if 0 <= idx < len(provider.urls):
        url_info = provider.urls[idx]
        return url_info.url, url_info.label

    # fallback: 手动输入
    custom_url = Prompt.ask("  自定义 URL")
    return custom_url, "自定义"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 模型选择（带模糊匹配）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _pick_models(
    provider: ProviderInfo,
    base_url: str,
    api_key: str,
    discovered: list[str],
) -> list[str]:
    """让用户选择或输入模型名，自动匹配。

    流程：
    1. 先列出预设模型，检测哪些能用
    2. 如果自动发现了模型，列出供选择
    3. 用户可以输入模型名，模糊匹配
    4. 最后一项始终是"自定义输入"
    """
    all_known = list(provider.default_models)
    if provider.deprecated_models:
        all_known.extend(provider.deprecated_models)

    # 合并自动发现的模型
    if discovered:
        for d in discovered:
            if d not in all_known:
                all_known.append(d)

    console.print("  检测预设模型中...")
    available = _scan_models(base_url, api_key, all_known)

    if not available:
        console.print(f"  ⚠ 预设模型均不可用，请手动输入模型名")
        manual = Prompt.ask("  模型名 (多个用逗号分隔)")
        if not manual:
            return []
        names = [n.strip() for n in manual.split(",") if n.strip()]
        matched = []
        for n in names:
            # 模糊匹配到已知模型
            match = _fuzzy_match(n, all_known)
            if match and match != n:
                console.print(f"    [yellow]'{n}' → '{match}'[/yellow]")
                matched.append(match)
            else:
                matched.append(n)
        # 检测手动输入的模型
        console.print("  检测手动输入的模型...")
        detected = _scan_models(base_url, api_key, matched)
        return [d["model"] for d in detected]

    # 让用户选择
    console.print(f"\n  可用模型:")
    for i, a in enumerate(available, 1):
        deprecated = any(a["model"] in d for d in provider.deprecated_models)
        tag = " [yellow](即将弃用)[/yellow]" if deprecated else ""
        console.print(f"    {i}) {a['model']}  ({a['latency_ms']}ms){tag}")
    console.print(f"    {len(available)+1}) 自定义输入")

    picks = Prompt.ask(
        "\n  选择模型 (逗号分隔编号，如 1,2)",
        default=",".join(str(i) for i in range(1, min(4, len(available) + 1))),
    )

    selected = []
    for p in picks.split(","):
        p = p.strip()
        if p.isdigit():
            idx = int(p) - 1
            if 0 <= idx < len(available):
                selected.append(available[idx]["model"])
            elif idx == len(available):
                # 自定义输入
                manual = Prompt.ask("  输入模型名")
                if manual:
                    match = _fuzzy_match(manual, all_known)
                    if match and match != manual:
                        console.print(f"    [yellow]'{manual}' → '{match}'[/yellow]")
                        selected.append(match)
                    else:
                        # 检测这个模型
                        status = detect_model(base_url, api_key, manual)
                        if status.available:
                            console.print(
                                f"    ✓ [green]{manual}[/green]  ({status.latency_ms}ms)"
                            )
                            selected.append(manual)
                        else:
                            console.print(
                                f"    ✗ [red]{manual}[/red]  ({status.error})"
                            )
                            # 尝试模糊匹配后再检测
                            if match:
                                console.print(f"    尝试匹配: [yellow]{match}[/yellow]")
                                status2 = detect_model(base_url, api_key, match)
                                if status2.available:
                                    console.print(
                                        f"    ✓ [green]{match}[/green]  ({status2.latency_ms}ms)"
                                    )
                                    selected.append(match)
                                else:
                                    console.print(
                                        f"    ✗ [red]{match}[/red]  ({status2.error})"
                                    )
        else:
            # 非数字，当模型名处理
            match = _fuzzy_match(p, all_known)
            if match:
                console.print(f"    [yellow]'{p}' → '{match}'[/yellow]")
                selected.append(match)
            else:
                selected.append(p)

    return selected


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 配置单个预设提供商
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _configure_provider(provider: ProviderInfo) -> list[dict]:
    """配置单个预设提供商。"""
    console.print(f"\n→ [cyan]{provider.name}[/cyan]")

    # 选择 URL 渠道
    base_url, url_label = _select_url(provider)

    # 输入 API Key
    api_key = ""
    if provider.requires_key:
        api_key = Prompt.ask(f"  API Key ({provider.key_placeholder})")

    # 自动发现模型
    discovered = []
    if provider.models_auto_discover:
        console.print("  查询可用模型...")
        discovered = _discover_models(base_url, api_key)
        if discovered:
            console.print(f"  [dim]自动发现 {len(discovered)} 个模型[/dim]")

    # 选择模型
    selected_models = _pick_models(provider, base_url, api_key, discovered)

    if not selected_models:
        console.print(f"  ⚠ {provider.name} 没有选择任何模型")
        return []

    return [
        {
            "provider_id": provider.id,
            "provider_name": provider.name,
            "url_label": url_label,
            "model": m,
            "base_url": base_url,
            "api_key": api_key,
            "latency_ms": 0.0,
        }
        for m in selected_models
    ]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 自定义提供商
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _configure_custom() -> list[dict]:
    """自定义提供商配置。"""
    console.print(f"\n→ [cyan]自定义提供商[/cyan]")
    console.print("  (任何 OpenAI 兼容 API 都行)\n")

    name = Prompt.ask("  名称", default="my-provider")
    base_url = Prompt.ask("  API URL (如 http://localhost:11434/v1)")
    api_key = Prompt.ask("  API Key (留空则不需要)", default="")

    # 先尝试自动发现
    console.print("  查询可用模型...")
    discovered = _discover_models(base_url, api_key)
    if discovered:
        console.print(f"  [dim]自动发现 {len(discovered)} 个模型[/dim]")
        console.print(f"  模型列表: [dim]{', '.join(discovered[:10])}{'...' if len(discovered) > 10 else ''}[/dim]")

    if discovered:
        use_discovered = Confirm.ask("  使用自动发现的模型？", default=True)
        if use_discovered:
            console.print("  选择模型:")
            for i, m in enumerate(discovered[:20], 1):
                console.print(f"    {i}) {m}")
            picks = Prompt.ask(
                "  选择 (逗号分隔，或 'all' 全选)",
                default="all",
            )
            if picks.strip().lower() == "all":
                selected = discovered
            else:
                indices = [int(x.strip()) - 1 for x in picks.split(",") if x.strip().isdigit()]
                selected = [discovered[i] for i in indices if 0 <= i < len(discovered)]
        else:
            models_input = Prompt.ask("  模型名 (多个用逗号分隔)")
            selected = [m.strip() for m in models_input.split(",") if m.strip()]
    else:
        models_input = Prompt.ask("  模型名 (多个用逗号分隔)")
        selected = [m.strip() for m in models_input.split(",") if m.strip()]

    if not selected:
        return []

    console.print("  检测模型中...")
    available = _scan_models(base_url, api_key, selected)

    pid = name.lower().replace(" ", "-")
    return [
        {
            "provider_id": pid,
            "provider_name": name,
            "url_label": "自定义",
            "model": a["model"],
            "base_url": base_url,
            "api_key": api_key,
            "latency_ms": a["latency_ms"],
        }
        for a in available
    ]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 主流程
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_setup(dry_run: bool = False):
    """运行配置向导主流程。"""
    if dry_run:
        console.print(
            "\n🩺 [bold]AgentPulse — 模型配置向导[/bold] "
            "[yellow](预览模式)[/yellow]\n"
        )
        console.print("  ⚠ 预览模式：不会写入任何配置文件\n")
    else:
        console.print("\n🩺 [bold]AgentPulse — 模型配置向导[/bold]\n")
    console.print("  目标：配好模型，出问题自动切换，不用你管。\n")

    # ── 第 1 步：选择提供商 ──
    console.print("[bold]第 1 步：选择提供商[/bold]")
    console.print("━" * 40)

    providers = list_providers()
    for i, p in enumerate(providers, 1):
        models_preview = ", ".join(p.default_models[:3])
        console.print(f"  {i}) {p.name:<16} ({models_preview})")
    console.print(
        f"  {len(providers)+1}) {'自定义':<16} (URL + Key + 模型名)"
    )

    choices = Prompt.ask(
        "\n选择 (逗号分隔，如 1,2,9)",
        default="1,2",
    )

    choice_indices = [
        int(x.strip()) for x in choices.split(",") if x.strip().isdigit()
    ]
    custom_idx = len(providers) + 1

    # ── 第 2 步：配置每个提供商 ──
    console.print(f"\n[bold]第 2 步：配置提供商[/bold]")
    console.print("━" * 40)

    all_models = []

    for idx in choice_indices:
        if idx == custom_idx:
            models = _configure_custom()
            all_models.extend(models)
        elif 1 <= idx <= len(providers):
            provider = providers[idx - 1]
            models = _configure_provider(provider)
            all_models.extend(models)
        else:
            console.print(f"  ⚠ 无效选项: {idx}，跳过")

    if not all_models:
        console.print("\n[red]没有可用模型，无法生成配置。[/red]")
        return

    # ── 第 3 步：生成 Fallback Chain ──
    console.print(f"\n[bold]第 3 步：生成 Fallback Chain[/bold]")
    console.print("━" * 40)

    all_models.sort(key=lambda m: m["latency_ms"])

    console.print("  推荐切换顺序 (按延迟排序):\n")
    for i, m in enumerate(all_models):
        role = "[bold green]主力[/bold green]" if i == 0 else f"备用 {i}"
        label = f" [{m['url_label']}]" if m.get("url_label") else ""
        console.print(
            f"  {i+1}. {m['model']:<28} "
            f"({m['provider_name']}{label})  "
            f"{m['latency_ms']}ms  — {role}"
        )

    accept = Confirm.ask("\n接受推荐？", default=True)

    if not accept:
        order_input = Prompt.ask("  输入顺序 (编号，逗号分隔)")
        order_indices = [int(x.strip()) - 1 for x in order_input.split(",")]
        all_models = [
            all_models[i] for i in order_indices if 0 <= i < len(all_models)
        ]

    # ── 第 4 步：写入配置 ──
    console.print(f"\n[bold]第 4 步：写入配置[/bold]")
    console.print("━" * 40)

    if dry_run:
        console.print("  [yellow](预览模式 — 以下操作不会执行)[/yellow]")
        console.print(
            "  → 将写入 Hermes 配置: ~/.hermes/config.yaml"
        )
        console.print(
            "  → 将写入 AgentPulse 配置: ~/.agentpulse/config.yaml"
        )
        chain_str = " → ".join(m["model"] for m in all_models)
        console.print(f"  → Fallback Chain: {chain_str}")
        console.print(
            f"\n[green]预览完成！去掉 --dry-run 参数即可真正执行。[/green]\n"
        )
        return

    from .config_writer import write_hermes_config, write_agentpulse_config

    write_hermes_config(all_models)
    write_agentpulse_config(all_models)

    console.print("  ✓ 已写入 Hermes 配置")
    console.print("  ✓ 已写入 AgentPulse 配置")

    # ── 完成 ──
    console.print(f"\n[green bold]✅ 配置完成！[/green bold]")
    console.print("  模型有问题时会自动切换，不用你管。")
    console.print("  查看状态: [cyan]agentpulse status[/cyan]")
    console.print("  测试模型: [cyan]agentpulse test[/cyan]\n")
