"""面试准备：按岗位维度生成问题清单与追问。

题目来自配置化题库（config/question_bank.yaml），可按岗位替换，
不依赖任何模型 API —— 同样的输入永远得到同样的输出，便于复跑验证。
"""

from __future__ import annotations

from typing import Any

from .config import PositionConfig


def _material_text(candidate: dict[str, Any], sources: tuple[str, ...] | None = None) -> str:
    """取候选人自述类字段的文本。

    必须与评估模块用同一套 evidence_sources：否则准备包说"命中 N 个信号"、
    评估却说"没有可引用原文"，两处口径不一致会让人无法判断该补什么材料。
    """
    parts: list[str] = []
    materials = candidate.get("materials") or {}
    for key, value in materials.items():
        if sources is not None and key not in sources:
            continue
        parts.append(_flatten(value))
    return "\n".join(p for p in parts if p)


def _flatten(node: Any) -> str:
    if isinstance(node, dict):
        return "\n".join(_flatten(v) for v in node.values())
    if isinstance(node, list):
        return "\n".join(_flatten(v) for v in node)
    if isinstance(node, str):
        return node
    return str(node) if node is not None else ""


def build_prep_kit(config: PositionConfig, candidate: dict[str, Any], per_dimension: int = 2) -> dict[str, Any]:
    """产出面试准备包：每个维度 2 道题 + 针对材料信号的追问。"""
    text = _material_text(candidate, sources=config.evidence_sources).lower()
    sections: list[dict[str, Any]] = []

    for dim in config.dimensions:
        bank = list(config.question_bank.get(dim.key, []))
        if not bank:
            continue
        picked = bank[:per_dimension]
        matched_signals = [s for s in dim.signals if s in text]
        followups: list[str] = []
        for signal in matched_signals[:2]:
            followups.append(
                f"材料里提到「{signal}」，请结合一个具体项目说明当时的取舍与结果。"
            )
        if not matched_signals:
            followups.append(
                "材料中未出现本维度的直接依据，请让候选人现场举例，并记录原话以便后续核对。"
            )
        sections.append(
            {
                "dimension": dim.key,
                "label": dim.label,
                "look_for": dim.look_for,
                "questions": picked,
                "followups": followups,
                "material_signals": matched_signals,
            }
        )

    return {
        "candidate_ref": candidate.get("candidate_ref"),
        "position": config.position,
        "position_title": config.title,
        "sections": sections,
        "note": "问题清单仅供面试官参考；评分与最终决定不由此模块产出。",
    }
