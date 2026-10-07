"""强制有依据 + 脱敏守卫测试。"""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from interview_agent import (  # noqa: E402
    AnonymizationError,
    Evidence,
    assess_candidate,
    load_candidate,
    load_guard,
    load_position,
)
from interview_agent.anonymize import assert_anonymized  # noqa: E402


class TestGrounding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_position(ROOT / "config", "backend_engineer")
        cls.guard = load_guard(ROOT / "config" / "guard.yaml")

    def test_01_every_score_has_evidence(self):
        """每个出分的维度都必须带原文引用，且引用能回到材料字段。"""
        cand = load_candidate(ROOT / "samples" / "candidate_advance.json")
        a = assess_candidate(self.config, self.guard, cand)
        self.assertTrue(a.dimension_scores)
        for dim in a.dimension_scores:
            self.assertTrue(dim.grounded, f"{dim.key} 出分了却没有证据")
            for ev in dim.evidence:
                self.assertTrue(ev.quote.strip())
                self.assertTrue(ev.source_field.startswith("materials."))

    def test_02_missing_evidence_is_refused_not_scored(self):
        """把材料掏空后，维度必须进 refused_items 而不是给 0 分。"""
        cand = load_candidate(ROOT / "samples" / "candidate_advance.json")
        stripped = copy.deepcopy(cand)
        stripped["materials"] = {"resume": {"summary": "无内容", "highlights": []}, "qa_transcript": [], "assessment_notes": []}
        a = assess_candidate(self.config, self.guard, stripped)
        self.assertEqual(a.dimension_scores, [])
        self.assertEqual(len(a.refused_items), len(self.config.dimensions))
        self.assertEqual(a.recommendation, "needs_review")

    def test_03_low_coverage_forces_review(self):
        """证据覆盖率不足时不得给出结论。"""
        cand = load_candidate(ROOT / "samples" / "candidate_needs_review.json")
        a = assess_candidate(self.config, self.guard, cand)
        self.assertLess(a.evidence_coverage, self.guard.min_evidence_coverage)
        self.assertEqual(a.recommendation, "needs_review")
        self.assertIn("不足以给出结论", " ".join(a.notes))

    def test_04_rule_hit_overrides_score(self):
        """命中硬性规则 -> 建议不通过，即便材料本身达标。"""
        cand = load_candidate(ROOT / "samples" / "candidate_rule_reject.json")
        a = assess_candidate(self.config, self.guard, cand)
        self.assertTrue(a.rule_hits)
        self.assertEqual(a.recommendation, "not_recommended")
        self.assertIn("min_years", [h.key for h in a.rule_hits])

    def test_05_evidence_requires_quote_and_source(self):
        with self.assertRaises(ValueError):
            Evidence(quote="   ", source_field="materials.resume")
        with self.assertRaises(ValueError):
            Evidence(quote="有内容", source_field="")


class TestAnonymization(unittest.TestCase):
    def test_01_samples_are_clean(self):
        for name in ("candidate_advance.json", "candidate_needs_review.json", "candidate_rule_reject.json"):
            cand = load_candidate(ROOT / "samples" / name)
            assert_anonymized(cand)  # 不抛异常即通过

    def test_02_pii_field_rejected(self):
        cand = load_candidate(ROOT / "samples" / "candidate_advance.json")
        dirty = copy.deepcopy(cand)
        dirty["candidate_email"] = "someone@example.com"
        with self.assertRaises(AnonymizationError):
            assert_anonymized(dirty)

    def test_03_pii_inside_text_rejected(self):
        cand = load_candidate(ROOT / "samples" / "candidate_advance.json")
        dirty = copy.deepcopy(cand)
        dirty["materials"]["resume"]["highlights"].append("联系方式 13800001111 方便沟通")
        with self.assertRaises(AnonymizationError):
            assert_anonymized(dirty)


if __name__ == "__main__":
    unittest.main(verbosity=2)
