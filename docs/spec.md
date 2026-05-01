# AgentPulse 设计规格

> 一条命令搞定多模型管理 + 自动切换

## 项目定位

AgentPulse 解决的核心问题：

**现在：** `hermes model` 只能配一个模型，改不了 key，URL 填错了不知道，出问题要手动排查手动切。
**目标：** `agentpulse setup` → 填你知道的 → 自动检测 → 自动生成方案 → 出问题自动切。

类比：手动挡 → 自动挡。

## 核心命令

### `agentpulse setup` — 交互式配置向导

流程：

```
$ agentpulse setup

🩺 AgentPulse — 模型配置向导

第 1 步：添加模型
━━━━━━━━━━━━━━━━
你想添加哪些模型？我会列出常见提供商供你选择。

  1) DeepSeek       (deepseek-v4-flash, deepseek-v3, ...)
  2) OpenRouter     (任意模型)
  3) 小米 MiMo      (mimo-v2-flash, mimo-v2.5-pro, ...)
  4) GLM / 智谱     (glm-5.1, glm-4, ...)
  5) Kimi / Moonshot (moonshot-v1-128k, ...)
  6) 通义千问       (qwen-max, qwen-plus, ...)
  7) OpenAI         (gpt-4o, gpt-4-turbo, ...)
  8) Anthropic      (claude-sonnet-4, claude-haiku, ...)
  9) 自定义（输入 URL + Key + 模型名）

选择 (逗号分隔): 1,3,9

→ DeepSeek
  API URL [https://api.deepseek.com/v1]: 回车用默认
  API Key: sk-xxxx
  模型列表（我帮你查）:
    ✓ deepseek-v4-flash   (延迟 230ms)
    ✓ deepseek-v3         (延迟 180ms)
    ✗ deepseek-r1         (401 认证失败)
  选择模型: 1,2

→ 小米 MiMo
  API URL [https://api.xiaomi.com/v1]: 回车用默认
  API Key: sk-xxxx
  模型列表（我帮你查）:
    ✓ mimo-v2-flash       (延迟 150ms)
    ✓ mimo-v2.5-pro       (延迟 320ms)
  选择模型: 1,2

→ 自定义
  名称: my-local-ollama
  API URL: http://localhost:11434/v1
  API Key [留空]: 
  模型名称: qwen2.5:7b
  检测中... ✓ (延迟 50ms)

第 2 步：生成 Fallback Chain
━━━━━━━━━━━━━━━━━━━━━━━━━━━
根据检测结果，推荐以下切换顺序：

  主力模型:   deepseek-v4-flash    (快、便宜)
  备用 1:    mimo-v2-flash         (快)
  备用 2:    deepseek-v3           (稳定)
  备用 3:    mimo-v2.5-pro         (强但慢)

  视觉模型:  mimo-v2.5-pro         (唯一支持视觉的)

接受推荐？(Y/n/自定义顺序): Y

第 3 步：写入配置
━━━━━━━━━━━━━━━━
✓ 已写入 ~/.hermes/config.yaml（模型配置）
✓ 已写入 ~/.agentpulse/config.yaml（fallback 规则）
✓ 已备份原配置到 ~/.agentpulse/backup/

配置完成！模型有问题时会自动切换，不用你管。
查看状态: agentpulse status
```

### `agentpulse status` — 查看当前状态

```
$ agentpulse status

🩺 AgentPulse — 模型状态

  模型               状态      延迟    最后检查
  ─────────────────────────────────────────────
  deepseek-v4-flash  ✓ 正常    230ms   10秒前
  mimo-v2-flash      ✓ 正常    150ms   10秒前
  deepseek-v3        ✓ 正常    180ms   10秒前
  mimo-v2.5-pro      ⚠ 限流    320ms   10秒前

  当前主力: deepseek-v4-flash
  Fallback Chain: deepseek → mimo-flash → deepseek-v3 → mimo-pro
  今日切换次数: 2

  最近事件:
  [14:32] deepseek-v4-flash 触发 429，自动切换到 mimo-v2-flash
  [14:35] deepseek-v4-flash 恢复，切回主力
```

### `agentpulse add` — 添加新模型

```
$ agentpulse add

添加新模型到 Fallback Chain

  1) 从已有提供商添加
  2) 添加自定义模型

选择: 1

当前提供商:
  1) DeepSeek (2 个模型)
  2) 小米 MiMo (2 个模型)

选择提供商: 1

可用模型（未添加的）:
  ✓ deepseek-r1         (延迟 450ms)
  ✗ deepseek-coder      (404 不存在)

添加: 1

✓ 已添加 deepseek-r1 到 Fallback Chain
```

### `agentpulse remove` — 移除模型

```
$ agentpulse remove

当前 Fallback Chain:
  1) deepseek-v4-flash (主力)
  2) mimo-v2-flash     (备用 1)
  3) deepseek-v3       (备用 2)
  4) mimo-v2.5-pro     (备用 3)

移除哪个 (编号): 4

✓ 已移除 mimo-v2.5-pro
```

