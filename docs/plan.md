# AgentPulse 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 构建 `agentpulse setup` 命令，让用户通过交互式向导配置多模型自动切换

**架构：** CLI 应用（click），扫描已知提供商的模型列表，检测可用性，生成 fallback chain 写入 Hermes config.yaml

**技术栈：** Python 3.11+, click, httpx, rich, pyyaml

---

## 项目文件结构

```
agentpulse/
├── README.md
├── LICENSE
├── pyproject.toml
├── src/
│   └── agentpulse/
│       ├── __init__.py
│       ├── cli.py              # CLI 入口
│       ├── setup_wizard.py     # setup 交互向导
│       ├── model_scanner.py    # 扫描可用模型
│       ├── config_writer.py    # 写入 Hermes 配置
│       ├── detector.py         # 模型可用性检测
│       ├── status.py           # status 命令
│       └── providers/
│           ├── __init__.py
│           ├── registry.py     # 提供商注册表
│           ├── deepseek.py
│           ├── xiaomi.py
│           ├── openai.py
│           ├── anthropic.py
│           ├── zhipu.py
│           ├── kimi.py
│           ├── qwen.py
│           ├── openrouter.py
│           └── custom.py
├── tests/
│   ├── __init__.py
│   ├── test_scanner.py
│   ├── test_detector.py
│   └── test_config_writer.py
└── docs/
    └── spec.md
```

---

## 任务 1：项目骨架

**文件：**
- 创建：`pyproject.toml`
- 创建：`src/agentpulse/__init__.py`
- 创建：`src/agentpulse/cli.py`
- 创建：`README.md`
- 创建：`LICENSE`

- [ ] **步骤 1：创建项目目录和 pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0", "setuptools-scm"]
build-backend = "setuptools.build_meta"

[project]
name = "agentpulse"
version = "0.1.0"
description = "Self-healing health monitor for AI Agents"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.11"
dependencies = [
    "click>=8.0",
    "httpx>=0.25",
    "rich>=13.0",
    "pyyaml>=6.0",
]

[project.scripts]
agentpulse = "agentpulse.cli:main"

[tool.setuptools.packages.find]
where = ["src"]
```

- [ ] **步骤 2：创建 __init__.py**

```python
"""AgentPulse — Self-healing health monitor for AI Agents."""
__version__ = "0.1.0"
```

- [ ] **步骤 3：创建 cli.py 骨架**

```python
"""AgentPulse CLI entry point."""
import click

@click.group()
@click.version_option()
def main():
    """🩺 AgentPulse — Self-healing health monitor for AI Agents."""
    pass

@main.command()
def setup():
    """交互式配置多模型自动切换。"""
    click.echo("🩺 AgentPulse Setup — 敬请期待")

@main.command()
def status():
    """查看当前模型状态。"""
    click.echo("🩺 AgentPulse Status — 敬请期待")

@main.command()
def test():
    """测试所有已配置模型。"""
    click.echo("🩺 AgentPulse Test — 敬请期待")
```

- [ ] **步骤 4：创建 README.md**

```markdown
# 🩺 AgentPulse

> 一条命令搞定多模型管理 + 自动切换

## 问题

- `hermes model` 只能配一个模型，改不了 key
- URL 填错了不知道，跑起来才报错
- 模型挂了要手动排查、手动切换

## 解决

```
agentpulse setup
    ↓
① 列出常见提供商，让你选择
② 输入 Key，自动查询可用模型
③ 检测所有模型状态（能不能通、延迟多少）
④ 自动生成 fallback chain（主→备1→备2→...）
⑤ 写入配置，模型有问题自动切换
```

## 安装

```bash
pip install agentpulse
# 或
uv pip install -e .
```

## 使用

```bash
agentpulse setup    # 配置向导
agentpulse status   # 查看状态
agentpulse test     # 测试模型
```

## License

