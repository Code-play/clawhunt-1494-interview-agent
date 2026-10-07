# 面试 Agent（面试准备 + 评估辅助，人工决策边界版）

订单 **#1494**「企业 Agent 系统 07/50｜面试 Agent」交付物。

面试官手上有一份候选人材料时，这个工具做两件事：

1. **面试准备** —— 按岗位维度生成面试题，并根据材料里**真实命中**的信号生成追问；
2. **评估辅助** —— 产出带原文引用的评估；引用不到原文的维度**拒绝打分**。

同时立三条硬规矩：

| 规矩 | 落地方式 |
|---|---|
| 每道题要有来由 | 题目来自配置化题库，追问由材料命中的信号驱动 |
| 每个分数要有原句 | 分数必须挂 `Evidence(quote, source_field)`，引用不到就不给分 |
| 最终决定只能人写 | `final_decision` 无机器人写入口；以 agent 身份写入抛 `HumanDecisionViolation` |

**不依赖任何模型 API**：全流程确定性，同样输入永远同样输出，买家可一键复跑比对。
第三方依赖只有 `pyyaml`。

## 目录

```
interview_agent/        代码
  schema.py             数据模型：证据必须带原文；最终决定是不可由机器人写入的封存字段
  config.py             YAML 配置加载与校验（岗位 / rubric / 阈值 / 硬性规则 / 证据来源）
  anonymize.py          脱敏守卫：出现个人信息字段或邮箱手机号即拒绝处理
  questions.py          面试准备：按维度出题 + 依据材料信号生成追问
  assess.py             带依据评估：无引用不打分、覆盖率不足不出结论、硬规则否决
  human_gate.py         人工决策边界：最终决定的唯一入口 + 审计
  cli.py                命令行入口
config/
  positions/backend_engineer.yaml   岗位配置（维度 / 权重 / 信号词 / 硬性规则）
  question_bank.yaml                题库（按维度）
  guard.yaml                        阈值（覆盖率下限 / 最小引用长度 / 边界分）
samples/                三份合成脱敏样例，覆盖三条判定路径
tests/                  21 个单元测试（标准库 unittest，无需额外依赖）
verify/
  run_verification.py   一键复跑，生成验证记录
  verification_record.md   验证记录（输入 / 原始输出 / 断言结论）
  verification_result.json 机器可读的断言结果
```

## 安装

```bash
pip install pyyaml
```

Python 3.10+（开发环境 3.11）。

## 使用

### 1. 校验材料是否已脱敏

```bash
python -m interview_agent check-anonymization --candidate samples/candidate_advance.json
```

未通过会以退出码 2 结束，并指出命中的字段或文本特征。

### 2. 出面试题

```bash
python -m interview_agent prepare --position backend_engineer --candidate samples/candidate_advance.json
```

输出每个维度的题目、材料命中信号、以及针对信号的追问。

### 3. 出评估建议

```bash
python -m interview_agent assess --position backend_engineer --candidate samples/candidate_advance.json
```

输出 `recommendation` / `confidence` / `evidence_coverage` / 每维度分数与原文引用 /
被拒绝打分的维度 / 命中的硬性规则。注意 `final_decision` 恒为 `null`。

### 4. 演示人工决策边界

```bash
python -m interview_agent assess --position backend_engineer --candidate samples/candidate_advance.json \
  --gate-demo --reviewer HUMAN-01 --decision hold --note "要求补充协作事例"
```

先让机器人尝试写最终决定（被拒绝，日志打到 stderr），再由人类评审写入并留审计。

### 5. 一键复跑全部验证

```bash
python verify/run_verification.py
```

全部断言通过时退出码为 0，并刷新 `verify/verification_record.md` 与 `verification_result.json`。

### 6. 单元测试

```bash
python -m unittest discover -s tests -t .
```

## 换岗位 / 调阈值

- **换岗位**：复制 `config/positions/backend_engineer.yaml` 改 `dimensions` 的 `signals` 与
  `hard_rules`，再在 `config/question_bank.yaml` 里补同名维度的题目。改配置不改代码。
- **调阈值**：`config/guard.yaml` 的 `min_evidence_coverage`（证据覆盖率下限，
  低于此值不出结论，转人工补材料）、`min_quote_chars`（引用最小长度）、
  `borderline_confidence`（不合格下限）。
- **证据来源**：岗位配置里的 `evidence_sources` 决定哪些材料字段可作为证据。
  默认 `resume` / `qa_transcript` —— **面试官自己的备注不作为证据来源**，
  否则等于用"面试官的判断"证明"面试官的判断"。

## 三条判定路径（`samples/`）

| 样例 | 证据覆盖率 | 机器人建议 | 演示的机制 |
|---|---|---|---|
| `candidate_advance.json` | 100% | `advance` | 材料齐备，给出正向建议（仍需人工确认） |
| `candidate_needs_review.json` | 55% | `needs_review` | 低于 60% 阈值，3 个维度拒绝打分，转人工补材料 |
| `candidate_rule_reject.json` | 75% | `not_recommended` | 命中硬性规则（经验下限 3 年，实际 2 年） |

## 运行注意事项

- **直接用 `python` 运行，不要用 `conda run`**：`conda run` 会把子进程输出用自己的
  GBK 编码重新打印，含中文时表现为 `UnicodeEncodeError` + 退出码 1（是 conda 的问题，
  不是本工具的问题）。若必须用 `conda run`，先设 `PYTHONIOENCODING=utf-8`。
- 本工具不联网、不调用任何模型 API。

## 范围与排除

- 仅使用授权或脱敏材料；材料含个人信息即被拒绝处理。
- 模型 API、云资源、训练算力等第三方费用不在本单范围内（本工具也不需要）。
- 业务答案的最终确认由授权人员完成。
