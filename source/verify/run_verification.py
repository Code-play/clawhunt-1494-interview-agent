"""一键复跑验证记录。

    python verify/run_verification.py

做三件事：
1. 对三份脱敏样例各跑一遍完整流程（脱敏校验 -> 面试准备包 -> 带依据评估）；
2. 断言每条预期（含"机器人写最终决定必须被拒"）；
3. 把输入、原始输出、断言结论写成 verify/verification_record.md 与
   verify/verification_result.json —— 买家可直接比对，无需人工看截图。

输出同时写到文件（UTF-8）与标准输出；文件是准的，终端编码不影响比对。
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
# stderr 同样必须是 UTF-8，否则中文 Windows 下重定向会乱码
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from interview_agent import (  # noqa: E402
    HumanDecisionGate,
    HumanDecisionViolation,
    assess_candidate,
    build_prep_kit,
    load_candidate,
    load_guard,
    load_position,
)
from interview_agent.anonymize import assert_anonymized  # noqa: E402

POSITION = "backend_engineer"
SAMPLES = (
    ("candidate_advance.json", "advance", "材料齐备，建议进入下一轮（仍待人工确认）"),
    ("candidate_needs_review.json", "needs_review", "证据不足，转人工补材料"),
    ("candidate_rule_reject.json", "not_recommended", "命中硬性规则（经验下限）"),
)


@dataclass
class Check:
    name: str
    expected: str
    actual: str
    passed: bool


def main() -> int:
    config = load_position(ROOT / "config", POSITION)
    guard = load_guard(ROOT / "config" / "guard.yaml")
    checks: list[Check] = []
    transcript: list[str] = []

    def add(name: str, expected, actual, ok: bool) -> None:
        checks.append(Check(name, str(expected), str(actual), bool(ok)))

    transcript.append(f"# 验证记录 · 面试 Agent（订单 #1494）\n")
    transcript.append(f"生成时间：{datetime.now(timezone.utc).isoformat()}")
    transcript.append(f"岗位配置：{POSITION}；阈值：证据覆盖率 >= {guard.min_evidence_coverage}、引用 >= {guard.min_quote_chars} 字\n")
    transcript.append("复跑命令：`python verify/run_verification.py`\n")

    # ---------- 1. 脱敏校验 ----------
    transcript.append("## 1. 脱敏校验（材料含个人信息即拒绝处理）\n")
    for name, _, _ in SAMPLES:
        cand = load_candidate(ROOT / "samples" / name)
        try:
            assert_anonymized(cand)
            add(f"脱敏校验 {name}", "通过", "通过", True)
            transcript.append(f"- `{name}`：通过")
        except Exception as exc:  # noqa: BLE001
            add(f"脱敏校验 {name}", "通过", f"未通过: {exc}", False)
            transcript.append(f"- `{name}`：未通过 {exc}")
    transcript.append("")

    # ---------- 2. 面试准备包 ----------
    transcript.append("## 2. 面试准备包（每个维度出题 + 依据材料生成追问）\n")
    first = load_candidate(ROOT / "samples" / SAMPLES[0][0])
    kit = build_prep_kit(config, first)
    add("准备包覆盖全部维度", len(config.dimensions), len(kit["sections"]), len(kit["sections"]) == len(config.dimensions))
    for section in kit["sections"]:
        transcript.append(
            f"- **{section['label']}**：{len(section['questions'])} 题，"
            f"命中材料信号 {len(section['material_signals'])} 个，追问 {len(section['followups'])} 条"
        )
        transcript.append(f"  - 例题：{section['questions'][0]}")
    transcript.append("")

    # ---------- 3. 带依据评估 ----------
    transcript.append("## 3. 带依据评估（无原文引用不给分）\n")
    assessments = {}
    for name, expected_reco, desc in SAMPLES:
        cand = load_candidate(ROOT / "samples" / name)
        a = assess_candidate(config, guard, cand)
        assessments[name] = (a, desc)
        add(f"{name} 建议结果", expected_reco, a.recommendation, a.recommendation == expected_reco)
        add(f"{name} 最终决定为空（机器人不写）", None, a.final_decision, a.final_decision is None)
        add(f"{name} 标注需人工复核", True, a.needs_human_review, a.needs_human_review is True)

        transcript.append(f"### {name} —— {desc}")
        transcript.append(
            f"- 建议：`{a.recommendation}`；置信度 {a.confidence:.3f}；"
            f"证据覆盖率 {a.evidence_coverage:.0%}；需人工复核：{a.needs_human_review}"
        )
        if a.rule_hits:
            transcript.append("- 命中硬性规则：" + "；".join(f"`{h.key}` {h.detail}" for h in a.rule_hits))
        for d in a.dimension_scores:
            quote = d.evidence[0].quote if d.evidence else ""
            transcript.append(f"  - {d.label}：{d.score} 分（权重 {d.weight}）依据 `{d.evidence[0].source_field}`：「{quote[:60]}」")
        for r in a.refused_items:
            transcript.append(f"  - {r.label}：**拒绝打分** —— {r.reason}")
        for note in a.notes:
            transcript.append(f"  - 备注：{note}")
        transcript.append("")

    # ---------- 4. 人工决策边界 ----------
    transcript.append("## 4. 人工决策边界（代码层强制，非流程约定）\n")
    a = assessments[SAMPLES[0][0]][0]
    gate = HumanDecisionGate(reviewer="HUMAN-01")
    rejected = False
    try:
        gate.attempt_agent_write(a, "advance")
    except HumanDecisionViolation as exc:
        rejected = True
        transcript.append(f"- 机器人写入最终决定：**被拒绝** —— {exc}")
    add("机器人写最终决定被拒", "HumanDecisionViolation", rejected, rejected)
    add("被拒后决定字段仍为空", None, a.final_decision, a.final_decision is None)
    transcript.append(f"- 被拒后 `final_decision`：{a.final_decision}")

    gate.record(a, "hold", note="面试官要求补充协作事例")
    add("人类评审写入成功", "hold", (a.final_decision or {}).get("decision"), (a.final_decision or {}).get("decision") == "hold")
    add("审计记录含是否同意建议", True, bool(gate.audit), bool(gate.audit))
    transcript.append(f"- 人类评审写入：`{a.final_decision}`")
    transcript.append(f"- 审计记录：{json.dumps(gate.audit, ensure_ascii=False)}")
    transcript.append("")

    # ---------- 5. 单元测试 ----------
    transcript.append("## 5. 单元测试\n")
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=180,
        )
        tail = (proc.stderr or "").strip().splitlines()
        summary = tail[-3] if len(tail) >= 3 else (proc.stderr or "").strip()
        ok = proc.returncode == 0
        add("单元测试全部通过", "returncode 0", proc.returncode, ok)
        transcript.append(f"```\n{summary}\n```")
    except Exception as exc:  # noqa: BLE001
        add("单元测试全部通过", "returncode 0", f"异常 {exc}", False)
        transcript.append(f"单元测试执行异常：{exc}")
    transcript.append("")

    # ---------- 结论 ----------
    failed = [c for c in checks if not c.passed]
    transcript.append("## 结论\n")
    transcript.append(f"- 断言总数：{len(checks)}；通过：{len(checks) - len(failed)}；失败：{len(failed)}")
    transcript.append(f"- 结果：**{'全部通过' if not failed else '存在失败项'}**\n")
    transcript.append("| 断言 | 预期 | 实际 | 结果 |")
    transcript.append("|---|---|---|---|")
    for c in checks:
        transcript.append(f"| {c.name} | {c.expected} | {c.actual} | {'通过' if c.passed else '失败'} |")

    body = "\n".join(transcript)
    (ROOT / "verify" / "verification_record.md").write_text(body, encoding="utf-8")
    (ROOT / "verify" / "verification_result.json").write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "position": POSITION,
                "checks_total": len(checks),
                "checks_passed": len(checks) - len(failed),
                "checks_failed": len(failed),
                "all_passed": not failed,
                "checks": [c.__dict__ for c in checks],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(body)
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
