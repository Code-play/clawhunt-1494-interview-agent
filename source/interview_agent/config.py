"""配置加载与校验（岗位维度、rubric、阈值、硬性规则）。

全部走 YAML，改配置即可换岗位复用，无需改代码。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """配置缺失或非法。"""


@dataclass(frozen=True)
class Dimension:
    key: str
    label: str
    weight: float
    signals: tuple[str, ...]
    look_for: str = ""


@dataclass(frozen=True)
class HardRule:
    key: str
    label: str
    field: str
    op: str
    value: Any


@dataclass(frozen=True)
class Guard:
    min_evidence_coverage: float
    min_quote_chars: int
    borderline_confidence: float


@dataclass(frozen=True)
class PositionConfig:
    position: str
    title: str
    dimensions: tuple[Dimension, ...]
    hard_rules: tuple[HardRule, ...]
    question_bank: dict[str, list[str]]
    evidence_sources: tuple[str, ...] = ("resume", "qa_transcript")

    def dimension(self, key: str) -> Dimension:
        for d in self.dimensions:
            if d.key == key:
                return d
        raise ConfigError(f"未知维度: {key}")


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ConfigError(f"配置文件不存在: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ConfigError(f"配置文件顶层必须是映射: {path}")
    return data


def load_position(config_dir: str | Path, position: str) -> PositionConfig:
    """载入一个岗位配置。"""
    config_dir = Path(config_dir)
    raw = _read_yaml(config_dir / "positions" / f"{position}.yaml")

    dims: list[Dimension] = []
    for item in raw.get("dimensions", []):
        for required in ("key", "label", "weight", "signals"):
            if required not in item:
                raise ConfigError(f"维度缺少字段 {required}: {item}")
        if not item["signals"]:
            raise ConfigError(f"维度 {item['key']} 的 signals 不能为空（否则永远无证据）")
        dims.append(
            Dimension(
                key=item["key"],
                label=item["label"],
                weight=float(item["weight"]),
                signals=tuple(str(s).lower() for s in item["signals"]),
                look_for=str(item.get("look_for", "")),
            )
        )
    if not dims:
        raise ConfigError("至少需要一个评分维度")

    total_weight = sum(d.weight for d in dims)
    if abs(total_weight - 1.0) > 1e-6:
        raise ConfigError(f"维度权重之和必须为 1.0，当前 {total_weight}")

    rules = tuple(
        HardRule(
            key=r["key"],
            label=r["label"],
            field=r["field"],
            op=r["op"],
            value=r["value"],
        )
        for r in raw.get("hard_rules", [])
    )

    bank_raw = _read_yaml(config_dir / "question_bank.yaml") if (config_dir / "question_bank.yaml").is_file() else {}
    bank = {str(k): [str(x) for x in v] for k, v in (bank_raw.get("by_dimension") or {}).items()}
    for d in dims:
        if d.key not in bank:
            raise ConfigError(f"题库缺少维度 {d.key} 的题目")

    sources = tuple(str(s) for s in raw.get("evidence_sources", ("resume", "qa_transcript")))
    if not sources:
        raise ConfigError("evidence_sources 不能为空")

    return PositionConfig(
        position=raw.get("position", position),
        title=str(raw.get("title", position)),
        dimensions=tuple(dims),
        hard_rules=rules,
        question_bank=bank,
        evidence_sources=sources,
    )


def load_guard(path: str | Path) -> Guard:
    raw = _read_yaml(Path(path))
    guard = raw.get("guard") or {}
    for key in ("min_evidence_coverage", "min_quote_chars", "borderline_confidence"):
        if key not in guard:
            raise ConfigError(f"guard 缺少 {key}")
    return Guard(
        min_evidence_coverage=float(guard["min_evidence_coverage"]),
        min_quote_chars=int(guard["min_quote_chars"]),
        borderline_confidence=float(guard["borderline_confidence"]),
    )


def load_candidate(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        raise ConfigError(f"候选材料不存在: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ConfigError("候选材料顶层必须是对象")
    return data
