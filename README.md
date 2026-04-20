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

设置以下环境变量（两个都是**必填**，脚本在运行时会校验）：

| 变量 | 必填 | 说明 |
|---|---|---|
| `QUOTE_API_URL` | ✅ | 报价服务 base URL，由运维/部署侧注入。**不在代码里硬编码**。UAT 期间通常为 `http://118.145.233.116:443`（纯 HTTP，IP 直连）；未来切到 `https://api.quanlaidian.com` 这类带 TLS 的正式域名时，只需改 env 变量无需改代码。兼容旧配置 `…/v1/quote`、`…/v1/quotes`，会自动去掉后缀。 |
| `QUOTE_API_TOKEN` | ✅ | API 认证令牌（向管理员申请，每个组织一个） |

**典型设置（UAT）：**

```bash
export QUOTE_API_URL=http://118.145.233.116:443
export QUOTE_API_TOKEN=<向管理员申请的 token>

# 连通性自检
curl -s "$QUOTE_API_URL/healthz"
# → {"status":"ok","pricing_version":"small-segment-v2.3"}
```

任一变量未设置，脚本会退出并打印 `配置缺失：环境变量 … 未设置`。

---

## 使用

准备一份符合 `references/openclaw_form_schema.json` 的表单 JSON，然后：

```bash
python3 scripts/quote.py --form <表单JSON路径>
```

OpenClaw 在用户提交表单时会自动调用此脚本。默认走 v2 资源流（`POST /v1/quotes` → 持久化 → 按需 render pdf/xlsx/json）。

```bash
# 过渡期可选：走老的一次性接口 /v1/quote（触发审批时会 409）
python3 scripts/quote.py --legacy --form <表单JSON路径>
```

### 输出

**A. 正常生成** — 配置摘要 + 三个下载链接 + 报价 ID：

```markdown
## 本次配置摘要

- 品牌：示例品牌
- 餐饮类型：正餐    门店数：10
- 套餐：旗舰版    折扣：0.85
- 总价：¥408,000（标价 ¥480,000）

## 下载文件

- [报价单 PDF](https://api.quanlaidian.com/files/.../示例品牌-全来店-报价单-20260420.pdf)
- [报价单 Excel](https://api.quanlaidian.com/files/.../示例品牌-全来店-报价单-20260420.xlsx)
- [报价配置 JSON](https://api.quanlaidian.com/files/.../示例品牌-全来店-报价配置-20260420.json)

_报价 ID：q_20260420_xxxxxxxx　报价版本：small-segment-v2.3_
```

文件链接 **有效期 7 天**，请指导客户及时下载。过期后可用同一 `报价 ID` 调用服务端 `POST /v1/quotes/{id}/render/{format}?force=1` 重新生成。

**B. 触发审批** — 配置摘要 + 待审批说明（不会展示 PDF/Excel/JSON 链接）：

```markdown
## 待审批

- 报价 ID：`q_20260420_xxxxxxxx`
- 审批状态：pending
- 触发原因：
  - final_factor_below_base_minus_0.01:manager_approval
  - manual_override_without_sufficient_history

配置已保存，暂不生成 PDF/Excel/JSON。请联系主管在 OpenClaw 内审批通过后，用同一个报价 ID 重新下发。
```

审批通过由主管在 OpenClaw 内完成，销售仅需把 `报价 ID` 和触发原因转给主管即可。

### 退出码与错误

| 场景 | 行为 |
|---|---|
| 成功 / 待审批 | 退出码 0，Markdown 输出到 stdout |
| `QUOTE_API_URL` 或 `QUOTE_API_TOKEN` 未配置 | 退出码 1，错误信息到 stderr |
| 服务端返回非 2xx（含 legacy 的 409 APPROVAL_PENDING） | 退出码 1，打印 `服务端错误 <HTTP状态码>：<响应体>` |
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
