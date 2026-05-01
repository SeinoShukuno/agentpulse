"""交互式配置向导 — AgentPulse 的核心。"""
import click
from rich.console import Console
from rich.prompt import Confirm, Prompt

from .providers import list_providers, ProviderInfo
from .detector import detect_model

console = Console()


def _scan_provider_models(
    base_url: str, api_key: str, models: list[str]
) -> list[dict]:
    """扫描一组模型，返回可用的列表。"""
    available = []
    for model_name in models:
        status = detect_model(base_url, api_key, model_name)
        if status.available:
            console.print(f"    ✓ [green]{model_name}[/green]  ({status.latency_ms}ms)")
            available.append({
                "model": model_name,
                "latency_ms": status.latency_ms,
            })
        else:
            console.print(f"    ✗ [red]{model_name}[/red]  ({status.error})")
    return available


def _configure_provider(provider: ProviderInfo) -> list[dict]:
    """配置单个预设提供商，返回可用模型列表。"""
    console.print(f"\n→ [cyan]{provider.name}[/cyan]")

    base_url = Prompt.ask(
        f"  API URL",
        default=provider.base_url,
    )

    api_key = ""
    if provider.requires_key:
        api_key = Prompt.ask(f"  API Key ({provider.key_placeholder})")

    console.print("  检测模型中...")
    available = _scan_provider_models(base_url, api_key, provider.default_models)

    if not available:
        # 预设模型全不可用时，让用户手动输入模型名
        console.print(f"  ⚠ 预设模型均不可用")
        manual = Prompt.ask("  手动输入模型名 (留空跳过)", default="")
        if manual:
            status = detect_model(base_url, api_key, manual)
            if status.available:
                console.print(f"    ✓ [green]{manual}[/green]  ({status.latency_ms}ms)")
                available.append({"model": manual, "latency_ms": status.latency_ms})
            else:
                console.print(f"    ✗ [red]{manual}[/red]  ({status.error})")

    # 给每个结果补上 provider 信息
    result = []
    for a in available:
        result.append({
            "provider_id": provider.id,
            "provider_name": provider.name,
            "model": a["model"],
            "base_url": base_url,
            "api_key": api_key,
            "latency_ms": a["latency_ms"],
        })
    return result


def _configure_custom() -> list[dict]:
    """自定义提供商配置。"""
    console.print(f"\n→ [cyan]自定义提供商[/cyan]")
    console.print("  (任何 OpenAI 兼容 API 都行)\n")

    name = Prompt.ask("  名称", default="my-provider")
    base_url = Prompt.ask("  API URL (如 http://localhost:11434/v1)")
    api_key = Prompt.ask("  API Key (留空则不需要)", default="")

    models_input = Prompt.ask("  模型名 (多个用逗号分隔)")
    models = [m.strip() for m in models_input.split(",") if m.strip()]

    console.print("  检测模型中...")
    available = _scan_provider_models(base_url, api_key, models)

    # 让用户确认用哪些
    if len(available) > 1:
        console.print(f"\n  可用模型: {', '.join(a['model'] for a in available)}")
        use_all = Confirm.ask("  全部添加？", default=True)
        if not use_all:
            picks = Prompt.ask("  选择 (逗号分隔模型名)")
            pick_set = {p.strip() for p in picks.split(",")}
            available = [a for a in available if a["model"] in pick_set]

    pid = name.lower().replace(" ", "-")
    return [
        {
            "provider_id": pid,
            "provider_name": name,
            "model": a["model"],
            "base_url": base_url,
            "api_key": api_key,
            "latency_ms": a["latency_ms"],
        }
        for a in available
    ]


def run_setup():
    """运行配置向导主流程。"""
    console.print("\n🩺 [bold]AgentPulse — 模型配置向导[/bold]\n")
    console.print("  目标：配好模型，出问题自动切换，不用你管。\n")

    # ── 第 1 步：选择提供商 ──
    console.print("[bold]第 1 步：选择提供商[/bold]")
    console.print("━" * 40)

    providers = list_providers()
    for i, p in enumerate(providers, 1):
        default_models_preview = ", ".join(p.default_models[:3])
        console.print(f"  {i}) {p.name:<16} ({default_models_preview})")
    console.print(f"  {len(providers)+1}) 自定义 (URL + Key + 模型名)")

    choices = Prompt.ask(
        "\n选择 (逗号分隔，如 1,2,9)",
        default="1,2",
    )

    choice_indices = [int(x.strip()) for x in choices.split(",") if x.strip().isdigit()]
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
        console.print(
            f"  {i+1}. {m['model']:<24} "
            f"({m['provider_name']})  "
            f"{m['latency_ms']}ms  — {role}"
        )

    accept = Confirm.ask("\n接受推荐？", default=True)

    if not accept:
        order_input = Prompt.ask("  输入顺序 (编号，逗号分隔)")
        order_indices = [int(x.strip()) - 1 for x in order_input.split(",")]
        all_models = [all_models[i] for i in order_indices if 0 <= i < len(all_models)]

    # ── 第 4 步：写入配置 ──
    console.print(f"\n[bold]第 4 步：写入配置[/bold]")
    console.print("━" * 40)

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
