# 全来店报价 — OpenClaw Skill

> [English version →](README.en.md)

> **销售 / 售前用户看这里：** [在飞书里用 OpenClaw 机器人出报价](docs/飞书使用指南.md)

一个用于 OpenClaw 的技能包：接收一份报价表单 JSON，调用后端 [quanlaidian-quote-service](https://github.com/jasonshao/quanlaidian-quote-service)，回写报价预览和 PDF / Excel / JSON 配置文件的下载链接。

**版本：** 1.0.0　**依赖：** 仅 Python 3 标准库

---

## 安装

```bash
git clone https://github.com/jasonshao/quanlaidian-quote-skills.git
```

零额外依赖，克隆后即可使用。

---

## 配置

设置以下环境变量：

| 变量 | 必填 | 说明 |
|---|---|---|
| `QUOTE_API_TOKEN` | ✅ | API 认证令牌（向管理员申请，每个组织一个） |
| `QUOTE_API_URL` | ❌ | 报价服务地址，默认 `https://api.quanlaidian.com/v1/quote` |

---

## 使用

准备一份符合 `references/openclaw_form_schema.json` 的表单 JSON，然后：

```bash
python3 scripts/quote.py --form <表单JSON路径>
```

OpenClaw 在用户提交表单时会自动调用此脚本。

### 输出

脚本直接向 stdout 打印 Markdown：

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

文件链接 **有效期 7 天**，请指导客户及时下载。

### 退出码与错误

| 场景 | 行为 |
|---|---|
| 成功 | 退出码 0，Markdown 输出到 stdout |
| `QUOTE_API_TOKEN` 未配置 | 退出码 1，错误信息到 stderr |
| 服务端返回非 2xx | 退出码 1，打印 `服务端错误 <HTTP状态码>：<响应体>` |
| 网络异常 | 退出码 1，打印 `网络异常：<原因>` |

---

## 表单字段

所有输入字段定义在：
- **`references/openclaw_form_schema.json`** — JSON Schema 定义
- **`references/openclaw_form_config.json`** — OpenClaw 表单配置
- **`references/openclaw_form_submission.example.json`** — 示例提交

核心字段：

| 字段 | 类型 | 必填 | 约束 |
|---|---|---|---|
| `客户品牌名称` | string | ✅ | |
| `餐饮类型` | string | ✅ | `"轻餐"` 或 `"正餐"` |
| `门店数量` | integer | ✅ | 1 – 30 |
| `门店套餐` | string | ✅ | 如 `"旗舰版"` |
| `门店增值模块` | string[] | ❌ | |
| `总部模块` | string[] | ❌ | |
| `配送中心数量` | integer | ❌ | ≥ 0 |
| `生产加工中心数量` | integer | ❌ | ≥ 0 |
| `成交价系数` | float | ❌ | 0.01 – 1.0；**显式提供时 `人工改价原因` 必填** |
| `人工改价原因` | string | ❌ | 显式提供 `成交价系数` 时必填，用于审计留痕 |
| `是否启用阶梯报价` | boolean | ❌ | |
| `实施服务类型` | string | ❌ | |
| `实施服务人天` | integer | ❌ | ≥ 0 |

完整的 API 请求/响应结构见 [quanlaidian-quote-service README](https://github.com/jasonshao/quanlaidian-quote-service)。

---

## 代码结构

```
quanlaidian-quotation-skill/
├── README.md / README.en.md              # 中文 / 英文说明
├── SKILL.md                              # OpenClaw 技能元数据与触发规则
├── VERSION                               # 1.0.0
├── CHANGELOG.md
├── LICENSE
├── scripts/
│   └── quote.py                          # 45 行客户端 — 零额外依赖
└── references/
    ├── openclaw_form_schema.json         # 表单 JSON Schema
    ├── openclaw_form_config.json         # OpenClaw 表单控件配置
    ├── openclaw_form_submission.example.json  # 示例提交
    ├── product_catalog.md                # 产品目录（供销售参考）
    └── sales_guide.md                    # 销售话术与使用场景
```