### `agentpulse test` — 测试所有模型

```
$ agentpulse test

测试所有已配置模型...

  deepseek-v4-flash  ✓ 发送成功  响应: "你好！"  延迟: 230ms
  mimo-v2-flash      ✓ 发送成功  响应: "你好！"  延迟: 150ms
  deepseek-v3        ✓ 发送成功  响应: "你好！"  延迟: 180ms
  mimo-v2.5-pro      ⚠ 限流      429 Too Many Requests

全部通过: 3/4
```

## 自动切换机制

AgentPulse 写入配置后，自动切换由 Hermes 原生的 fallback 机制驱动：

1. `agentpulse setup` 生成的配置符合 Hermes config.yaml 的 fallback 格式
2. Hermes 本身就有 provider fallback 支持
3. AgentPulse 的价值是：**让配置过程变得简单，让检测变得自动**

不需要 AgentPulse 守护进程常驻运行。配置完就完事了。

## 项目结构

```
agentpulse/
├── README.md
├── LICENSE
├── pyproject.toml
├── src/
│   └── agentpulse/
│       ├── __init__.py
│       ├── cli.py              # CLI 入口（click）
│       ├── setup_wizard.py     # setup 交互向导
│       ├── model_scanner.py    # 扫描/检测模型
│       ├── config_writer.py    # 写入 Hermes 配置
│       ├── status.py           # status 展示
│       ├── providers/
│       │   ├── __init__.py
│       │   ├── registry.py     # 已知提供商注册表
│       │   ├── deepseek.py     # DeepSeek 适配
│       │   ├── xiaomi.py       # 小米 MiMo 适配
│       │   ├── openai.py       # OpenAI 适配
│       │   ├── anthropic.py    # Anthropic 适配
│       │   ├── zhipu.py        # GLM/智谱 适配
│       │   ├── kimi.py         # Kimi/Moonshot 适配
│       │   ├── qwen.py         # 通义千问 适配
│       │   ├── openrouter.py   # OpenRouter 适配
│       │   └── custom.py       # 自定义提供商
│       └── detector.py         # 模型可用性检测（ping + 发送测试消息）
├── tests/
│   ├── __init__.py
│   ├── test_scanner.py
│   ├── test_config_writer.py
│   └── test_detector.py
└── docs/
    └── spec.md
```

## 技术栈

- **语言：** Python 3.11+
- **CLI：** click（命令行框架）
- **HTTP：** httpx（异步 HTTP 客户端）
- **输出：** rich（终端美化）
- **配置：** pyyaml
- **打包：** pyproject.toml
- **License：** MIT

## 设计原则：不限提供商

AgentPulse 的核心能力是：**任何 OpenAI 兼容 API，填 URL + Key + 模型名就能用。**

预设提供商只是快捷选项（帮你省去查 URL 的麻烦），真正的重点是"自定义"：
- 本地 Ollama：http://localhost:11434/v1
- 私有部署：https://my-api.example.com/v1
- 任何兼容 OpenAI 格式的第三方服务
- 不限数量，想加多少加多少

```python
# 预设 = 快捷选项，不是限制
PROVIDERS = {
    "deepseek": {...},    # 预设
    "xiaomi": {...},      # 预设
    "openrouter": {...},  # 预设
    "openai": {...},      # 预设
    "anthropic": {...},   # 预设
    "zhipu": {...},       # 预设
    "kimi": {...},        # 预设
    "qwen": {...},        # 预设
    # + 无限自定义（用户输入 URL + Key + 模型名）
}
```

## MVP 功能清单

### P0（第一版）
1. ✅ `agentpulse setup` — 交互式配置向导
2. ✅ 模型可用性检测（HTTP ping + 发送测试消息）
3. ✅ 已知提供商注册表（DeepSeek、小米、OpenAI、Anthropic、GLM、Kimi、千问、OpenRouter）
4. ✅ 自定义模型支持（URL + Key + 模型名）
5. ✅ 自动生成 fallback chain 并写入 Hermes config.yaml
6. ✅ `agentpulse status` — 查看当前状态
7. ✅ `agentpulse test` — 测试所有模型

### P1（第二版）
1. `agentpulse add` — 添加新模型
2. `agentpulse remove` — 移除模型
3. 自动检测已有的 Hermes 配置并导入
4. 模型延迟历史记录

### P2（未来）
1. 通道健康检测（飞书/微信/Telegram）
2. 记忆压力检测
3. 成本预算
4. OpenClaw 适配

## 与 Hermes 的关系

AgentPulse 不是替代 Hermes，而是 Hermes 的**配置助手**：

- Hermes 本身有 fallback 机制，但配置门槛高
- AgentPulse 让配置过程傻瓜化
- 配置完成后，切换逻辑由 Hermes 原生驱动
- AgentPulse 不需要常驻运行（除非你想定期 test）
