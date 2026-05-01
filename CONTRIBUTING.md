# 贡献指南

感谢你对 AgentPulse 的兴趣！

## 开发环境

```bash
git clone https://github.com/SeinoShukuno/agentpulse.git
cd agentpulse
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## 运行测试

```bash
pytest tests/ -v
```

## 提交规范

使用约定式提交格式：

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
refactor: 重构
test: 测试
chore: 构建/工具
```

示例：
```
feat: 添加 Ollama 提供商预设
fix: 修复小米模型名大小写问题
docs: 补充 README 使用示例
```

## 如何贡献

### 添加新提供商

1. 编辑 `src/agentpulse/providers/registry.py`
2. 在 `PROVIDERS` 字典中添加新条目
3. 确保 `urls`、`default_models`、`key_env` 正确
4. 运行测试确认没有破坏已有功能
5. 提交 PR

### 修复 Bug

1. 先开 Issue 描述问题
2. 写一个能复现问题的测试
3. 修复代码
4. 确保所有测试通过
5. 提交 PR

### 改进文档

直接提交 PR 即可，文档改进不需要测试。

## 项目结构

```
src/agentpulse/
├── cli.py              # CLI 入口（click）
├── setup_wizard.py     # 交互式配置向导
├── detector.py         # 模型可用性检测
├── config_writer.py    # Hermes 配置写入
├── status.py           # 状态展示
└── providers/
    └── registry.py     # 提供商注册表
```

详见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

## Code of Conduct

请保持友善和尊重。我们都是来解决问题的。

## License

贡献的代码将在 [MIT License](LICENSE) 下发布。
