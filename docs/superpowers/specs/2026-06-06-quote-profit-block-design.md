# 报价输出增加「报价利润评估」区块 — 设计

需求编号：PRD-QUOTE-20260606-001

## Context

`quote.py` 当前的对话输出只有配置摘要 + 3 个文件下载链接。成本/利润数据（逐项 `成本单价/成本小计/利润/利润率` 及 `internal_financials` 汇总）只存在于 `files.json.url` 下载的报价配置 JSON 里，销售/售前每次要下载 JSON 手动翻看才能知道毛利空间，流程冗长。

目标：在对话输出末尾直接展示利润评估区块，省掉下载+翻看 JSON 的点击成本。

**口径前提**（已与需求方确认）：当前报价能力暂未开放给外部用户，全部视为内部场景，利润区块每次报价自动输出、放对话最后。区块标题带「(内部)」字样作护栏；现有 `SKILL.md` 的「对外只展示 `totals.final`、不展示标价/折扣率」硬规则不变，若未来开放对客需剥离此区块。

## 数据来源（已确认）

- `quote.py` 调 API 拿到的 `result` 对象**不含**财务字段（只有 `preview`/`files`/`pricing_version`）。
- 财务数据只在 `files.json.url` 下载的 JSON 里。该短链**公开可读**（无 token 的 curl 即可拉取，已实测），`quote.py` 用 stdlib `urllib`（默认跟 302）即可下载。

JSON 结构（实测样例 `https://quanlaidian-quote-service.iwosai.com/q/NIgxuPXKO3`）：

```jsonc
{
  "报价项目": [
    { "商品名称": "正餐连锁营销旗舰版", "数量": 5,
      "报价小计": 19655, "成本单价": 756, "成本小计": 3780,
      "利润": 15875, "利润率": 81, "子项": [...] }
  ],
  "internal_financials": {
    "quote_total": 19655, "cost_total": 3780,
    "profit_total": 15875, "profit_rate": 81
  }
}
```

## 设计

### quote.py 新增两个函数（职责分离，便于离线测试）

- `fetch_financials(json_url) -> dict | None`
  下载 + `json.loads`。任何失败（网络/超时/解析/非 200）返回 `None`，**不抛异常**。
- `render_profit(data) -> str`
  **纯函数**，输入解析好的 JSON dict，输出区块 Markdown 文本。无网络依赖，可离线单测。缺 `internal_financials` 时返回空串。

### render() 串联

`render()` 打完 3 个下载链接后：取 `result["files"]["json"]["url"]` → `fetch_financials` → 若拿到 dict 则 `render_profit` 打印；拿到 `None` 或空串则**静默跳过**，不崩、不阻塞已输出的主报价（同 PDF 区块的降级思路）。

### 输出格式

```
## 报价利润评估（内部）

- 报价总额：¥19,655    成本总额：¥3,780
- 利润总额：¥15,875    利润率：81%

| 项目 | 数量 | 报价小计 | 成本小计 | 利润 | 利润率 |
|------|------|---------|---------|------|--------|
| 正餐连锁营销旗舰版 | 5 | ¥19,655 | ¥3,780 | ¥15,875 | 81% |
```

- 金额用千分位（沿用现有 `f"¥{n:,}"`）；`利润率` 为整数 → `81%`。
- 逐项表遍历 `报价项目[]` 全部条目（总部/增值模块各占一行）。

## 测试（离线）

- 新增 `tests/fixtures/quote_config_sample.json`（即上方实测样例，脱敏数字无所谓）。
- 新增 `tests/test_render_profit.py`：加载 fixture → `render_profit` → 断言
  汇总四项金额（含千分位）、利润率 `81%`、表头与商品行存在。
- 既有 `tests/test_render.py` 不动：其用假 URL，`fetch_financials` 必失败返回 `None`，区块跳过，`render()` 不崩，原断言仍通过。
- 验证命令：`python3 -m unittest discover tests -v`（改 SKILL.md/tests 触发 PostToolUse 钩子自动跑离线套件）。

## 改动文件

- `scripts/quote.py`（主）
- `tests/fixtures/quote_config_sample.json`、`tests/test_render_profit.py`（新增）
- `SKILL.md`：「OpenClaw 对话输出规范」加第 4 节说明（内部利润评估区块，自动输出、对客需剥离）

## 提交

- `feat:` 前缀（新增对话输出能力）。不动 VERSION/manifest。
