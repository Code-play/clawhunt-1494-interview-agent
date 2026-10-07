"""人工决策边界测试：机器人无论如何都写不了最终决定。

这是本单验收标准里「人工决策边界」的可执行证明：
不是文档承诺，而是跑得出来的断言。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from interview_agent import (  # noqa: E402
    HumanDecisionGate,
    HumanDecisionViolation,
    assess_candidate,
    load_candidate,
    load_guard,
    load_position,
)
from interview_agent.anonymize import assert_anonymized  # noqa: E402


class TestHumanGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_position(ROOT / "config", "backend_engineer")
        cls.guard = load_guard(ROOT / "config" / "guard.yaml")

    def _assess(self, name: str):
        cand = load_candidate(ROOT / "samples" / name)
        assert_anonymized(cand)
        return assess_candidate(self.config, self.guard, cand)

    def test_01_bot_output_has_no_final_decision(self):
        """评估产出里 final_decision 必须是空的 —— 机器人不写决定。"""
        a = self._assess("candidate_advance.json")
        self.assertIsNone(a.final_decision)
        self.assertFalse(a.decision_sealed)
        self.assertTrue(a.needs_human_review, "任何建议都必须标注需人工复核")

    def test_02_agent_write_is_rejected(self):
        """机器人尝试写最终决定 -> 抛 HumanDecisionViolation。"""
        a = self._assess("candidate_advance.json")
        gate = HumanDecisionGate(reviewer="HUMAN-01")
        with self.assertRaises(HumanDecisionViolation):
            gate.attempt_agent_write(a, "advance")
        self.assertIsNone(a.final_decision, "被拒后决定字段仍必须为空")

    def test_03_human_write_succeeds_and_is_audited(self):
        """人类评审写入成功，并留下审计记录（含是否同意机器人建议）。"""
        a = self._assess("candidate_advance.json")
        gate = HumanDecisionGate(reviewer="HUMAN-01")
        gate.record(a, "advance", note="面试官确认")
        self.assertTrue(a.decision_sealed)
        self.assertEqual(a.final_decision["decision"], "advance")
        self.assertEqual(a.final_decision["reviewer"], "HUMAN-01")
        self.assertEqual(len(gate.audit), 1)
        self.assertTrue(gate.audit[0]["agreed_with_bot"])

    def test_04_human_can_override_bot(self):
        """人类可以推翻机器人建议（这里机器人建议 advance，人类判 reject）。"""
        a = self._assess("candidate_advance.json")
        self.assertEqual(a.recommendation, "advance")
        gate = HumanDecisionGate(reviewer="HUMAN-02")
        gate.record(a, "reject", note="现场表现与材料不符")
        self.assertEqual(a.final_decision["decision"], "reject")
        self.assertFalse(gate.audit[0]["agreed_with_bot"])

    def test_05_illegal_decision_value_rejected(self):
        a = self._assess("candidate_advance.json")
        gate = HumanDecisionGate(reviewer="HUMAN-01")
        with self.assertRaises(ValueError):
            gate.record(a, "hired", note="不合法的取值")

    def test_06_reviewer_identity_required(self):
        a = self._assess("candidate_advance.json")
        gate = HumanDecisionGate(reviewer="")
        with self.assertRaises(ValueError):
            gate.record(a, "hold", note="缺少评审人")


if __name__ == "__main__":
    unittest.main(verbosity=2)
