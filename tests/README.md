# 全来店报价 · 回归测试套件

11 个真实场景的 API 回归测试 + SKILL.md 三条业务规则的 payload 修正单测。零外部依赖（Python ≥ 3.10 标准库），可离线运行；可选 `--live` 模式打 beta API 验真实价格。

## 怎么跑

```bash
# 离线（默认）：跑规则单测 + payload 修正断言，不打网络
python3 -m unittest discover tests -v

# Live：打 beta API 验 final_price 与 4xx 拒绝行为
QUOTE_TEST_LIVE=1 \
QUOTE_API_URL=https://<beta-host>/v1/quote \
QUOTE_API_TOKEN=<token> \
python3 -m unittest discover tests -v
```

## 文件布局

```
tests/
├── rules.py                    SKILL.md 三条 payload 修正规则的纯函数实现
├── test_business_rules.py      rules.py 的 19 个单测
├── test_scenarios.py           动态注入 11 个场景测试的 runner
└── scenarios/
    ├── 01_manner_coffee_5.json … 08_xiaofandian_1.json     一次性通过：单文件 fixture
    └── 09_luckin_120/ 10_laoxiangji_200/ 11_xiaolongkan_300/  翻车：目录形式，含 initial.json / corrected.json / violation.md
```

## 11 个场景速览

| # | 品牌 | 餐饮类型 | 门店数 | 套餐 | 增值/总部模块 | final_price | 触发规则 |
| - | --- | --- | --- | --- | --- | ---: | --- |
| ① | Manner Coffee | 轻餐 | 5 | 营销基础版 | KDS | ¥9,310 | — |
| ② | 一点点 | 轻餐 | 20 | 营销旗舰版 | KDS+发票+成本 | ¥52,031 | — |
| ③ | 好利来 | 轻餐 | 50 | 营销全能版 | 门店点位+KDS+发票 / 配送×2+加工×1 | ¥108,851 | — |
| ④ | 巴比馒头 | 轻餐 | 15 | 标准版 | 无 | ¥14,700 | — |
| ⑤ | 胡子大厨 | 正餐 | 8 | 营销旗舰版 | KDS+发票 | ¥35,867 | — |
| ⑥ | 海底捞 | 正餐 | 30 | 营销全能版 | KDS+分账+发票 | ¥95,621 | — |
| ⑦ | 王品台塑 | 正餐 | 3 | 营销旗舰版 | 宴秘书+晓食菜单+发票 | ¥63,758 | — |
| ⑧ | 楼下小饭店 | 正餐 | 1 | 标准版 | 无 | ¥2,673 | — |
| ⑨ | 瑞幸咖啡 | 轻餐 | 120→100 | 供应链版 → 全能版 | + 配送×2+加工×1 | ¥214,876 | ①② |
| ⑩ | 老乡鸡 | 正餐 | 200→200 | 全能版 | + 配送×5（追加门店点位） | ¥671,926 | ② |
| ⑪ | 小龙坎 | 正餐 | 300→200 | 旗舰版 → 全能版 | + 配送×5 | ¥673,701 | ①② |

## 三条业务规则（SKILL.md 第 122–129、177–182 行）

⑨⑩⑪ 三个翻车用例对应的契约，已在 `rules.py` 中以纯函数复刻：

1. **旗舰版/供应链版 + 配送中心/生产加工 → 全能版**  
   旗舰版与供应链版含『单门店库存』，与总部供应链路线互斥；自动改用全能版（`轻餐连锁营销全能版` / `正餐连锁营销全能版`）。

2. **配送中心/生产加工 → 必须含「供应链基础-门店点位」**  
   门店端需要『供应链基础-门店点位』承接收货，否则 service 端 400。

3. **「无总部模块/无门店增值模块」+ 其他勾选 → 以「无」为准**  
   sentinel 优先，清空其他项；摘要里显式提示。

## fixture 字段约定

```jsonc
{
  "id": "01",
  "name": "...",
  "tags": [...],
  "notes": "...",
  "payload": { /* 8 字段，对齐 references/openclaw_form_submission.example.json */ },
  "expected": {
    "final_price": 9310,            // 历史 beta 报价
    "segment": "small",             // small (1-30) / large (31-300)
    "effective_store_count": 5,     // 大客户段为锚点值，小客户段 == 输入值
    "price_baseline_only": false    // true 表示 --live 不强校验价格，只验 200（仅翻车场景用）
  }
}
```

## --live 模式做什么

- 单文件 fixture：调 API，断言 `final_price == expected.final_price`（除非 `price_baseline_only`）。
- 翻车目录：调 API 两遍——`corrected.payload` 期望 200，`initial.payload` 期望 4xx（验证后端规则兜底仍生效）。
- token 未设直接 `unittest.skip`，不会因为环境缺配置 CI 红。

## 加新场景

1. 小客户段（≤30 店）/ 大客户段无总部模块 → 在 `scenarios/` 加单文件 `NN_brand_stores.json`。
2. 翻车场景 → 加目录 `scenarios/NN_brand_stores/`，三件套 `initial.json` + `corrected.json` + `violation.md`。

测试 runner 自动 discover，无需改代码。

## 边界与已知问题

- **价格漂移**：beta API 调价时所有 `final_price` 都会失效；--live 失败后需要手动核对新价并更新 fixture。这是预期行为，不是 bug。
- **300 店 effective=200**：⑪ 售前实测 300 → 200 锚点。SKILL.md 第 199 行写的『50/100/200/300』中 300 锚点在 beta 当时未独立报价，按下锚点规则 fallback 到 200。若后端补齐 300 锚点，更新 ⑪ 的 `effective_store_count` 即可。
- **翻车 fixture 的总部数量是合理还原**：售前报告只给了总价没给配送/加工中心数量，本套件按 SKILL.md 决策树给出合理猜测，并把 `price_baseline_only: true` 标在 expected 里。--live 在此场景只验响应 200，不严格校验金额。
