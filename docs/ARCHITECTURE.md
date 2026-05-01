# 架构文档

## 整体架构

AgentPulse 是一个**单次运行的 CLI 工具**，不是守护进程。它在用户执行 `ap setup` 时完成所有工作，然后退出。

```
用户输入
    │
    ▼
┌─────────────────────────────────────────────┐
│ CLI 层 (cli.py)                              │
│   click 命令分发                              │
└─────────┬───────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────┐
│ Setup Wizard (setup_wizard.py)               │
│   ① 选择提供商                                │
│   ② 输入 Key + URL                            │
│   ③ 调用 Scanner 检测模型                      │
│   ④ 模糊匹配 + 排序                           │
│   ⑤ 调用 Writer 写入配置                      │
└─────┬───────────────┬───────────────────────┘
      │               │
      ▼               ▼
┌───────────┐   ┌───────────────┐
│ Scanner   │   │ Writer        │
│ (detector)│   │ (config_writer)│
│           │   │               │
│ HTTP ping │   │ 写入 Hermes   │
│ + 重试    │   │ config.yaml   │
└───────────┘   └───────────────┘
      │
      ▼
┌─────────────────────────────────────────────┐
│ Provider Registry (providers/registry.py)     │
│   8 个预设提供商的 URL、模型列表、Key 环境变量   │
└─────────────────────────────────────────────┘
```

## 核心模块

### cli.py — CLI 入口

使用 click 框架定义命令。只做命令分发，不含业务逻辑。

```python
@click.group()
def main():
    """ap — 一条命令搞定多模型管理。"""

@main.command()
@click.option("--dry-run", is_flag=True)
def setup(dry_run): ...

@main.command()
def status(): ...
```

### setup_wizard.py — 配置向导

最核心的模块，约 400 行。负责整个交互流程：

- **提供商选择** — 列出预设 + 自定义选项
- **URL 渠道选择** — 多渠道提供商（如小米 Token/按量）让用户选
- **模型检测** — 调用 detector 检测每个模型
- **模糊匹配** — 用户输入 `v4pro` → 匹配 `deepseek-v4-pro`
- **排序生成** — 按延迟排序，生成 Fallback Chain

### detector.py — 模型检测器

发送最小的 chat/completions 请求来判断模型可用性。

**特性：**
- 自动重试（网络异常 + 5xx 错误）
- 指数退避（1s → 2s → 4s）
- 详细错误分类（401 认证、404 不存在、429 限流）
- 延迟测量

**不重试的情况：**
- 401/403/404 — 确定性错误，重试没用
- 超时后重试 — 给网络一个恢复的机会

### config_writer.py — 配置写入器

将检测结果写入两个文件：

**~/.hermes/config.yaml（合并模式）：**
- 读取已有配置
- 只动 `providers` 和 `fallback` 字段
- provider 用 `_ap` 后缀（如 `deepseek_ap`）避免覆盖用户已有配置
- 写入前自动备份

**~/.agentpulse/config.yaml（AgentPulse 自己的记录）：**
- 记录用户选了什么模型、延迟多少
- `ap status` 读取这个文件

### providers/registry.py — 提供商注册表

预设提供商的静态配置。每个提供商包含：

```python
@dataclass
class ProviderInfo:
    id: str                    # 唯一标识
    name: str                  # 显示名称
    urls: list[ProviderURL]    # 可用 URL 渠道
    default_models: list[str]  # 预设模型列表
    deprecated_models: list[str]  # 弃用模型（带警告）
    key_env: str               # 环境变量名
    requires_key: bool         # 是否需要 Key
    models_auto_discover: bool # 是否支持 /v1/models
```

## 与 Hermes 的关系

```
AgentPulse 不是 Hermes 的插件或扩展。
它是一个独立的配置生成器。

ap setup → 生成配置 → 写入 ~/.hermes/config.yaml
                                    │
                                    ▼
                          Hermes 运行时读取
                          使用 fallback 机制切换模型
```

AgentPulse 的 `_ap` 后缀命名策略确保不会覆盖用户已有的 provider 配置。

## 数据流

```
ap setup:
  用户选择 → 提供商注册表 → URL + Key
                              │
                              ▼
                        /v1/models 自动发现
                              │
                              ▼
                        模型列表 + 预设模型
                              │
                              ▼
                        HTTP ping 检测（带重试）
                              │
                              ▼
                        可用模型 + 延迟排序
                              │
                              ▼
                        写入 Hermes config.yaml
                        写入 AgentPulse config.yaml

ap status:
  读取 AgentPulse config.yaml
  逐个 ping 已配置的模型
  显示状态表格
```

## 扩展点

### 添加新提供商

在 `providers/registry.py` 的 `PROVIDERS` 字典中添加条目：

```python
"new_provider": ProviderInfo(
    id="new_provider",
    name="新提供商",
    urls=[ProviderURL(url="...", label="官方", description="...")],
    default_models=["model-a", "model-b"],
    key_env="NEW_PROVIDER_API_KEY",
),
```

### 添加新检测方式

在 `detector.py` 中扩展 `detect_model` 函数，或添加新的检测函数。

### 添加新自愈策略

未来计划：`healers/` 目录下的可插拔自愈策略。
