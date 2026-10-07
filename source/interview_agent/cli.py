"""命令行入口。

    python -m interview_agent prepare  --position backend_engineer --candidate samples/candidate_advance.json
    python -m interview_agent assess   --position backend_engineer --candidate samples/candidate_advance.json
    python -m interview_agent assess   --position backend_engineer --candidate samples/candidate_review.json --gate-demo
    python -m interview_agent check-anonymization --candidate samples/candidate_advance.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
# stderr 也必须改：中文 Windows 上默认是 GBK，提示信息被管道/重定向读取时会乱码
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from .anonymize import assert_anonymized
from .assess import assess_candidate
from .config import load_candidate, load_guard, load_position
from .human_gate import HumanDecisionGate
from .questions import build_prep_kit
from .schema import AnonymizationError, HumanDecisionViolation

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "config"
DEFAULT_GUARD = DEFAULT_CONFIG / "guard.yaml"


def _dump(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def cmd_prepare(args) -> int:
    config = load_position(args.config_dir, args.position)
    candidate = load_candidate(args.candidate)
    assert_anonymized(candidate)
    _dump(build_prep_kit(config, candidate))
    return 0


def cmd_assess(args) -> int:
    config = load_position(args.config_dir, args.position)
    guard = load_guard(args.guard)
    candidate = load_candidate(args.candidate)
    assert_anonymized(candidate)

    assessment = assess_candidate(config, guard, candidate)

    if args.gate_demo and args.reviewer:
        gate = HumanDecisionGate(reviewer=args.reviewer)
        try:
            gate.attempt_agent_write(assessment, "advance")
        except HumanDecisionViolation as exc:
            print(f"[人工边界生效] 机器人写入被拒绝: {exc}", file=sys.stderr)
        gate.record(assessment, args.decision, note=args.note or "")

    _dump(assessment.to_dict())
    return 0


def cmd_check_anonymization(args) -> int:
    candidate = load_candidate(args.candidate)
    try:
        assert_anonymized(candidate)
    except AnonymizationError as exc:
        print(f"未通过: {exc}")
        return 2
    print(f"通过: {args.candidate} 未发现个人信息字段")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="interview_agent", description="面试准备与评估辅助 Bot")
    p.add_argument("--config-dir", default=str(DEFAULT_CONFIG), help="配置目录（含 positions/ 与 question_bank.yaml）")
    sub = p.add_subparsers(dest="command", required=True)

    prep = sub.add_parser("prepare", help="生成面试准备包")
    prep.add_argument("--position", required=True)
    prep.add_argument("--candidate", required=True)
    prep.set_defaults(func=cmd_prepare)

    assess = sub.add_parser("assess", help="生成带依据的评估建议")
    assess.add_argument("--position", required=True)
    assess.add_argument("--candidate", required=True)
    assess.add_argument("--guard", default=str(DEFAULT_GUARD))
    assess.add_argument("--gate-demo", action="store_true", help="演示人工决策边界：先让机器人试写（会被拒），再由人类写入")
    assess.add_argument("--reviewer", default="", help="人类评审标识（脱敏代号）")
    assess.add_argument("--decision", default="hold", choices=["advance", "hold", "reject"])
    assess.add_argument("--note", default="")
    assess.set_defaults(func=cmd_assess)

    chk = sub.add_parser("check-anonymization", help="校验候选材料是否已脱敏")
    chk.add_argument("--candidate", required=True)
    chk.set_defaults(func=cmd_check_anonymization)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
