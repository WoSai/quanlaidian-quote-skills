# Quanlaidian Quote — OpenClaw Skill

> [中文版 →](README.md)

> **For sales & pre-sales:** [Using this skill via the OpenClaw bot in Feishu (zh)](docs/飞书使用指南.md)

An OpenClaw skill: takes a quotation form JSON, calls the backend [quanlaidian-quote-service](https://github.com/jasonshao/quanlaidian-quote-service), and returns a quotation summary with download links for PDF / Excel / JSON config files.

**Version:** 1.0.0　**Dependencies:** Python 3 standard library only

---

## Install

```bash
git clone https://github.com/jasonshao/quanlaidian-quote-skills.git
```

Zero extra dependencies — works immediately after cloning.

---

## Configure

Set these environment variables:

| Variable | Required | Description |
|---|---|---|
| `QUOTE_API_TOKEN` | ✅ | API token (one per organisation, issued by the service admin) |
| `QUOTE_API_URL` | ❌ | Quote service endpoint, default `https://api.quanlaidian.com/v1/quote` |

---

## Usage

Prepare a form JSON matching `references/openclaw_form_schema.json`, then:

```bash
python3 scripts/quote.py --form <path-to-form.json>
```

OpenClaw automatically invokes this script when the user submits the form.

### Output

The script writes Markdown directly to stdout:

```markdown
## 本次配置摘要

- 品牌：示例品牌
- 餐饮类型：正餐    门店数：10
- 套餐：旗舰版    折扣：0.85
- 总价：¥408,000（标价 ¥480,000）

## 下载文件

- [报价单 PDF](https://api.quanlaidian.com/files/.../示例品牌-全来店-报价单-20260419.pdf)
- [报价单 Excel](https://api.quanlaidian.com/files/.../示例品牌-全来店-报价单-20260419.xlsx)
- [报价配置 JSON](https://api.quanlaidian.com/files/.../示例品牌-全来店-报价配置-20260419.json)

_报价版本：small-segment-v2.3_
```

File URLs expire after **7 days** — instruct the customer to download promptly.

### Exit Codes & Errors

| Scenario | Behaviour |
|---|---|
| Success | Exit 0, Markdown on stdout |
| `QUOTE_API_TOKEN` not set | Exit 1, error on stderr |
| Server returns non-2xx | Exit 1, prints `服务端错误 <HTTP code>：<body>` |
| Network error | Exit 1, prints `网络异常：<reason>` |

---

## Form Fields

All input fields are defined in:
- **`references/openclaw_form_schema.json`** — JSON Schema definition
- **`references/openclaw_form_config.json`** — OpenClaw form control config
- **`references/openclaw_form_submission.example.json`** — example submission

Core fields:

| Field | Type | Required | Constraint |
|---|---|---|---|
| `客户品牌名称` | string | ✅ | Customer brand name |
| `餐饮类型` | string | ✅ | `"轻餐"` or `"正餐"` |
| `门店数量` | integer | ✅ | 1 – 30 |
| `门店套餐` | string | ✅ | e.g. `"旗舰版"` |
| `门店增值模块` | string[] | ❌ | |
| `总部模块` | string[] | ❌ | |
| `配送中心数量` | integer | ❌ | ≥ 0 |
| `生产加工中心数量` | integer | ❌ | ≥ 0 |
| `成交价系数` | float | ❌ | 0.01 – 1.0 |
| `人工改价原因` | string | ⚠️ | Required when `成交价系数` is provided |
| `是否启用阶梯报价` | boolean | ❌ | |
| `实施服务类型` | string | ❌ | |
| `实施服务人天` | integer | ❌ | ≥ 0 |

Full API request/response schema lives in the [quanlaidian-quote-service README](https://github.com/jasonshao/quanlaidian-quote-service).

---

## Repository Layout

```
quanlaidian-quotation-skill/
├── README.md / README.en.md              # Chinese / English
├── SKILL.md                              # OpenClaw skill metadata and triggers
├── VERSION                               # 1.0.0
├── CHANGELOG.md
├── LICENSE
├── scripts/
│   └── quote.py                          # 45-line client — zero extra deps
└── references/
    ├── openclaw_form_schema.json         # Form JSON Schema
    ├── openclaw_form_config.json         # OpenClaw form control config
    ├── openclaw_form_submission.example.json  # Example submission
    ├── product_catalog.md                # Product catalogue (sales reference)
    └── sales_guide.md                    # Sales talking points and use cases
```
