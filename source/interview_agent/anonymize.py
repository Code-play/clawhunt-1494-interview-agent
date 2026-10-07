"""脱敏守卫：候选材料在进入流程前必须已去除个人信息。

本单交付要求写明「只能使用获授权或脱敏的资料」。把它做成代码强制，
而不是写在 README 里靠自觉：任何禁用字段出现在材料里就直接拒绝处理。
"""

from __future__ import annotations

import re
from typing import Any, Iterable

from .schema import AnonymizationError

# 禁用字段名（大小写不敏感、允许前后缀）
FORBIDDEN_KEYS: tuple[str, ...] = (
    "name",
    "full_name",
    "real_name",
    "email",
    "mail",
    "phone",
    "mobile",
    "tel",
    "wechat",
    "weixin",
    "qq",
    "id_card",
    "idcard",
    "passport",
    "address",
    "school",
    "university",
    "college",
    "employer",
    "company",
    "organization",
    "photo",
    "avatar",
    "birthday",
    "birth",
)

# 文本里的邮箱 / 手机号 / 身份证号特征
_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("email", re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")),
    ("cn_mobile", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    ("cn_id", re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")),
)


def _iter_items(node: Any, path: str = "$") -> Iterable[tuple[str, Any]]:
    if isinstance(node, dict):
        for k, v in node.items():
            yield f"{path}.{k}", k
            yield from _iter_items(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _iter_items(v, f"{path}[{i}]")
    else:
        yield path, node


def assert_anonymized(candidate: dict[str, Any]) -> None:
    """材料里出现禁用字段或可识别信息时抛 AnonymizationError。"""
    problems: list[str] = []

    for path, key in _iter_items(candidate):
        if not isinstance(key, str):
            continue
        if path.endswith(str(key)) and isinstance(key, str):
            low = key.lower()
            if any(low == f or low.endswith("_" + f) or low.startswith(f + "_") for f in FORBIDDEN_KEYS):
                problems.append(f"禁用字段 {path}（命中 PII 规则 {low}）")

    text = _flatten_text(candidate)
    for label, pattern in _PATTERNS:
        m = pattern.search(text)
        if m:
            problems.append(f"文本中出现疑似{label}：{m.group(0)[:6]}***")

    if problems:
        raise AnonymizationError("候选材料未脱敏，拒绝处理： " + "；".join(problems))


def _flatten_text(node: Any) -> str:
    parts: list[str] = []
    if isinstance(node, dict):
        for v in node.values():
            parts.append(_flatten_text(v))
    elif isinstance(node, list):
        for v in node:
            parts.append(_flatten_text(v))
    elif isinstance(node, str):
        parts.append(node)
    return "\n".join(p for p in parts if p)
