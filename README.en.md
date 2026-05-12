# Quanlaidian Quote — OpenClaw Skill

> [中文版 →](README.md)

An OpenClaw skill: collects quotation fields based on the runtime environment, then returns a quotation summary with download links for PDF / Excel / JSON config files.

**Field collection paths** (auto-selected by runtime environment, with a unified conversational fallback — see `SKILL.md` for details):

- **Feishu chat environment** → uses `feishu_ask_user_question` interactive cards (3 rounds + 1 optional confirmation card; fields already supplied by the user are skipped automatically)
- **OpenClaw and other platforms** → uses the native form
- **Neither available** → falls back to a low-typing, option-driven guided dialogue

**Version:** 1.2.0　**Dependencies:** Python 3 standard library only

---

## Install

Zero extra dependencies — works immediately after cloning.

---

## Auto-update

OpenClaw nodes check the `VERSION` file on `main` daily at 01:00 and run `git pull --ff-only` when a newer version is published.

One-shot enable (installs into the current user's crontab, idempotent):

```bash
bash scripts/install_cron.sh
```

| Action | Command |
|---|---|
| Manual check (no pull) | `python3 scripts/check_openclaw_update.py` |
| Manual check + pull | `python3 scripts/check_openclaw_update.py --apply` |
| Tail log | `tail -f ~/.cache/quanlaidian-quote-skills/update.log` |
| Disable | `crontab -e` — delete the line containing `check_openclaw_update.py` |

Overridable env vars: `SKILL_REPO` (default `jasonshao/quanlaidian-quote-skills`), `SKILL_LOCAL_DIR` (default: the repo root containing the script), `SKILL_UPDATE_LOG_DIR` (default `~/.cache/quanlaidian-quote-skills`).

> **Release note:** Detection is based on the repo-root `VERSION` file. Release commits merged into `main` **must** bump `VERSION`, otherwise nodes will not pull.

---

## Release Flow (release-please automation)

The repo uses [release-please](https://github.com/googleapis/release-please) to aggregate changes based on Conventional Commits.

- Every PR merged into `main` triggers `.github/workflows/release-please.yml`.
- release-please scans commits since the last release (`feat:` / `fix:` / `docs:` / `refactor:` / `perf:`, etc.), then opens/updates a **release PR** (titled like `chore(release): 1.3.0`) that groups entries by type into `CHANGELOG.md` and bumps the version in `.release-please-manifest.json`.
- **Reviewer steps**:
  1. Review the CHANGELOG draft in the release PR; tidy wording if needed.
  2. Sync the version in `.release-please-manifest.json` into the `VERSION` file (release-please does not touch `VERSION` by default, because the auto-update script on nodes reads it directly).
  3. Merge the release PR. release-please then automatically creates a `v<version>` git tag and a GitHub Release.
- Commit message convention: use Conventional Commits (`feat:` / `fix:` / `docs:` / `refactor:` / `perf:` / `chore:`, etc.). `chore` / `test` / `build` / `ci` / `style` are hidden from the CHANGELOG by default.
- Config files: `release-please-config.json` (section rules) + `.release-please-manifest.json` (current version).

---

## Configure

Set these environment variables:

| Variable | Required | Description |
|---|---|---|
| `QUOTE_API_TOKEN` | ✅ | API token (one per organisation, issued by the service admin) |
| `QUOTE_API_URL` | ❌ | Quote service endpoint, default `https://<your-api-host>/v1/quote`; for production use `https://<your-api-host>/v1/quote` (ask the admin for the actual host) |

---

## Usage

The skill collects fields internally based on the runtime (Feishu cards / native form / guided dialogue) and then invokes the following with the same structured form JSON:

```bash
python3 scripts/quote.py --form <path-to-form.json>
```

Form JSON fields are defined in `references/openclaw_form_schema.json`; see `references/openclaw_form_submission.example.json` for an example. OpenClaw also calls this script automatically when the user submits the native form.

### Output

The script writes Markdown directly to stdout:

```markdown
## 本次配置摘要

- 品牌：示例品牌
- 餐饮类型：正餐    门店数：10
- 套餐：旗舰版
- 总价：¥408,000

## 下载文件

- [报价单 PDF](https://<your-api-host>/files/.../示例品牌-全来店-报价单-20260419.pdf)
- [报价单 Excel](https://<your-api-host>/files/.../示例品牌-全来店-报价单-20260419.xlsx)
- [报价配置 JSON](https://<your-api-host>/files/.../示例品牌-全来店-报价配置-20260419.json)

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
| `门店数量` | integer | ✅ | 1 – 300; 31–300 auto-routes to anchor + tiered comparison (see service README) |
| `门店套餐` | string | ✅ | e.g. `"旗舰版"` |
| `门店增值模块` | string[] | ❌ | |
| `总部模块` | string[] | ❌ | |
| `配送中心数量` | integer | ❌ | ≥ 0 |
| `生产加工中心数量` | integer | ❌ | ≥ 0 |
| `成交价系数` | float | ❌ | 0.01 – 1.0; **`人工改价原因` is required when this is explicitly provided** |
| `人工改价原因` | string | ❌ | Required when `成交价系数` is explicitly provided, kept for audit trail |
| `是否启用阶梯报价` | boolean | ❌ | |
| `实施服务类型` | string | ❌ | |
| `实施服务人天` | integer | ❌ | ≥ 0 |


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
│   ├── quote.py                          # 45-line client — zero extra deps
│   ├── check_openclaw_update.py          # Daily self-update checker
│   └── install_cron.sh                   # Idempotent crontab installer
└── references/
    ├── openclaw_form_schema.json         # Form JSON Schema
    ├── openclaw_form_config.json         # OpenClaw form control config
    ├── openclaw_form_submission.example.json  # Example submission
    ├── product_catalog.md                # Product catalogue (sales reference)
    └── sales_guide.md                    # Sales talking points and use cases
```
