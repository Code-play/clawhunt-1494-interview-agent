# 验证记录 · 面试 Agent（订单 #1494）

生成时间：2026-10-07T14:11:33.920806+00:00
岗位配置：backend_engineer；阈值：证据覆盖率 >= 0.6、引用 >= 12 字

复跑命令：`python verify/run_verification.py`

## 1. 脱敏校验（材料含个人信息即拒绝处理）

- `candidate_advance.json`：通过
- `candidate_needs_review.json`：通过
- `candidate_rule_reject.json`：通过

## 2. 面试准备包（每个维度出题 + 依据材料生成追问）

- **系统设计**：2 题，命中材料信号 5 个，追问 2 条
  - 例题：请挑一个你主导过的高并发场景，说明当时的容量估算、瓶颈定位和最终架构取舍。
- **编码深度**：2 题，命中材料信号 6 个，追问 2 条
  - 例题：挑一段你重构过的核心代码，说明重构前后复杂度或可维护性的具体变化。
- **数据与存储**：2 题，命中材料信号 7 个，追问 2 条
  - 例题：你设计过的索引/分片方案解决了什么查询问题？代价是什么？
- **协作与推进**：2 题，命中材料信号 5 个，追问 2 条
  - 例题：讲一次你跨团队推动落地的经历：阻力来自哪里，你怎么对齐的？
- **责任与复盘**：2 题，命中材料信号 6 个，追问 2 条
  - 例题：讲一次你负责的线上事故：你当时的位置、排查路径、根因和后续改进。

## 3. 带依据评估（无原文引用不给分）

### candidate_advance.json —— 材料齐备，建议进入下一轮（仍待人工确认）
- 建议：`advance`；置信度 0.821；证据覆盖率 100%；需人工复核：True
  - 系统设计：71.43 分（权重 0.3）依据 `materials.resume.highlights[0]`：「主导订单域从单体拆分为六个微服务，按业务边界重划数据归属，拆分后发布相互阻塞的问题消失」
  - 编码深度：85.71 分（权重 0.25）依据 `materials.resume.highlights[2]`：「用 Python 与 Go 重写结算批处理，重构后核心路径复杂度下降，单元测试覆盖率从 41% 提升到 78%，性能优化」
  - 数据与存储：100.0 分（权重 0.2）依据 `materials.qa_transcript[0].a`：「结算表一度单表两亿行，查询走不到索引」
  - 协作与推进：71.43 分（权重 0.15）依据 `materials.resume.highlights[3]`：「跨团队推动过结算与财务的口径对齐，带人方面带过两名同学，排期由我统一协调」
  - 责任与复盘：85.71 分（权重 0.1）依据 `materials.qa_transcript[2].a`：「事后我主持了复盘并推动上线前的容量基线检查」
  - 备注：加权得分 82.1，建议进入下一轮；最终决定由人工写入。
  - 备注：系统只产出建议；final_decision 只能由人类评审写入。

### candidate_needs_review.json —— 证据不足，转人工补材料
- 建议：`needs_review`；置信度 0.193；证据覆盖率 55%；需人工复核：True
  - 系统设计：28.57 分（权重 0.3）依据 `materials.resume.summary`：「四年后端开发，做过服务拆分与接口性能优化，材料以项目片段为主」
  - 编码深度：42.86 分（权重 0.25）依据 `materials.resume.highlights[1]`：「用 Go 重写日志采集组件，重构后内存占用下降明显」
  - 数据与存储：**拒绝打分** —— 材料中找不到可引用的原文（或引用短于最小长度），拒绝为该维度打分
  - 协作与推进：**拒绝打分** —— 材料中找不到可引用的原文（或引用短于最小长度），拒绝为该维度打分
  - 责任与复盘：**拒绝打分** —— 材料中找不到可引用的原文（或引用短于最小长度），拒绝为该维度打分
  - 备注：证据覆盖率 55% 低于阈值 60%，不足以给出结论，转人工补充材料。
  - 备注：系统只产出建议；final_decision 只能由人类评审写入。

### candidate_rule_reject.json —— 命中硬性规则（经验下限）
- 建议：`not_recommended`；置信度 0.257；证据覆盖率 75%；需人工复核：True
- 命中硬性规则：`min_years` declared.years_experience=2 低于要求 3
  - 系统设计：42.86 分（权重 0.3）依据 `materials.resume.summary`：「两年后端开发，参与过微服务拆分与线上稳定性治理」
  - 编码深度：28.57 分（权重 0.25）依据 `materials.resume.highlights[1]`：「用 Python 补了回调幂等的单元测试，覆盖重复投递与乱序两类场景」
  - 数据与存储：28.57 分（权重 0.2）依据 `materials.qa_transcript[0].a`：「先看慢查询日志和索引命中情况，再看缓存是否穿透，最后确认是不是锁等待」
  - 协作与推进：**拒绝打分** —— 材料中找不到可引用的原文（或引用短于最小长度），拒绝为该维度打分
  - 责任与复盘：**拒绝打分** —— 材料中找不到可引用的原文（或引用短于最小长度），拒绝为该维度打分
  - 备注：命中硬性规则，建议不通过；仍须人工确认后才生效。
  - 备注：系统只产出建议；final_decision 只能由人类评审写入。

## 4. 人工决策边界（代码层强制，非流程约定）

- 机器人写入最终决定：**被拒绝** —— 最终录用决定只能由人类评审写入；机器人只能输出 recommendation
- 被拒后 `final_decision`：None
- 人类评审写入：`{'decision': 'hold', 'note': '面试官要求补充协作事例', 'reviewer': 'HUMAN-01'}`
- 审计记录：[{"at": "2026-10-07T14:11:33.923801+00:00", "candidate_ref": "CAND-0001", "reviewer": "HUMAN-01", "decision": "hold", "note": "面试官要求补充协作事例", "bot_recommendation": "advance", "agreed_with_bot": false}]

## 5. 单元测试

```
Ran 21 tests in 0.043s
```

## 结论

- 断言总数：18；通过：18；失败：0
- 结果：**全部通过**

| 断言 | 预期 | 实际 | 结果 |
|---|---|---|---|
| 脱敏校验 candidate_advance.json | 通过 | 通过 | 通过 |
| 脱敏校验 candidate_needs_review.json | 通过 | 通过 | 通过 |
| 脱敏校验 candidate_rule_reject.json | 通过 | 通过 | 通过 |
| 准备包覆盖全部维度 | 5 | 5 | 通过 |
| candidate_advance.json 建议结果 | advance | advance | 通过 |
| candidate_advance.json 最终决定为空（机器人不写） | None | None | 通过 |
| candidate_advance.json 标注需人工复核 | True | True | 通过 |
| candidate_needs_review.json 建议结果 | needs_review | needs_review | 通过 |
| candidate_needs_review.json 最终决定为空（机器人不写） | None | None | 通过 |
| candidate_needs_review.json 标注需人工复核 | True | True | 通过 |
| candidate_rule_reject.json 建议结果 | not_recommended | not_recommended | 通过 |
| candidate_rule_reject.json 最终决定为空（机器人不写） | None | None | 通过 |
| candidate_rule_reject.json 标注需人工复核 | True | True | 通过 |
| 机器人写最终决定被拒 | HumanDecisionViolation | True | 通过 |
| 被拒后决定字段仍为空 | None | None | 通过 |
| 人类评审写入成功 | hold | hold | 通过 |
| 审计记录含是否同意建议 | True | True | 通过 |
| 单元测试全部通过 | returncode 0 | 0 | 通过 |