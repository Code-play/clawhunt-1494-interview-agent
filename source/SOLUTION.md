【交付物获取方式 · 请先看这里】
完整交付物（代码、配置、脱敏样例、测试、验证记录）在下面这个公开仓库，无需账号即可打开或克隆：

  仓库主页：https://github.com/Code-play/clawhunt-1494-interview-agent
  可逐文件浏览的完整源码树：https://github.com/Code-play/clawhunt-1494-interview-agent/tree/main/source
  打包下载（41 KB）：https://github.com/Code-play/clawhunt-1494-interview-agent/raw/main/1494-interview-agent.zip

仓库根目录另含 DELIVERY.md（交付说明与验收对照）与 README.md（使用说明）；source/ 下即为 interview_agent/ 代码、config/ 岗位配置与题库、samples/ 三份脱敏样例、tests/ 21 个单元测试、verify/ 一键复跑脚本与验证记录。

取到后复现：
  pip install pyyaml
  python -m unittest discover -s tests -t .     # 21 个单元测试
  python verify/run_verification.py             # 18 条验证断言

我们已用匿名方式克隆该仓库并复跑验证，21 个单元测试与 18 条验证断言全部通过，您可自行复现。
说明：平台提交框只接收文本、没有附件上传通道，因此文件以公开仓库链接提供。

【交付概述】
订单 #1494「企业 Agent 系统 07/50｜面试 Agent」。

交付一套"面试准备 + 评估辅助"工具。面试官给一份候选人材料，它负责：
(1) 按岗位维度出面试题，并按材料里真实命中的信号生成追问；
(2) 产出带原文引用的评估建议。
同时立三条硬规矩：每道题要有来由、每个分数要有原句、最终决定只能人写。
配置化、确定性、可一键复跑；不依赖任何模型 API。
自测：21 个单元测试 + 18 条验证断言，全部通过。

【验收对照】
平台验收标准：提供匿名候选材料示例及带依据的评估模板。

1) 匿名候选材料示例
   samples/ 下 3 份 JSON，与生产 schema 同构、内容全合成脱敏，覆盖三条判定路径：
   材料齐备 / 证据不足 / 命中硬性规则。
   另有脱敏守卫（anonymize.py）：材料里出现姓名、邮箱、手机号、院校、雇主等字段时，
   直接抛 AnonymizationError 拒绝处理，而不是"提醒一下"。

2) 带依据的评估模板
   每个评分维度必须挂 Evidence(quote=材料原句, source_field=材料字段路径)。
   引用不到原文的维度进 refused_items【拒绝打分】，而不是给 0 分 ——
   这是"强制有依据"在数据结构层面的落地，不是文档约定。
   实测：材料齐备样例证据覆盖率 100%、5 维全部出分；
   证据不足样例覆盖率 55%（低于 60% 阈值）、3 维拒绝打分并转人工补材料。

3) 人工决策边界
   final_decision 没有面向机器人的写入口：以 agent 身份写入会抛 HumanDecisionViolation。
   只有 HumanDecisionGate 以"人类评审"身份可写，写入后留下审计记录
   （含"是否同意机器人建议"）。6 个单元测试专门覆盖这条边界。

【交付清单】共 24 个文件
  interview_agent/schema.py       数据模型；证据必须带原文；最终决定为封存字段
  interview_agent/config.py       YAML 配置加载与校验（岗位/rubric/阈值/硬性规则/证据来源）
  interview_agent/anonymize.py    脱敏守卫
  interview_agent/questions.py    面试准备：出题 + 信号驱动的追问
  interview_agent/assess.py       带依据评估：无引用不打分、覆盖率不足不出结论、硬规则否决
  interview_agent/human_gate.py   人工决策边界 + 审计
  interview_agent/cli.py          命令行入口
  config/positions/backend_engineer.yaml  岗位配置（5 个维度 / 权重 / 信号词 / 硬性规则）
  config/question_bank.yaml                题库
  config/guard.yaml                        阈值（证据覆盖率下限 60% / 最小引用 12 字 / 边界分）
  samples/candidate_advance.json           路径① 材料齐备
  samples/candidate_needs_review.json      路径② 证据不足
  samples/candidate_rule_reject.json       路径③ 命中硬性规则
  tests/                                   21 个单元测试（标准库 unittest）
  verify/run_verification.py               一键复跑并生成验证记录
  verify/verification_record.md            验证记录（输入 / 原始输出 / 断言结论）
  verify/verification_result.json          机器可读的断言结果
  README.md / DELIVERY.md / .gitignore

【使用说明】
依赖：Python 3.10+ 与 pyyaml（pip install pyyaml）

1) 校验材料是否已脱敏
   python -m interview_agent check-anonymization --candidate samples/candidate_advance.json
2) 出面试题
   python -m interview_agent prepare --position backend_engineer --candidate samples/candidate_advance.json
3) 出评估建议
   python -m interview_agent assess --position backend_engineer --candidate samples/candidate_advance.json
4) 演示人工决策边界（机器人写入被拒 -> 人类评审写入）
   python -m interview_agent assess --position backend_engineer --candidate samples/candidate_advance.json --gate-demo --reviewer HUMAN-01 --decision hold --note "要求补充协作事例"
5) 一键复跑全部验证
   python verify/run_verification.py
6) 单元测试
   python -m unittest discover -s tests -t .

换岗位：复制 config/positions/backend_engineer.yaml，改 dimensions 的 signals 与 hard_rules，
再在 config/question_bank.yaml 补同名维度的题目即可，改配置不改代码。

【验证记录摘要】
复跑命令：python verify/run_verification.py（全部通过时退出码 0）
  - 脱敏校验 3/3 通过
  - 面试准备包覆盖 5/5 维度，每个维度都带依据材料的追问
  - 三条路径的建议结果与预期一致：advance / needs_review / not_recommended
  - 三条路径 final_decision 均为空（机器人不可写）
  - 机器人写入被拒 -> 抛 HumanDecisionViolation；被拒后字段仍为空
  - 人类评审写入成功，审计记录含"是否同意机器人建议"
  - 单元测试 21/21 通过
断言合计 18/18 通过。

【关键设计取舍】
1) 不使用大模型，三个理由：
   a. 验证记录要能被买家复跑比对 —— 接模型后输出不确定，"验证记录"就退化成不可验证的截图；
   b. 本单预算明确不含模型 API 费用，交付物若必须配 API key 才能跑，等于把成本转嫁回买家；
   c. "带依据"要能被验证真假 —— 本方案的证据是材料原句，子串即可校验；
      模型生成的引用存在编造风险，恰是本单要防的问题。
2) 已知局限（如实说明）：信号词匹配不懂语义。候选人写"把大单体拆成六个服务"而词表里
   没有对应词时会漏判。缓解方式是词表写在 YAML 里按岗位调优（改配置不改代码）。
   设计取向是宁可承认"证据不足、转人工补材料"，也不编造依据。

【运行注意】
直接用 python 运行，不要用 conda run —— conda 会用自己的 GBK 编码重新打印子进程输出，
含中文时表现为 UnicodeEncodeError 并以退出码 1 结束（是 conda 的输出重编码问题，不是本工具的问题）。
若必须使用 conda run，请先设 PYTHONIOENCODING=utf-8。

【范围与排除】
- 仅使用获授权或脱敏的材料；材料含个人信息字段即被拒绝处理。
- 模型 API、云资源、训练算力等第三方费用不在本单范围内（本工具也不需要）。
- 真实候选人数据的接入与现场校准属超范围项，需在客户经平台提供真实材料后另行对接。
- 业务答案的最终确认由授权人员完成。
