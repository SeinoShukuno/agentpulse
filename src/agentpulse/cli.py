"""AgentPulse CLI 入口。"""
import click


@click.group()
@click.version_option(version="0.1.0", prog_name="agentpulse")
def main():
    """🩺 AgentPulse — 一条命令搞定多模型管理 + 自动切换。"""
    pass


@main.command()
def setup():
    """交互式配置多模型自动切换。"""
    from .setup_wizard import run_setup
    run_setup()


@main.command()
def status():
    """查看当前模型状态。"""
    from .status import run_status
    run_status()


@main.command()
def test():
    """测试所有已配置模型。"""
    from .status import run_test
    run_test()
