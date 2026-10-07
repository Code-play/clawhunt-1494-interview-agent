"""带依据的评估：每个维度都必须能引用候选材料原文，否则拒绝生成该项。

这里刻意不使用任何大模型：
- 交付要求写明第三方费用（模型 API）不含在本单预算内；
- 更要紧的是可复现 —— 同一份材料任何时候跑都得到同一份结果，
  验证记录才能被买家一键复跑比对。
"""

from __future__ import annotations

import re
from typing import Any

from .config import Guard, PositionConfig
from .schema import (
    Assessment,
    DimensionScore,
    Evidence,
    RefusedItem,
    RuleHit,
)

_SENTENCE_SPLIT = re.compile(r"[。；;!?\n]+")


def _units(
    materials: dict[str, Any],
    prefix: str = "materials",
    sources: tuple[str, ...] | None = None,
) -> list[tuple[str, str]]:
    """把材料拍平成 (字段路径, 句子) 列表 —— 证据必须能回到具体字段。

    只从候选人自述类字段取证据（默认 resume / qa_transcript）。
    面试官的 assessment_notes 不作为证据来源：拿"面试官的判断"去证明
    "面试官的判断"是循环论证，也会让阈值失真。
    """
    out: list[tuple[str, str]] = []

    def walk(node: Any, path: str, top: str | None) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{path}.{k}", top if top is not None else k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]", top)
        elif isinstance(node, str):
            if sources is not None and top not in sources:
                return
            for raw in _SENTENCE_SPLIT.split(node):
                s = raw.strip()
                if s:
                    out.append((path, s))
        elif node is not None:
            if sources is not None and top not in sources:
                return
            out.append((path, str(node)))

    walk(materials, prefix, None)
    return out


def _lookup(node: dict[str, Any], field: str) -> Any:
    cur: Any = node
    for part in field.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _eval_rule(rule, candidate: dict[str, Any]) -> RuleHit | None:
    actual = _lookup(candidate, rule.field)
    if actual is None:
        return RuleHit(rule.key, rule.label, f"材料缺少字段 {rule.field}，需人工核实")
    if rule.op == "min_value" and isinstance(actual, (int, float)) and actual < rule.value:
        return RuleHit(rule.key, rule.label, f"{rule.field}={actual} 低于要求 {rule.value}")
    if rule.op == "max_value" and isinstance(actual, (int, float)) and actual > rule.value:
        return RuleHit(rule.key, rule.label, f"{rule.field}={actual} 高于上限 {rule.value}")
    if rule.op == "required_in":
        declared = actual if isinstance(actual, list) else [actual]
        if rule.value not in declared:
            return RuleHit(rule.key, rule.label, f"{rule.field} 未包含必需项 {rule.value}")
    return None


def assess_candidate(
    config: PositionConfig,
    guard: Guard,
    candidate: dict[str, Any],
    max_evidence_per_dimension: int = 3,
) -> Assessment:
    """产出建议（recommendation）。注意：不产出最终决定。"""
    units = _units(candidate.get("materials") or {}, sources=config.evidence_sources)
    lower_units = [(path, sent, sent.lower()) for path, sent in units]

    result = Assessment(
        candidate_ref=str(candidate.get("candidate_ref") or "UNKNOWN"),
        position=config.position,
    )

    for dim in config.dimensions:
        matched_signals: list[str] = []
        evidence: list[Evidence] = []
        seen_quotes: set[str] = set()

        for signal in dim.signals:
            hit_sentence: tuple[str, str] | None = None
            for path, sent, low in lower_units:
                if signal in low:
                    hit_sentence = (path, sent)
                    break
            if not hit_sentence:
                continue
            matched_signals.append(signal)
            path, sent = hit_sentence
            if len(sent) >= guard.min_quote_chars and sent not in seen_quotes:
                seen_quotes.add(sent)
                if len(evidence) < max_evidence_per_dimension:
                    evidence.append(Evidence(quote=sent, source_field=path))

        if not matched_signals or not evidence:
            result.refused_items.append(
                RefusedItem(
                    key=dim.key,
                    label=dim.label,
                    reason="材料中找不到可引用的原文（或引用短于最小长度），拒绝为该维度打分",
                    weight=dim.weight,
                )
            )
            continue

        score = round(100.0 * len(matched_signals) / len(dim.signals), 2)
        result.dimension_scores.append(
            DimensionScore(
                key=dim.key,
                label=dim.label,
                weight=dim.weight,
                score=score,
                evidence=evidence,
                rationale=(
                    f"命中 {len(matched_signals)}/{len(dim.signals)} 个信号"
                    f"（{('、'.join(matched_signals))}），按命中比例折算得分。"
                ),
            )
        )

    # 硬性规则
    for rule in config.hard_rules:
        hit = _eval_rule(rule, candidate)
        if hit:
            result.rule_hits.append(hit)

    scored = [d for d in result.dimension_scores if d.grounded]
    scored_weight = sum(d.weight for d in scored)
    weighted = (
        sum((d.score or 0.0) * d.weight for d in scored) / scored_weight if scored_weight else 0.0
    )
    coverage = result.evidence_coverage

    if result.rule_hits:
        result.recommendation = "not_recommended"
        result.notes.append("命中硬性规则，建议不通过；仍须人工确认后才生效。")
    elif coverage < guard.min_evidence_coverage:
        result.recommendation = "needs_review"
        result.notes.append(
            f"证据覆盖率 {coverage:.0%} 低于阈值 {guard.min_evidence_coverage:.0%}，"
            "不足以给出结论，转人工补充材料。"
        )
    elif weighted >= 70:
        result.recommendation = "advance"
        result.notes.append(f"加权得分 {weighted:.1f}，建议进入下一轮；最终决定由人工写入。")
    elif weighted >= guard.borderline_confidence * 100:
        result.recommendation = "borderline"
        result.notes.append(f"加权得分 {weighted:.1f}，处于边界区间，建议人工复核。")
    else:
        result.recommendation = "not_recommended"
        result.notes.append(f"加权得分 {weighted:.1f} 低于边界下限；仍须人工确认。")

    result.confidence = round(min(1.0, coverage) * (weighted / 100.0), 4)
    result.needs_human_review = True
    result.notes.append("系统只产出建议；final_decision 只能由人类评审写入。")
    return result