MIT
```

- [ ] **步骤 5：创建 LICENSE**

MIT License

- [ ] **步骤 6：安装并验证**

```bash
cd /home/seino/projects/agentpulse
uv venv .venv
source .venv/bin/activate
uv pip install -e .
agentpulse --version
# 预期: agentpulse, version 0.1.0
```

- [ ] **步骤 7：Commit**

```bash
git init
git add -A
git commit -m "feat: init project skeleton"
```

---

## 任务 2：提供商注册表

**文件：**
- 创建：`src/agentpulse/providers/__init__.py`
- 创建：`src/agentpulse/providers/registry.py`

- [ ] **步骤 1：创建 registry.py**

```python
"""已知模型提供商注册表。"""
from dataclasses import dataclass, field

@dataclass
class ProviderInfo:
    id: str                       # 唯一标识
    name: str                     # 显示名称
    base_url: str                 # API 基础 URL
    models_endpoint: str = "/models"
    chat_endpoint: str = "/chat/completions"
    default_models: list[str] = field(default_factory=list)
    key_env: str = ""             # 环境变量名
    key_placeholder: str = "sk-xxx"  # Key 输入提示
    requires_key: bool = True

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
        default_models=["anthropic/claude-sonnet-4", "openai/gpt-4o", "deepseek/deepseek-v4-flash"],
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
```

- [ ] **步骤 2：创建 providers/__init__.py**

```python
from .registry import ProviderInfo, PROVIDERS, get_provider, list_providers
```

- [ ] **步骤 3：Commit**

```bash
git add -A
git commit -m "feat: add provider registry"
```

---

## 任务 3：模型检测器

**文件：**
- 创建：`src/agentpulse/detector.py`
- 创建：`tests/test_detector.py`

- [ ] **步骤 1：编写测试**

```python
"""测试模型可用性检测。"""
import pytest
from agentpulse.detector import ModelStatus, detect_model

def test_model_status_dataclass():
    status = ModelStatus(
        model="test-model",
        provider="test",
        available=True,
        latency_ms=100.0,
    )
    assert status.available is True
    assert status.latency_ms == 100.0

def test_detect_model_with_invalid_url():
    """无效 URL 应该返回不可用。"""
    status = detect_model(
        base_url="http://localhost:99999/v1",
        api_key="fake-key",
        model="test-model",
    )
    assert status.available is False
    assert status.error is not None
```

- [ ] **步骤 2：运行测试验证失败**

```bash
cd /home/seino/projects/agentpulse
pytest tests/test_detector.py -v
```

- [ ] **步骤 3：实现 detector.py**

```python
"""模型可用性检测。"""
import time
from dataclasses import dataclass
import httpx

@dataclass
class ModelStatus:
    model: str
    provider: str
    available: bool
    latency_ms: float = 0.0
    error: str | None = None

def detect_model(base_url: str, api_key: str, model: str, timeout: float = 10.0) -> ModelStatus:
    """检测单个模型是否可用。"""
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1,
    }
    
    start = time.monotonic()
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=payload, headers=headers)
        elapsed = (time.monotonic() - start) * 1000
        
        if resp.status_code == 200:
            return ModelStatus(model=model, provider="", available=True, latency_ms=round(elapsed, 1))
        elif resp.status_code == 401:
            return ModelStatus(model=model, provider="", available=False, error="认证失败 (401)")
        elif resp.status_code == 404:
            return ModelStatus(model=model, provider="", available=False, error="模型不存在 (404)")
        elif resp.status_code == 429:
            return ModelStatus(model=model, provider="", available=False, error="限流 (429)")
        else:
            return ModelStatus(model=model, provider="", available=False, error=f"HTTP {resp.status_code}")
    except httpx.ConnectError:
        return ModelStatus(model=model, provider="", available=False, error="连接失败")
    except httpx.TimeoutException:
        return ModelStatus(model=model, provider="", available=False, error="超时")
    except Exception as e:
        return ModelStatus(model=model, provider="", available=False, error=str(e))
