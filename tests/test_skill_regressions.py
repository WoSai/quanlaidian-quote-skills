"""
Prompt-validation tests for the 全来店报价 skill.

Each test sends a user message to Claude with SKILL.md + references as system prompt,
plays the role of the OpenClaw runtime by mocking the feishu_ask_user_question and Bash
tools, and asserts that the resulting tool calls match expected behavior.

Covers the 5 regressions fixed in PR #24 (湘菜 case):
  A. 湘菜 (tier-1 正餐 keyword) → no 轻餐/正餐 disambiguation card
  B. 同勾「无总部模块」+ 其他项 → 互斥校验取「无」
  C. 卡片选项 description 中不含具体金额 / 折扣率
  D. 卡片 1 拿到门店数档位后，不再追问精确门店数
  E. 卡片 2 包含「无门店增值模块」选项

These tests call the real Claude API. Set ANTHROPIC_API_KEY before running.
Override the model via SKILL_TEST_MODEL (defaults to claude-opus-4-7).
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import anthropic
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MODEL = os.environ.get("SKILL_TEST_MODEL", "claude-opus-4-7")
EFFORT = os.environ.get("SKILL_TEST_EFFORT", "low")
MAX_TURNS = int(os.environ.get("SKILL_TEST_MAX_TURNS", "4"))


def load_system_prompt() -> str:
    parts: list[str] = [
        "你正在 OpenClaw 飞书环境中运行。当用户消息触发『全来店报价』技能时，"
        "请严格按下方 SKILL.md 的工作流程和约束执行。可用工具是 "
        "`feishu_ask_user_question`（发送飞书消息卡片，单次调用可携带多个 question）"
        "和 `Bash`（执行 shell 命令，用于调用 `python3 scripts/quote.py --form <JSON>`）。"
        "本次会话的运行环境就是飞书，无 OpenClaw 原生表单可用。\n\n",
        "---\n\n# SKILL.md\n\n",
        (REPO_ROOT / "SKILL.md").read_text(encoding="utf-8"),
    ]
    refs_dir = REPO_ROOT / "references"
    if refs_dir.exists():
        for path in sorted(p for p in refs_dir.iterdir() if p.suffix == ".md"):
            parts.append(f"\n\n---\n\n# references/{path.name}\n\n")
            parts.append(path.read_text(encoding="utf-8"))
    return "".join(parts)


TOOLS = [
    {
        "name": "feishu_ask_user_question",
        "description": (
            "向用户发送飞书消息卡片，让用户点选/输入字段。"
            "单次调用可携带多个 question（每个 question 含 question 文案 + options 列表）。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "questions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "options": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "label": {"type": "string"},
                                        "description": {"type": "string"},
                                    },
                                },
                            },
                        },
                    },
                },
            },
            "required": ["questions"],
        },
    },
    {
        "name": "Bash",
        "description": (
            "执行 shell 命令。本 skill 用它调用 `python3 scripts/quote.py --form <JSON>`"
            " 生成报价文件。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    },
]

PRICE_PATTERN = re.compile(r"\d{2,}\s*元|/年\b|/店\b|/个\b|%|\d+\s*折")


@dataclass
class CapturedCalls:
    feishu_calls: list[dict] = field(default_factory=list)
    bash_calls: list[dict] = field(default_factory=list)
    text_blocks: list[str] = field(default_factory=list)
    stop_reasons: list[str] = field(default_factory=list)

    def all_card_options(self) -> list[dict]:
        out: list[dict] = []
        for call in self.feishu_calls:
            for q in call.get("questions", []):
                out.extend(q.get("options", []) or [])
        return out

    def all_card_questions(self) -> list[dict]:
        out: list[dict] = []
        for call in self.feishu_calls:
            out.extend(call.get("questions", []) or [])
        return out


@pytest.fixture(scope="session")
def client() -> anthropic.Anthropic:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set; skipping live prompt-validation tests")
    return anthropic.Anthropic()


@pytest.fixture(scope="session")
def system_prompt() -> str:
    return load_system_prompt()


CANNED_QUOTE_RESULT = json.dumps(
    {
        "stdout": json.dumps(
            {
                "preview": {
                    "门店套餐": "全能版",
                    "totals": {"final": 100000},
                    "pricing_info": {"algorithm_version": "v1"},
                    "files": {
                        "pdf": "/tmp/quote.pdf",
                        "xlsx": "/tmp/quote.xlsx",
                        "json": "/tmp/quote.json",
                    },
                },
            },
            ensure_ascii=False,
        ),
        "returncode": 0,
    },
    ensure_ascii=False,
)


def run_scenario(
    client: anthropic.Anthropic,
    system_prompt: str,
    user_message: str,
    canned_feishu_response: dict,
    *,
    max_turns: int = MAX_TURNS,
) -> CapturedCalls:
    """Send user_message; for each feishu_ask_user_question tool call, return the
    canned response; for each Bash tool call, return a canned quote.py result and stop."""
    captured = CapturedCalls()
    messages: list[dict] = [{"role": "user", "content": user_message}]

    for _ in range(max_turns):
        response = client.messages.create(
            model=MODEL,
            max_tokens=8000,
            output_config={"effort": EFFORT},
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=TOOLS,
            messages=messages,
        )
        captured.stop_reasons.append(response.stop_reason or "")

        for block in response.content:
            if block.type == "text":
                captured.text_blocks.append(block.text)

        if response.stop_reason != "tool_use":
            break

        messages.append({"role": "assistant", "content": response.content})

        tool_results: list[dict] = []
        stop_after = False
        for block in response.content:
            if block.type != "tool_use":
                continue
            if block.name == "feishu_ask_user_question":
                captured.feishu_calls.append(dict(block.input))
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(canned_feishu_response, ensure_ascii=False),
                    }
                )
            elif block.name == "Bash":
                captured.bash_calls.append(dict(block.input))
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": CANNED_QUOTE_RESULT,
                    }
                )
                stop_after = True

        messages.append({"role": "user", "content": tool_results})
        if stop_after:
            break

    return captured


# ============================================================
# A. 湘菜 → 一级正餐关键词，不发轻餐/正餐 disambiguation card
# ============================================================


def test_xiangcai_skips_disambiguation_card(client, system_prompt):
    captured = run_scenario(
        client,
        system_prompt,
        user_message="做个胡子大厨湘菜的报价单，50 家店",
        canned_feishu_response={"submitted": True, "answers": {}},
    )

    for q in captured.all_card_questions():
        labels = [opt.get("label", "") for opt in q.get("options", []) or []]
        has_qingcan = any("轻餐" in lbl for lbl in labels)
        has_zhengcan = any("正餐" in lbl for lbl in labels)
        question_text = q.get("question", "")
        assert not (has_qingcan and has_zhengcan), (
            "湘菜 is a tier-1 正餐 keyword and should be auto-detected — "
            "the agent should NOT send a 轻餐/正餐 disambiguation question. "
            f"Got:\n  question: {question_text}\n  options: {labels}"
        )

    assert captured.bash_calls, (
        "Agent should eventually invoke scripts/quote.py to generate the quote. "
        f"Captured no Bash calls. Text:\n{''.join(captured.text_blocks)[:500]}"
    )
    bash_cmd = " ".join(b.get("command", "") for b in captured.bash_calls)
    assert "quote.py" in bash_cmd, f"Bash call should invoke quote.py:\n{bash_cmd}"
    assert "正餐" in bash_cmd, (
        f"quote.py --form payload should set 餐饮类型=正餐 for 湘菜 brand:\n{bash_cmd}"
    )


# ============================================================
# C. 卡片选项 description 不含具体金额 / 折扣率
#    (Run alongside scenarios that trigger card 2 — broadest coverage)
# ============================================================


def _collect_price_offenders(captured: CapturedCalls) -> list[str]:
    offenders: list[str] = []
    for opt in captured.all_card_options():
        desc = opt.get("description", "") or ""
        if PRICE_PATTERN.search(desc):
            offenders.append(f"  - label={opt.get('label')!r} description={desc!r}")
    return offenders


def test_card_descriptions_have_no_prices_via_chacanting(client, system_prompt):
    """茶餐厅 = 三级歧义 → 走顺序卡兜底 → 至少触发卡片 1（+ 可能卡片 2）。
    所有卡片选项的 description 都应满足『禁价格』硬规则。"""
    captured = run_scenario(
        client,
        system_prompt,
        user_message="给我做个『鸿运茶餐厅』的报价单",
        canned_feishu_response={
            "submitted": True,
            "answers": {
                "品牌名称": "鸿运茶餐厅",
                "餐饮类型": "正餐",
                "门店数量": "11-30店",
            },
        },
        max_turns=3,
    )

    offenders = _collect_price_offenders(captured)
    assert not offenders, (
        "卡片选项 description 不得含具体金额 / 折扣率（per SKILL.md 卡片设计规则）。\n"
        "违规选项：\n" + "\n".join(offenders)
    )


# ============================================================
# E. 卡片 2 / 总部模块 / 增值模块 多选都含「无 X 模块」选项
# ============================================================


def test_card_2_includes_no_value_add_module(client, system_prompt):
    captured = run_scenario(
        client,
        system_prompt,
        user_message="给我做个『鸿运茶餐厅』的报价单",
        canned_feishu_response={
            "submitted": True,
            "answers": {
                "品牌名称": "鸿运茶餐厅",
                "餐饮类型": "正餐",
                "门店数量": "11-30店",
            },
        },
        max_turns=3,
    )

    value_add_cards: list[tuple[str, list[str]]] = []
    for q in captured.all_card_questions():
        question_text = q.get("question", "") or ""
        options = q.get("options", []) or []
        labels = [opt.get("label", "") for opt in options]
        joined = question_text + " " + " ".join(labels)
        if "增值模块" in joined or "门店增值" in joined:
            value_add_cards.append((question_text, labels))

    if not value_add_cards:
        pytest.skip(
            "本轮没有触发『门店增值模块』多选卡片（可能 LLM 走了别的路径）；"
            "由 _no_prices_ 测试覆盖该字段是否含金额。"
        )

    for question_text, labels in value_add_cards:
        has_wu = any(("无门店增值模块" in lbl) or ("无增值模块" in lbl) for lbl in labels)
        assert has_wu, (
            "门店增值模块多选必须把『无门店增值模块』作为可选项（per SKILL.md:107）。\n"
            f"  question: {question_text}\n  options: {labels}"
        )


# ============================================================
# D. 卡片 1 拿到门店数档位（31-100店）后，不应追问精确门店数
# ============================================================


def test_no_second_card_for_exact_store_count(client, system_prompt):
    captured = run_scenario(
        client,
        system_prompt,
        user_message="给我做个『鸿运茶餐厅』的报价单",
        canned_feishu_response={
            "submitted": True,
            "answers": {
                "品牌名称": "鸿运茶餐厅",
                "餐饮类型": "正餐",
                "门店数量": "31-100店",
            },
        },
        max_turns=4,
    )

    forbidden = ("准确门店数", "精确门店数", "具体多少家店", "具体门店数")
    for idx, call in enumerate(captured.feishu_calls):
        for q in call.get("questions", []) or []:
            question_text = q.get("question", "") or ""
            for forbidden_phrase in forbidden:
                if forbidden_phrase in question_text:
                    pytest.fail(
                        f"门店数采集后不应二次追问精确数字（per SKILL.md 卡片设计规则）。\n"
                        f"  第 {idx + 1} 张卡片包含禁止文案 {forbidden_phrase!r}: {question_text}"
                    )


# ============================================================
# B. 互斥校验：同勾「无总部模块」+「配送中心」时取「无」
# ============================================================


def test_mutual_exclusion_no_hq_module(client, system_prompt):
    captured = run_scenario(
        client,
        system_prompt,
        user_message="给我做个『鸿运茶餐厅』的报价单",
        canned_feishu_response={
            "submitted": True,
            "answers": {
                "品牌名称": "鸿运茶餐厅",
                "餐饮类型": "正餐",
                "门店数量": "11-30店",
                "门店套餐": "全能版",
                "总部模块": ["无总部模块", "配送中心", "生产加工"],
                "门店增值模块": ["无门店增值模块"],
            },
        },
        max_turns=4,
    )

    assert captured.bash_calls, (
        "Agent should eventually invoke quote.py after submission. "
        f"Stop reasons: {captured.stop_reasons}"
    )

    final_command = captured.bash_calls[-1].get("command", "")
    text_combined = "\n".join(captured.text_blocks)

    # Heuristic check 1: form JSON should not list 配送中心 as a 总部模块 entry
    # (the互斥 rule clears the other selections when 无 is also chosen)
    # We allow 配送中心 to be MENTIONED in摘要 text, but the structured field shouldn't have it.
    # As a practical proxy: check the JSON-quoted form fragment.
    form_match = re.search(r"--form\s+'([^']+)'", final_command) or re.search(
        r'--form\s+"((?:[^"\\]|\\.)*)"', final_command
    )
    form_blob = form_match.group(1) if form_match else final_command

    has_peisongzhongxin_in_form = '"配送中心"' in form_blob
    has_wu_in_form = '"无总部模块"' in form_blob

    # Either (a) 配送中心 is dropped from the 总部模块 list, OR
    # (b) the agent represented 总部=无 explicitly AND quote.py form structure
    # is clear (we accept this as evidence互斥 was applied).
    assert (not has_peisongzhongxin_in_form) or (
        not has_wu_in_form and "忽略" in text_combined
    ), (
        "Agent must apply 互斥校验 when both 「无总部模块」 and 其他总部模块 are "
        "selected — drop the other selections and keep only 「无」 "
        "(per SKILL.md card-answer → API correction table).\n"
        f"Final quote.py command:\n{final_command[:1200]}\n\n"
        f"Text response excerpt:\n{text_combined[:500]}"
    )

    # Heuristic check 2: agent should announce the resolution in the summary
    announced = any(
        kw in text_combined
        for kw in ("无总部模块", "忽略", "已忽略", "其他勾选", "互斥")
    )
    assert announced, (
        "Agent should mention the 互斥 resolution in the 配置摘要 "
        "(e.g. 「按『无总部模块』处理，其他勾选已忽略」).\n"
        f"Text response:\n{text_combined[:800]}"
    )
