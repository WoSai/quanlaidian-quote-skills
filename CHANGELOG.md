# Changelog

## 1.2.0 (2026-04-23)

- [#3] SKILL.md 新增"行业关键字 → 餐饮类型软推荐"：按奶茶/火锅等关键字主动建议轻餐或正餐，用户一键确认即可；歧义行业（茶餐厅、日料、西餐、小笼包、融合菜、烧烤）显式追问，不做自动判定
- [#3] `references/sales_guide.md` 同步说明软推荐机制；`references/openclaw_form_schema.json` 餐饮类型 help_text 增加提示
- [#4] `references/product_catalog.md` 每个 SKU 新增『套餐说明』小节（QC-01~05 / ZC-01~05），内容来自 `盼盼食品-全来店报价单V2.xlsx` K 列；成本管理 / 配送中心 / 生产加工 模块说明列扩充为 xlsx 完整原文
- [#4] `references/product_catalog.md` 新增 `## 三、权益类` 章节：小程序手机验证次数充值、外卖接单费用标准文案（单一权威来源）
- [#4] 新增 `docs/backend_template_requirements.md`：面向 `quanlaidian-quote-service` 的模板需求说明，包含三-logo 抬头、主表列结构、K 列『套餐说明』数据源、权益类页脚与阶梯列动态规则
- 新增 `scripts/update_notice.py`：节点被 `check_openclaw_update.py` 拉取到新版本后，下次 skill 激活时（SKILL.md 工作流 step 1）自动在回复首段插入一段升级提示（从 `CHANGELOG.md` 对应版本条目抽取），每个版本对同一用户**只提示一次**，之后自沉默。状态文件存 `~/.cache/quanlaidian-quote-skills/last_notified_version`，不进 git

## 1.1.1 (2026-04-22)

- 门店数量范围 1–30 → **1–300**；31–300 段服务端自动走锚点 + 阶梯对比报价，301+ 转人工
- 对外渲染去掉"标价"和"折扣率"两列，只展示最终成交价；客户报价单不暴露底价
- SKILL.md 新增硬约束：**禁止任何形式的折扣率外推、推演、估算**，所有价格只从 API 响应透传
- SKILL.md 新增"大客户段（31–300 店）处理规则"和"多档主动对比"两节，覆盖 50/100/200 等锚点多次调用场景
- `scripts/quote.py` 读到 `pricing_info.algorithm_version=large-segment-v1` 时追加两档提示；老响应兼容（防御式跳过）

## 1.1.0 (2026-04-22)

- 新增节点每日自动更新机制：`scripts/check_openclaw_update.py` 比对本地 `VERSION` 与 `main` 分支 raw `VERSION`，有新版本时 `git pull --ff-only`
- 新增 `scripts/install_cron.sh`：幂等地把每日 01:00 自更新 cron 行写入当前用户 crontab
- README 增加"自动更新"章节（中英文）
- 借鉴归档仓库 `quanlaidian-quotation-skill` 的节点自检方案

## 1.0.0 (2026-04-18)

### Breaking Changes
- **架构重构**：报价逻辑、文件生成、价格基线全部迁移到服务端
- 客户端仅保留 ~60 行薄客户端 `scripts/quote.py`，零 Python 依赖
- 删除所有飞书相关脚本（v1 不再支持原生飞书文件推送）
- 删除 `requirements.txt`（不再需要外部依赖）
- 新增环境变量：`QUOTE_API_TOKEN`（必填）、`QUOTE_API_URL`（可选）

## 0.1.10 - 2026-04-15

- 自动版本更新：main 分支有新提交

## 0.1.9 - 2026-04-14

- 自动版本更新：main 分支有新提交

## 0.1.8 - 2026-04-14

- 自动版本更新：main 分支有新提交

## 0.1.7 - 2026-04-14

- 自动版本更新：main 分支有新提交

## 0.1.6 - 2026-04-13

- 自动版本更新：main 分支有新提交

## 0.1.5 - 2026-04-13

- 自动版本更新：main 分支有新提交

## 0.1.4 - 2026-04-13

- 自动版本更新：main 分支有新提交

## 0.1.3 - 2026-04-13

- 自动版本更新：main 分支有新提交

## 0.1.2 - 2026-04-13

- 新增供应链实施费计算逻辑（实现费算法更新）
- 发布流程补齐版本号，确保 OpenClaw 自动更新可正确识别新版本

## 0.1.0 - 2026-04-10

- 初始化全来店报价技能仓库
- 增加 OpenClaw 对话输出规范（预览 + 下载链接）
- 增加自动化更新机制（Release 通知 + 节点自检脚本）
