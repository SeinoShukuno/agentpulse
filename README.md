# 🩺 AgentPulse

> **一条命令搞定 AI 模型管理 + 自动切换。**

让你的 AI Agent 出问题时自动切模型，不用手动排查。

## 解决什么问题？

- `hermes model` 只能配一个模型，改不了 Key
- URL 填错了不知道，跑起来才报错
- 模型挂了要手动排查、手动切换
- 不知道有哪些模型可选、哪个能用

## 怎么用？

```bash
ap setup     # 交互式配置向导
ap status    # 查看模型状态
```

## 特性

- ✅ 8 大提供商预设（DeepSeek、小米、OpenAI、Anthropic、GLM、Kimi、千问、OpenRouter）
- ✅ 自定义支持（任何 OpenAI 兼容 API，填 URL + Key + 模型名）
- ✅ 自动检测模型可用性 + 延迟
- ✅ `/v1/models` 自动发现模型
- ✅ 模糊匹配模型名（输入 `v4pro` 自动匹配 `deepseek-v4-pro`）
- ✅ 按延迟排序生成 Fallback Chain
- ✅ 写入 Hermes 配置，出问题自动切换
- ✅ 无需守护进程

## 安装

```bash
git clone https://github.com/SeinoShukuno/agentpulse.git
cd agentpulse
pip install -e .
```

## 使用

### 配置向导

```bash
ap setup
```

向导会：
1. 列出常见提供商供你选择（或自定义 URL + Key + 模型名）
2. 自动检测所有模型状态（能不能通、延迟多少）
3. 按延迟排序生成 Fallback Chain
4. 写入 Hermes 配置，模型有问题自动切换

### 查看状态

```bash
ap status
```

显示当前配置的模型状态、延迟、Fallback Chain。

### 预览模式

```bash
ap setup --dry-run
```

走完整流程但不写入任何配置，安全测试。

## 兼容

- **主平台：** [Hermes Agent](https://github.com/nousresearch/hermes-agent)
- **任何 OpenAI 兼容 API**（Ollama、vLLM、LiteLLM 等）

## License

MIT
