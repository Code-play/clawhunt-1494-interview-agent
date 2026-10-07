"""核心数据模型。

设计原则（对应本单验收标准「带依据的评估模板」与「人工决策边界」）：

1. 评估的每一项都必须挂证据（Evidence）。没有证据的项不产出分数，而是进
   refused_items —— 这是"强制有依据"在数据结构层面的落地，不是文档约定。
2. 最终决定（final decision）不属于机器人可写字段。机器人只能产出
   recommendation（建议）；最终决定由 HumanDecisionGate 以"人类操作者"身份写入。
   任何以 agent 身份写入最终决定的尝试都会抛 HumanDecisionViolation。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ActorRole(str, Enum):
    """操作者身份。只有 HUMAN_REVIEWER 有权写最终决定。"""

    AGENT = "agent"
    HUMAN_REVIEWER = "human_reviewer"


class HumanDecisionViolation(RuntimeError):
    """机器人（或任何非人类操作者）试图写最终决定。"""


class AnonymizationError(ValueError):
    """候选材料里出现了未脱敏的个人信息字段。"""


@dataclass(frozen=True)
class Evidence:
    """一条证据：必须能回到原文的一句话。"""

    quote: str
    source_field: str

    def __post_init__(self) -> None:
        if not self.quote or not self.quote.strip():
            raise ValueError("Evidence.quote 不能为空 —— 没有原文引用就不是证据")
        if not self.source_field:
            raise ValueError("Evidence.source_field 不能为空 —— 证据必须可回溯到材料字段")


@dataclass
class DimensionScore:
    """一个评分维度的结果。带证据才算分。"""

    key: str
    label: str
    weight: float
    score: float | None
    evidence: list[Evidence] = field(default_factory=list)
    rationale: str = ""

    @property
    def grounded(self) -> bool:
        return bool(self.evidence)


@dataclass
class RefusedItem:
    """因证据不足而拒绝生成的评分项。"""

    key: str
    label: str
    reason: str
    weight: float = 0.0


@dataclass
class RuleHit:
    """命中的硬性规则。"""

    key: str
    label: str
    detail: str


@dataclass
class Assessment:
    """机器人产出物。注意：这里没有可写的终局决定字段。"""

    candidate_ref: str
    position: str
    dimension_scores: list[DimensionScore] = field(default_factory=list)
    refused_items: list[RefusedItem] = field(default_factory=list)
    rule_hits: list[RuleHit] = field(default_factory=list)
    recommendation: str = "needs_review"
    confidence: float = 0.0
    needs_human_review: bool = True
    notes: list[str] = field(default_factory=list)

    # 最终决定是"只读"的：只能由 HumanDecisionGate 通过 _seal_decision 写入。
    _final_decision: dict[str, Any] | None = field(default=None, repr=False)
    _decision_sealed: bool = field(default=False, repr=False)

    @property
    def final_decision(self) -> dict[str, Any] | None:
        """最终决定。读取自由，写入只能走 HumanDecisionGate。"""
        return self._final_decision

    def _seal_decision(self, actor_role: ActorRole, decision: str, note: str, reviewer: str) -> None:
        """唯一写入口。非人类操作者一律拒绝。"""
        if actor_role is not ActorRole.HUMAN_REVIEWER:
            raise HumanDecisionViolation(
                "最终录用决定只能由人类评审写入；机器人只能输出 recommendation"
            )
        if not decision:
            raise ValueError("decision 不能为空")
        if not reviewer:
            raise ValueError("必须记录评审人标识（可脱敏代号）")
        self._final_decision = {"decision": decision, "note": note, "reviewer": reviewer}
        self._decision_sealed = True

    @property
    def decision_sealed(self) -> bool:
        return self._decision_sealed

    @property
    def evidence_coverage(self) -> float:
        """有证据的维度权重占比 —— 用来判断结论是否站得住。

        分母必须包含被拒项，否则覆盖率恒为 100%，阈值形同虚设。
        """
        total = sum(d.weight for d in self.dimension_scores) + sum(r.weight for r in self.refused_items)
        scored = sum(d.weight for d in self.dimension_scores if d.grounded)
        return (scored / total) if total else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_ref": self.candidate_ref,
            "position": self.position,
            "recommendation": self.recommendation,
            "confidence": round(self.confidence, 4),
            "needs_human_review": self.needs_human_review,
            "evidence_coverage": round(self.evidence_coverage, 4),
            "rule_hits": [h.__dict__ for h in self.rule_hits],
            "dimension_scores": [
                {
                    "key": d.key,
                    "label": d.label,
                    "weight": d.weight,
                    "score": d.score,
                    "grounded": d.grounded,
                    "rationale": d.rationale,
                    "evidence": [e.__dict__ for e in d.evidence],
                }
                for d in self.dimension_scores
            ],
            "refused_items": [r.__dict__ for r in self.refused_items],
            "final_decision": self._final_decision,
            "notes": self.notes,
        }
