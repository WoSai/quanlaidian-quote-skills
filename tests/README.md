# Prompt-validation tests

轻量级 prompt 校验测试套件 —— 用真实 Claude API 跑一遍 `SKILL.md` + 模拟用户输入，
断言 LLM 产生的 `feishu_ask_user_question` / `Bash` tool 调用结构是否符合预期。

覆盖 PR #24 中修复的 5 个回归（来自「胡子大厨湘菜」真实会话）：

| Case | 断言 |
|---|---|
| A. 湘菜 → 一级正餐 | 不发"轻餐/正餐"卡片；quote.py 调用含 `餐饮类型=正餐` |
| B. 无总部模块互斥 | 同勾「无」+「配送中心」时取「无」，quote.py form 不含 `配送中心` |
| C. 卡片不含价格 | 所有选项 description 不含 `元`、`%`、`/年`、`/店` 等 token |
| D. 不二次追问门店数 | 卡片 1 后续卡片 question 不含「准确门店数」等措辞 |
| E. 卡片 2 含「无门店增值模块」 | 增值模块多选选项有「无门店增值模块」 |

## 本地运行

```bash
pip install -r requirements-test.txt
export ANTHROPIC_API_KEY=sk-ant-...
pytest tests/ -v
```

如果 `ANTHROPIC_API_KEY` 没设置，测试会被 skip（不会失败）。

## 配置

通过环境变量调整测试参数：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `SKILL_TEST_MODEL` | `claude-opus-4-7` | 用哪个模型跑测试。降级到 `claude-haiku-4-5` 可省钱（约 1/5 成本），但断言可能更脆 |
| `SKILL_TEST_EFFORT` | `low` | `output_config.effort` 值。测试只是检查 tool call 结构，不需要深度推理 |
| `SKILL_TEST_MAX_TURNS` | `4` | 单 scenario 最多跑几轮 LLM 交互 |

省钱跑法：

```bash
SKILL_TEST_MODEL=claude-haiku-4-5 pytest tests/ -v
```

## 工作原理

每个 scenario：

1. 加载 `SKILL.md` + `references/*.md` 作为系统提示（带 prompt caching）
2. 定义两个 mock tool：`feishu_ask_user_question` + `Bash`（schema 跟真实 OpenClaw 接近）
3. 发送用户消息给 Claude
4. 当 LLM 调用 `feishu_ask_user_question` 时，返回 scenario 预设的 canned response（模拟用户提交）
5. 当 LLM 调用 `Bash` 时，返回 canned quote.py 输出并终止
6. 把所有 tool call signature（卡片选项、bash 命令）喂给 scenario 的断言函数

这不是端到端测试 —— 真实的 OpenClaw 飞书运行时跑的是 Claude Code SDK，工具集和编排细节不同。
这套测试只验证 **prompt 指令本身能否引导 LLM 产生正确的 tool call 形态**，足够拦截 SKILL.md /
references 的文案漂移。

## 成本

单次完整运行（5 个 scenario × 平均 ~2 轮 LLM 调用，含 prompt caching）：

| 模型 | 估算成本 |
|---|---|
| `claude-opus-4-7` | ~$0.30–$0.60 |
| `claude-sonnet-4-6` | ~$0.10–$0.20 |
| `claude-haiku-4-5` | ~$0.05–$0.10 |

CI 仅在 `SKILL.md` / `references/` 变化时触发（见 `.github/workflows/skill-prompt-tests.yml`），
普通 PR 不会消耗额度。

## CI 设置

需要在 repo Settings → Secrets and variables → Actions 加一个 secret：

- Name: `ANTHROPIC_API_KEY`
- Value: 你的 Anthropic API key

只有有写权限的 repo admin 能改这个 secret，PR 来的 fork 拉到的 workflow run 看不到值
（GitHub Actions 默认安全策略）。

## 维护

新增 SKILL.md 行为约束时，建议同步加一个 scenario（最起码加一个回归 case）。模板：

```python
def test_new_behavior(client, system_prompt):
    captured = run_scenario(
        client, system_prompt,
        user_message="<用户输入>",
        canned_feishu_response={"submitted": True, "answers": {...}},
    )
    # 检查 captured.feishu_calls / captured.bash_calls / captured.text_blocks
    assert ...
```

LLM 是非确定性的，断言要写得**结构化、宽容**：检查关键字段的存在 / 缺失，而非精确字符串
匹配。出现 flake 时优先放宽断言，而不是引入重试。
