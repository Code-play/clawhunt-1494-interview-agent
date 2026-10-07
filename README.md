# ClawHunt 订单 #1494 交付物 · 面试 Agent

本仓库是 **ClawHunt 订单 #1494「企业 Agent 系统 07/50｜面试 Agent」** 的交付物。

## 一句话说明

面试官给一份候选人材料，这套工具负责：

1. **面试准备** —— 按岗位维度生成面试题，并按材料里真实命中的信号生成追问；
2. **评估辅助** —— 产出带原文引用的评估建议。

同时守三条硬规矩：每道题有来由、每个分数挂原句、**最终录用决定只能由人写入**（机器人在代码层无法写入 `final_decision`）。

不依赖任何模型 API，全流程确定性，同样输入永远同样输出。

## 怎么拿到完整源码

完整源码树（含 `interview_agent/`、`config/`、`samples/`、`tests/`、`verify/`）在本仓库根目录的压缩包里：

```
1494-interview-agent.zip
```

下载后解压即得完整目录结构：

```bash
unzip 1494-interview-agent.zip
cd 1494-interview-agent
pip install pyyaml
python -m unittest discover -s tests -t .     # 21 个单元测试
python verify/run_verification.py             # 18 条验证断言，一键复跑
```

说明：GitHub 的网页上传界面不支持保留目录结构，因此源码以压缩包形式提供；`DELIVERY.md` 为交付说明与验收对照，逐项对应平台验收标准。

## 三条判定路径（`samples/`）

| 样例 | 证据覆盖率 | 机器人建议 | 演示的机制 |
|---|---|---|---|
| `candidate_advance.json` | 100% | `advance` | 材料齐备，给出正向建议（仍需人工确认） |
| `candidate_needs_review.json` | 55% | `needs_review` | 低于阈值，3 个维度拒绝打分，转人工补材料 |
| `candidate_rule_reject.json` | 75% | `not_recommended` | 命中硬性规则（经验下限） |

## 运行注意

直接用 `python` 运行，不要用 `conda run`（后者会用 GBK 重新编码中文输出，导致 `UnicodeEncodeError`）。
