"""配置与面试准备包测试。"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from interview_agent import load_candidate, load_guard, load_position  # noqa: E402
from interview_agent.config import ConfigError  # noqa: E402
from interview_agent.questions import build_prep_kit  # noqa: E402


class TestConfig(unittest.TestCase):
    def test_01_loads_position(self):
        cfg = load_position(ROOT / "config", "backend_engineer")
        self.assertEqual(cfg.position, "backend_engineer")
        self.assertAlmostEqual(sum(d.weight for d in cfg.dimensions), 1.0)

    def test_02_rejects_bad_weight_sum(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "positions").mkdir()
            (tmp / "positions" / "broken.yaml").write_text(
                "position: broken\ntitle: x\ndimensions:\n"
                "  - key: a\n    label: A\n    weight: 0.5\n    signals: [x]\n",
                encoding="utf-8",
            )
            with self.assertRaises(ConfigError):
                load_position(tmp, "broken")

    def test_03_rejects_dimension_without_signals(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "positions").mkdir()
            (tmp / "positions" / "nosig.yaml").write_text(
                "position: nosig\ntitle: x\ndimensions:\n"
                "  - key: a\n    label: A\n    weight: 1.0\n    signals: []\n",
                encoding="utf-8",
            )
            with self.assertRaises(ConfigError):
                load_position(tmp, "nosig")

    def test_04_guard_values(self):
        g = load_guard(ROOT / "config" / "guard.yaml")
        self.assertGreater(g.min_evidence_coverage, 0)
        self.assertLessEqual(g.min_evidence_coverage, 1)
        self.assertGreater(g.min_quote_chars, 0)


class TestPrepKit(unittest.TestCase):
    def test_01_covers_every_dimension(self):
        cfg = load_position(ROOT / "config", "backend_engineer")
        cand = load_candidate(ROOT / "samples" / "candidate_advance.json")
        kit = build_prep_kit(cfg, cand)
        self.assertEqual(len(kit["sections"]), len(cfg.dimensions))
        for section in kit["sections"]:
            self.assertTrue(section["questions"], "每个维度都要有题")
            self.assertTrue(section["followups"], "每个维度都要有追问")

    def test_02_followups_react_to_material(self):
        """材料里有信号的维度应生成引用该信号的追问。"""
        cfg = load_position(ROOT / "config", "backend_engineer")
        cand = load_candidate(ROOT / "samples" / "candidate_advance.json")
        kit = build_prep_kit(cfg, cand)
        sd = next(s for s in kit["sections"] if s["dimension"] == "system_design")
        self.assertTrue(sd["material_signals"])
        self.assertTrue(any("材料里提到" in f for f in sd["followups"]))

    def test_03_notes_no_decision_in_prep(self):
        cfg = load_position(ROOT / "config", "backend_engineer")
        cand = load_candidate(ROOT / "samples" / "candidate_advance.json")
        kit = build_prep_kit(cfg, cand)
        self.assertIn("最终决定不由此模块产出", kit["note"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
