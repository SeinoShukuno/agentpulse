"""AgentPulse CLI 入口。"""
import click


@click.group()
@click.version_option(version="0.1.0", prog_name="ap")
def main():
    """🩺 AgentPulse — 一条命令搞定多模型管理 + 自动切换。"""
    pass


@main.command()
@click.option("--dry-run", is_flag=True, help="预览模式，不写入任何配置。")
def setup(dry_run):
    """交互式配置多模型自动切换。"""
    from .setup_wizard import run_setup
    run_setup(dry_run=dry_run)


@main.command()
def status():
    """查看当前模型状态。"""
    from .status import run_status
    run_status()