```

- [ ] **步骤 4：运行测试验证通过**

```bash
pytest tests/test_detector.py -v
```

- [ ] **步骤 5：Commit**

```bash
git add -A
git commit -m "feat: add model availability detector"
```

---

## 任务 4：交互式 Setup 向导

**文件：**
- 创建：`src/agentpulse/setup_wizard.py`

- [ ] **步骤 1：实现 setup_wizard.py**

```python
"""交互式配置向导。"""
import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

from .providers import list_providers, get_provider, ProviderInfo
from .detector import detect_model, ModelStatus

console = Console()

def run_setup():
    """运行配置向导。"""
    console.print("\n🩺 [bold]AgentPulse — 模型配置向导[/bold]\n")
    
    # 第 1 步：选择提供商
    console.print("[bold]第 1 步：选择提供商[/bold]")
    console.print("━" * 40)
    
    providers = list_providers()
    for i, p in enumerate(providers, 1):
        console.print(f"  {i}) {p.name}")
    
    choices = Prompt.ask(
        "\n选择提供商 (逗号分隔)",
        default="1,2"
    )
    
    selected_indices = [int(x.strip()) - 1 for x in choices.split(",")]
    selected_providers = [providers[i] for i in selected_indices if 0 <= i < len(providers)]
    
    # 第 2 步：配置每个提供商
    console.print(f"\n[bold]第 2 步：配置提供商[/bold]")
    console.print("━" * 40)
    
    configured_models = []  # list of (provider_id, model_name, api_key, base_url)
    
    for provider in selected_providers:
        console.print(f"\n→ [cyan]{provider.name}[/cyan]")
        
        # 输入 API URL
        base_url = Prompt.ask(
            f"  API URL [{provider.base_url}]",
            default=provider.base_url
        )
        
        # 输入 API Key
        api_key = ""
        if provider.requires_key:
            api_key = Prompt.ask(f"  API Key ({provider.key_placeholder})")
        
        # 检测可用模型
        console.print("  检测模型中...")
        
        for model_name in provider.default_models:
            status = detect_model(base_url, api_key, model_name)
            if status.available:
                console.print(f"    ✓ [green]{model_name}[/green] (延迟 {status.latency_ms}ms)")
                configured_models.append({
                    "provider_id": provider.id,
                    "provider_name": provider.name,
                    "model": model_name,
                    "base_url": base_url,
                    "api_key": api_key,
                    "latency_ms": status.latency_ms,
                })
            else:
                console.print(f"    ✗ [red]{model_name}[/red] ({status.error})")
        
        if not configured_models:
            console.print(f"  ⚠ {provider.name} 没有可用模型")
    
    if not configured_models:
        console.print("\n[red]没有可用模型，无法生成配置。[/red]")
        return
    
    # 第 3 步：生成 Fallback Chain
    console.print(f"\n[bold]第 3 步：生成 Fallback Chain[/bold]")
    console.print("━" * 40)
    
    # 按延迟排序
    configured_models.sort(key=lambda m: m["latency_ms"])
    
    console.print("  推荐切换顺序 (按延迟排序):\n")
    for i, m in enumerate(configured_models):
        role = "[bold green]主力[/bold green]" if i == 0 else f"备用 {i}"
        console.print(f"  {i+1}. {m['model']} ({m['provider_name']}) — {m['latency_ms']}ms — {role}")
    
    accept = Confirm.ask("\n接受推荐？", default=True)
    
    if not accept:
        console.print("  请手动排序 (输入编号，逗号分隔):")
        order = Prompt.ask("  顺序")
        order_indices = [int(x.strip()) - 1 for x in order.split(",")]
        configured_models = [configured_models[i] for i in order_indices if 0 <= i < len(configured_models)]
    
    # 第 4 步：写入配置
    console.print(f"\n[bold]第 4 步：写入配置[/bold]")
    console.print("━" * 40)
    
    from .config_writer import write_hermes_config, write_agentpulse_config
    
    write_hermes_config(configured_models)
    write_agentpulse_config(configured_models)
    
    console.print("  ✓ 已写入 Hermes 配置")
    console.print("  ✓ 已写入 AgentPulse 配置")
    
    console.print(f"\n[green]配置完成！模型有问题时会自动切换，不用你管。[/green]")
    console.print("  查看状态: [cyan]agentpulse status[/cyan]")
    console.print("  测试模型: [cyan]agentpulse test[/cyan]\n")
