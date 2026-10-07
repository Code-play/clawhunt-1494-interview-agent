"""人工决策边界。

机器人可以：生成问题、产出建议、标注不确定性、列出证据。
机器人不可以：写最终决定。这一条由 HumanDecisionGate 在代码层强制，
而不是靠流程约定 —— 见 tests/test_human_gate.py。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .schema import ActorRole, Assessment, HumanDecisionViolation

ALLOWED_DECISIONS = ("advance", "hold", "reject")


@dataclass
class HumanDecisionGate:
    """人类评审写入最终决定的唯一入口。"""

    reviewer: str
    audit: list[dict] = field(default_factory=list)

    def record(self, assessment: Assessment, decision: str, note: str = "") -> Assessment:
        if decision not in ALLOWED_DECISIONS:
            raise ValueError(f"decision 必须是 {ALLOWED_DECISIONS} 之一，收到 {decision!r}")
        assessment._seal_decision(
            actor_role=ActorRole.HUMAN_REVIEWER,
            decision=decision,
            note=note,
            reviewer=self.reviewer,
        )
        self.audit.append(
            {
                "at": datetime.now(timezone.utc).isoformat(),
                "candidate_ref": assessment.candidate_ref,
                "reviewer": self.reviewer,
                "decision": decision,
                "note": note,
                "bot_recommendation": assessment.recommendation,
                "agreed_with_bot": assessment.recommendation == decision,
            }
        )
        return assessment

    def attempt_agent_write(self, assessment: Assessment, decision: str) -> None:
        """演示用：模拟机器人尝试写最终决定 —— 必然被拒绝。"""
        assessment._seal_decision(
            actor_role=ActorRole.AGENT,
            decision=decision,
            note="automated",
            reviewer="bot",
        )


__all__ = ["HumanDecisionGate", "ALLOWED_DECISIONS", "HumanDecisionViolation"]
