# 🩺 AgentPulse

> 一条命令搞定多模型管理 + 自动切换

## 问题

- `hermes model` 只能配一个模型，改不了 key
- URL 填错了不知道，跑起来才报错
- 模型挂了要手动排查、手动切换

## 解决

```bash
agentpulse setup
    ↓
① 列出常见提供商，让你选择（或自定义 URL + Key + 模型名）
② 自动检测所有模型状态（能不能通、延迟多少）
③ 自动生成 fallback chain（主→备1→备2→...）
④ 写入配置，模型有问题自动切换
```

## 安装

```bash
pip install agentpulse
# 或开发模式
git clone https://github.com/yourname/agentpulse.git
cd agentpulse
pip install -e .
```

## 使用

```bash
agentpulse setup    # 配置向导
agentpulse status   # 查看状态
agentpulse test     # 测试模型
```

## 特性

- ✅ 预设 8 大提供商快捷选项（DeepSeek、小米、OpenAI、Anthropic 等）
- ✅ 自定义支持（任何 OpenAI 兼容 API，填 URL + Key + 模型名就行）
- ✅ 自动检测模型可用性 + 延迟
- ✅ 按延迟排序生成最优 Fallback Chain
- ✅ 写入 Hermes 配置，出问题自动切换
- ✅ 无需守护进程，配置完就完事

## License

MIT