```

- [ ] **步骤 2：Commit**

```bash
git add -A
git commit -m "feat: add interactive setup wizard"
```

---

## 任务 5：配置写入器

**文件：**
- 创建：`src/agentpulse/config_writer.py`
- 创建：`tests/test_config_writer.py`

- [ ] **步骤 1：编写测试**

```python
"""测试配置写入。"""
import pytest
import tempfile
import os
import yaml
from agentpulse.config_writer import build_hermes_config

def test_build_hermes_config():
    """测试生成 Hermes 配置内容。"""
    models = [
        {"provider_id": "deepseek", "model": "deepseek-v4-flash", "base_url": "https://api.deepseek.com/v1", "api_key": "sk-test", "latency_ms": 200},
        {"provider_id": "xiaomi", "model": "mimo-v2-flash", "base_url": "https://api.xiaomi.com/v1", "api_key": "sk-test2", "latency_ms": 150},
    ]
    config = build_hermes_config(models)
    
    assert "providers" in config
    assert "fallback" in config
    assert config["fallback"]["primary"] == "deepseek/deepseek-v4-flash"
    assert len(config["fallback"]["chain"]) == 2
```

- [ ] **步骤 2：实现 config_writer.py**

```python
"""写入 Hermes 和 AgentPulse 配置。"""
import os
import shutil
from pathlib import Path
import yaml

HERMES_CONFIG = Path.home() / ".hermes" / "config.yaml"
AGENTPULSE_CONFIG = Path.home() / ".agentpulse" / "config.yaml"

def build_hermes_config(models: list[dict]) -> dict:
    """构建 Hermes 配置内容。"""
    providers = {}
    fallback_chain = []
    
    for m in models:
        pid = m["provider_id"]
        provider_key = f"{pid}_agentpulse"
        
        providers[provider_key] = {
            "type": "openai",
            "base_url": m["base_url"],
            "api_key_env": f"{pid.upper()}_API_KEY_AGENTPULSE",
            "models": [m["model"]],
        }
        fallback_chain.append(f"{provider_key}/{m['model']}")
    
    return {
        "providers": providers,
        "fallback": {
            "primary": fallback_chain[0] if fallback_chain else "",
            "chain": fallback_chain[1:] if len(fallback_chain) > 1 else [],
        },
    }

def write_hermes_config(models: list[dict]):
    """写入 Hermes 配置（合并已有配置）。"""
    new_config = build_hermes_config(models)
    
    # 备份已有配置
    if HERMES_CONFIG.exists():
        backup_dir = Path.home() / ".agentpulse" / "backup"
        backup_dir.mkdir(parents=True, exist_ok=True)
        import time
        backup_name = f"config-{int(time.time())}.yaml.bak"
        shutil.copy2(HERMES_CONFIG, backup_dir / backup_name)
        
        # 合并已有配置
        with open(HERMES_CONFIG) as f:
            existing = yaml.safe_load(f) or {}
        
        if "providers" not in existing:
            existing["providers"] = {}
        existing["providers"].update(new_config["providers"])
        existing["fallback"] = new_config["fallback"]
        
        with open(HERMES_CONFIG, "w") as f:
            yaml.dump(existing, f, default_flow_style=False, allow_unicode=True)
    else:
        HERMES_CONFIG.parent.mkdir(parents=True, exist_ok=True)
        with open(HERMES_CONFIG, "w") as f:
            yaml.dump(new_config, f, default_flow_style=False, allow_unicode=True)

