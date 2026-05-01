"""查看当前模型状态。"""
from pathlib import Path

import yaml
from rich.console import Console
from rich.table import Table

from .detector import detect_model

console = Console()
AGENTPULSE_CONFIG = Path.home() / ".agentpulse" / "config.yaml"


def run_status():
    """显示当前配置和模型状态。"""
    if not AGENTPULSE_CONFIG.exists():
        console.print("[red]尚未配置。请先运行: ap setup[/red]")
        return

    with open(AGENTPULSE_CONFIG) as f:
        config = yaml.safe_load(f)

    ap = config.get("agentpulse", {})
    models = ap.get("models", [])
    chain = ap.get("fallback_chain", [])

    console.print("\n🩺 [bold]AgentPulse — 模型状态[/bold]\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=3)
    table.add_column("模型", style="cyan")
    table.add_column("提供商")
    table.add_column("状态")
    table.add_column("延迟", justify="right")

    for i, m in enumerate(models, 1):
        status = detect_model(m["base_url"], m["api_key"], m["model"])
        if status.available:
            table.add_row(
                str(i),
                m["model"],
                m.get("provider_name", m["provider_id"]),
                "[green]✓ 正常[/green]",
                f"{status.latency_ms}ms",
            )
        else:
            table.add_row(
                str(i),
                m["model"],
                m.get("provider_name", m["provider_id"]),
                f"[red]✗ {status.error}[/red]",
                "—",
            )

    console.print(table)

    if chain:
        console.print(f"\n  当前主力: [bold cyan]{chain[0]}[/bold cyan]")
        if len(chain) > 1:
            console.print(f"  Fallback: {' → '.join(chain[1:])}")
    console.print()
