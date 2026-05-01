# 🩺 AgentPulse

> **一条命令搞定 AI 模型管理 + 自动切换。**

## 这是什么？

AgentPulse 是一个**模型配置助手**——帮你检测哪些模型能用、哪个最快，然后自动生成最优配置写入 Hermes Agent。

**一句话：你只管填 Key，剩下的它帮你搞定。**

## 解决什么问题？

| 现在 | 用 AgentPulse |
|------|--------------|
| `hermes model` 只能配一个模型 | 一次配多个模型 |
| 改不了 Key | 直接填 Key |
| URL 填错了不知道 | 自动检测 URL + 模型可用性 |
| 不知道延迟多少 | 显示每个模型的延迟 |
| 没有 Fallback Chain | 自动生成切换顺序 |
| 模型挂了手动切 | **Hermes 原生自动切换** |

## 工作原理

```
ap setup
    │
    ▼
① 选择提供商（8 大预设 + 无限自定义）
② 输入 API Key
③ 自动检测模型可用性 + 延迟
④ 按延迟排序生成 Fallback Chain
⑤ 写入 Hermes 配置
    │
    ▼
Hermes 运行时：模型挂了 → 自动切到下一个
```

> **注意：** "自动切换"是 Hermes Agent 的 Fallback Chain 机制在运行时完成的。
> AgentPulse 的职责是：**帮你检测、帮你排序、帮你写配置**。
> 配置完成后，切换逻辑由 Hermes 原生驱动，不需要 AgentPulse 常驻运行。

## 快速开始

### 安装

```bash
git clone https://github.com/SeinoShukuno/agentpulse.git
cd agentpulse
pip install -e .
```

### 使用

```bash
ap setup           # 配置向导（第一次用）
ap setup --dry-run # 预览模式（不写入配置）
ap status          # 查看模型状态
```

### 示例

```bash
$ ap setup

🩺 AgentPulse — 模型配置向导

第 1 步：选择提供商
━━━━━━━━━━━━━━━━━━
  1) DeepSeek         (deepseek-v4-flash, deepseek-v4-pro)
  2) 小米 MiMo        (mimo-v2.5-pro, mimo-v2-flash)
  ...
  9) 自定义           (URL + Key + 模型名)

第 2 步：配置提供商
━━━━━━━━━━━━━━━━━━
→ DeepSeek
  URL: https://api.deepseek.com/v1  [DeepSeek 官方 base_url (OpenAI 兼容)]
  API Key: sk-xxx
  检测模型中...
    ✓ deepseek-v4-flash  (230ms)
    ✓ deepseek-v4-pro    (310ms)

第 3 步：生成 Fallback Chain
━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. deepseek-v4-flash    230ms  — 主力
  2. mimo-v2.5-pro        320ms  — 备用 1
  3. deepseek-v4-pro      310ms  — 备用 2

配置完成！模型有问题时 Hermes 会自动切换。
```

## 特性

- ✅ **8 大提供商预设**（DeepSeek、小米、OpenAI、Anthropic、GLM、Kimi、千问、OpenRouter）
- ✅ **自定义支持**（任何 OpenAI 兼容 API，填 URL + Key + 模型名）
- ✅ **自动检测模型可用性 + 延迟**（HTTP ping + 真实请求检测）
- ✅ **/v1/models 自动发现**（查询提供商有什么模型）
- ✅ **模糊匹配模型名**（输入 `v4pro` 自动匹配 `deepseek-v4-pro`）
- ✅ **URL 渠道识别**（提示是按量付费还是 Token 计费）
- ✅ **预览模式**（`--dry-run` 不写入配置，安全测试）
- ✅ **无需守护进程**（配置完就完事）

## 兼容性

| 平台 | 支持程度 |
|------|---------|
| [Hermes Agent](https://github.com/nousresearch/hermes-agent) | ✅ 主平台，深度集成 |
| 任何 OpenAI 兼容 API | ✅ 通用支持（Ollama、vLLM、LiteLLM 等） |
| OpenClaw | 🔜 计划中 |

## 项目结构

```
agentpulse/
├── src/agentpulse/
│   ├── cli.py              # CLI 入口
│   ├── setup_wizard.py     # 交互式配置向导
│   ├── detector.py         # 模型可用性检测
│   ├── config_writer.py    # Hermes 配置写入
│   ├── status.py           # 状态展示
│   └── providers/
│       └── registry.py     # 提供商注册表
├── tests/                  # 单元测试
├── docs/
│   ├── spec.md             # 设计规格
│   ├── plan.md             # 实现计划
│   └── ARCHITECTURE.md     # 架构文档
├── CONTRIBUTING.md         # 贡献指南
├── pyproject.toml          # 项目配置
└── LICENSE                 # MIT
```

## 贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

## License

[MIT](LICENSE)