def write_agentpulse_config(models: list[dict]):
    """写入 AgentPulse 自己的配置。"""
    AGENTPULSE_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    
    config = {
        "agentpulse": {
            "models": models,
            "fallback_chain": [f"{m['provider_id']}/{m['model']}" for m in models],
        }
    }
    
    with open(AGENTPULSE_CONFIG, "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
```

- [ ] **步骤 3：运行测试**

```bash
pytest tests/test_config_writer.py -v
```

- [ ] **步骤 4：Commit**

```bash
git add -A
git commit -m "feat: add config writer for Hermes and AgentPulse"
```

---

## 任务 6：Status 和 Test 命令

**文件：**
- 创建：`src/agentpulse/status.py`

- [ ] **步骤 1：实现 status.py**

```python
"""查看当前模型状态。"""
import yaml
from pathlib import Path
from rich.console import Console
from rich.table import Table
from .detector import detect_model

console = Console()
AGENTPULSE_CONFIG = Path.home() / ".agentpulse" / "config.yaml"

def run_status():
    """显示当前配置和模型状态。"""
    if not AGENTPULSE_CONFIG.exists():
        console.print("[red]尚未配置。请先运行: agentpulse setup[/red]")
        return
    
    with open(AGENTPULSE_CONFIG) as f:
        config = yaml.safe_load(f)
    
    models = config.get("agentpulse", {}).get("models", [])
    chain = config.get("agentpulse", {}).get("fallback_chain", [])
    
    console.print("\n🩺 [bold]AgentPulse — 模型状态[/bold]\n")
    
    table = Table()
    table.add_column("模型", style="cyan")
    table.add_column("提供商")
    table.add_column("状态")
    table.add_column("延迟")
    
    for m in models:
        status = detect_model(m["base_url"], m["api_key"], m["model"])
        if status.available:
            table.add_row(
                m["model"],
                m.get("provider_name", m["provider_id"]),
                "[green]✓ 正常[/green]",
                f"{status.latency_ms}ms",
            )
        else:
            table.add_row(
                m["model"],
                m.get("provider_name", m["provider_id"]),
                f"[red]✗ {status.error}[/red]",
                "-",
            )
    
    console.print(table)
    
    console.print(f"\n  当前主力: [bold cyan]{chain[0]}[/bold cyan]" if chain else "")
    if len(chain) > 1:
        console.print(f"  Fallback: {' → '.join(chain[1:])}")
    console.print()
```

- [ ] **步骤 2：实现 test 命令**

在 `cli.py` 中更新 test 命令，调用 status 模块的逻辑并发送测试消息。

- [ ] **步骤 3：Commit**

```bash
git add -A
git commit -m "feat: add status and test commands"
```

---

## 任务 7：串联 CLI + 端到端测试

**文件：**
- 修改：`src/agentpulse/cli.py`

- [ ] **步骤 1：更新 cli.py 连接所有模块**

```python
"""AgentPulse CLI entry point."""
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
    from .status import run_status
    run_status()  # test 和 status 共享检测逻辑
```

- [ ] **步骤 2：端到端手动测试**

```bash
cd /home/seino/projects/agentpulse
source .venv/bin/activate
agentpulse --version
agentpulse setup
agentpulse status
```

- [ ] **步骤 3：Final Commit**

```bash
git add -A
git commit -m "feat: wire up CLI with all modules"
```

---

## 任务总结

| 任务 | 内容 | 预计时间 |
|------|------|---------|
| 1 | 项目骨架 | 5 分钟 |
| 2 | 提供商注册表 | 5 分钟 |
| 3 | 模型检测器 | 10 分钟 |
| 4 | Setup 向导 | 15 分钟 |
| 5 | 配置写入器 | 10 分钟 |
| 6 | Status/Test 命令 | 10 分钟 |
| 7 | 串联 + 端到端 | 5 分钟 |

总计：约 60 分钟
