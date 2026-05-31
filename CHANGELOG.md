# Changelog

## 1.6.0 (2026-05-31)

- `SKILL.md` 大幅精简去重 + 决策逻辑结构化（#36 及第二轮）：套餐默认决策树 / 全通判定 / 大客户段锚点等"脊柱规则"改为伪代码 / 布尔门 / 区间查表；⭐推荐机制、套餐决策树、配置摘要、门店数精确数字等散落 5–7 处的重复表述收敛为单一权威小节 + 指针；合并『强制 API 调用』与『其他约束』、删除引导式对话兜底「路径对照」冗余表、压缩触发场景与输出小节；结构化块加"执行态以 `tests/rules.py` 为准"脚注，`tests/` 中失效的 SKILL.md 行号引用改为稳定小节名
- 报价文件下载链接逐字符原样透传（#29）：`scripts/quote.py` 渲染改为整段原样输出、不再用 Markdown 包裹；`SKILL.md` 新增"链接含 OSS 签名必须逐字符复制、禁止改写"硬规则防 `SignatureDoesNotMatch`；新增 `tests/test_render.py` 回归
- 表单「无…模块」哨兵项声明式互斥（#30）：schema 用 `none_option.exclusive` 声明，渲染层点击即清空其他勾选、勾其他即取消「无…」
- 飞书卡片流程细化（#31–#35）：顺序卡兜底卡片 2 去价格、门店套餐由决策树自动判定、总部/增值模块首项加「无…」互斥标记；门店数采集改为精确数字输入并移除档位单选（锚点折算交由 API）；推荐方案确认卡门店套餐不作为可改项；新增"全通只凭首条消息判一次（防折返跑）""进了顺序卡兜底就走到底""文本在前、卡片在后每轮至多一句过渡"等约束
- 工程：新增 11 场景回归测试套件（#25）；新增 `CLAUDE.md` 编程原则与项目须知（#26 / #27）
- 文档版本号整体对齐：`VERSION` / `CHANGELOG.md` / `README.md` / `README.en.md` / `.release-please-manifest.json` 同步到 `1.6.0`

## 1.5.0 (2026-05-22)

- 飞书卡片采集流程修复（来自一次"做个胡子大厨湘菜的报价单"真实会话回归暴露的 5 个问题）：
  - `references/dining_type_keywords.md` 一级正餐关键词补齐八大菜系 + 常见变体：新增 `湘菜` / `湘菜馆` / `湖南菜` / `苏菜` / `江苏菜` / `淮扬菜` / `浙菜` / `闽菜` / `徽菜` / `鲁菜` 等，原有 `粤菜馆` / `川菜馆` 补不带"馆"形式；湘菜等已明确属于正餐的关键词不再走三级歧义追问
  - `SKILL.md` 顺序卡兜底 · 卡片 2：门店增值模块新增「无门店增值模块」作为首项，让"不要增值模块"成为显式表态；`references/module_candidates.md` 同步在轻餐 / 正餐候选清单顶部列出
  - `SKILL.md` 卡片答案 → API 字段修正映射表新增两条互斥校验：同时勾「无总部模块」/「无门店增值模块」+ 其他项时，以「无」为准、清空其他勾选并在摘要标注
  - `SKILL.md` 卡片设计规则新增"禁止在卡片选项 description 写具体金额 / 折扣率"硬规则：价格统一由 API 返回后在最终配置摘要中展示
  - `SKILL.md` 卡片设计规则新增"门店数字段经卡片采集后不再二次追问"硬规则；映射表删除"如需精确可追问一句"表述，明确 31–300 店段精确度差异由 API 按 50 / 100 / 200 / 300 锚点处理
- 文档版本号整体对齐：`VERSION` / `CHANGELOG.md` / `README.md` / `README.en.md` 同步到 `1.5.0`

## 1.4.0 (2026-05-12)

- 下线人工改价能力：删除 `成交价系数` / `人工改价原因` 字段及相关 schema、配置、提交示例、卡片问题、对话步骤、FAQ 文案；价格统一由服务端按门店数推荐折扣，用户要求改价时引导走线下特批
- 下线阶梯报价开关：删除 `是否启用阶梯报价` 字段及 ≤30 店段的卡片问题；多档对比改为用户主动发起的 `quote.py` 多次调用，所有相关文档同步更新
- `SKILL.md`：卡片 3 收敛为「配套数量」单一用途；引导式对话步骤由 9 步缩减为 8 步；约束节新增两条硬规则
- `references/openclaw_form_schema.json` / `openclaw_form_config.json` / `openclaw_form_submission.example.json`：清理对应字段与 `pricing` 分组
- `README.md` / `README.en.md` / `docs/飞书使用指南.md`：字段表、FAQ、对话示例、进阶用法同步收敛

## 1.3.0 (2026-05-12)

- 移除全部「实施服务」相关字段与文案，与后端能力对齐：
  - `references/openclaw_form_schema.json` / `openclaw_form_config.json` 删除 `实施服务类型` / `实施服务人天` 字段及 `implementation` 分组
  - `references/openclaw_form_submission.example.json` 删除示例字段
  - `references/product_catalog.md` 删除『实施服务人天测算口径』小节
  - `SKILL.md` 核心字段、卡片 2 选项、引导式对话步骤、配置摘要展示项均移除实施服务相关描述
  - `README.md` / `README.en.md` 字段表删除实施服务两行
  - `references/sales_guide.md`、`docs/飞书使用指南.md`、`docs/backend_template_requirements.md` 同步删除引用

## 1.2.1 (2026-05-06)

- [#14] SKILL.md 约束节顶部新增「强制 API 调用」最高优先级小节：明确报价文件唯一来源是 `scripts/quote.py`，禁止本地拼装 / 伪生成 / 失败回退本地估算；API 返回业务冲突时优先按 SKILL 决策树自动改写参数后**重新调用 API**，仅在决策树无法消歧时再向用户追问
- [#15] SKILL.md 瘦身 261 → 193 行（-26%）：把行业关键字映射、模块候选短列表等纯静态查表数据下沉到 `references/`，让入口文档专注于触发判定 + 工作流程 + 行为约束
- [#15] 新增 `references/dining_type_keywords.md`：行业关键字 → 餐饮类型软推荐映射 + 对话模板 + 规则
- [#15] 新增 `references/module_candidates.md`：对话场景下的门店增值/总部模块推荐候选短列表（完整 SKU + 价格仍以 `product_catalog.md` 为准）
- [#15] 合并「总原则」与「对话风格要求」为单一「交互原则」小节；把「默认值与少打字要求」改名为「套餐默认决策树」并压缩措辞，所有规则语义保持不变

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
