"""面试准备与评估辅助 Bot（人工决策边界版）。

模块划分：
- schema      数据模型；最终决定字段在结构上不可由机器人写入
- config      YAML 配置加载与校验（岗位 / rubric / 阈值 / 硬性规则）
- anonymize   脱敏守卫：材料含个人信息即拒绝处理
- questions   面试准备：按维度出题 + 依据材料信号生成追问
- assess      带依据的评估：无原文引用就不给分
- human_gate  人工决策边界：最终决定的唯一入口
"""

from .assess import assess_candidate
from .config import Guard, PositionConfig, load_candidate, load_guard, load_position
from .human_gate import ALLOWED_DECISIONS, HumanDecisionGate
from .questions import build_prep_kit
from .schema import (
    ActorRole,
    AnonymizationError,
    Assessment,
    Evidence,
    HumanDecisionViolation,
)

__all__ = [
    "assess_candidate",
    "build_prep_kit",
    "load_position",
    "load_guard",
    "load_candidate",
    "PositionConfig",
    "Guard",
    "HumanDecisionGate",
    "ALLOWED_DECISIONS",
    "Assessment",
    "Evidence",
    "ActorRole",
    "AnonymizationError",
    "HumanDecisionViolation",
]

__version__ = "1.0.0"
