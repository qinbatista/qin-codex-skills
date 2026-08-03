<div align="center">

# 🚀 Auto Best Model

**专用于 Codex · 每个任务评分 · 先完成主任务 · 再用强制 Ending 证明结果**

[English](./README.md)

已保存的最高版本家族质量梯级 · 只有你主动要求本地模型更新时才刷新

0–24 分的小型低风险编辑优先 Spark-low · 更大任务使用已保存的质量梯级

</div>

## 🔄 核心流程

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/core-flow-zh-mobile.svg">
  <img src="./management-skill/assets/readme/core-flow-zh.svg" alt="核心流程：先评分并完成主任务，再为独立真实检查运行强制评分 Ending Task">
</picture>

## ✅ 先完成主任务，再执行强制真实验证

这是整个生命周期最重要的结构规则：

1. **每个提交先按 0–100 评分，再完成用户要求的工作**，并运行与实现相称的基础检查。
2. **立即返回已完成结果。** 不让用户被验证、轮询或修复流程卡住。
3. **每个结果之后，每个独立真实检查都在当前准确的已保存项目中另开一个独立评分并选模的 `End Task-<任务名>-<检查>`。** 通过规范项目根解析项目，并要求真实 project/local task 回执。
4. **每个 Ending 必须执行分配的真实检查，所有必需检查都要 PASS。** PASS/FAIL/BLOCKED task 都保持可见，并报告阶段难度与模型、尝试次数、一次过/重试通过、模型适配度、下一模型路线和 Obsidian 记录链接/状态。FAIL 会在同一项目建立 Fix Task，再由全新的 End Task 重跑；最多修复三次。End/Fix task 永不自动归档或删除。

主工作与 Ending 验证刻意使用不同任务会话。文字总结不算验证；重型修改必须用对应的真实测试、API 证据、build、render 或视觉检查证明。

## ⚡ 模型与私有学习

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/model-router-mobile.svg">
  <img src="./management-skill/assets/readme/model-router.svg" alt="任务策略质量梯级：按 receipt 证据保留、降级或升级一个档位">
</picture>

- **入口感知启动：** 用步骤能力 fingerprint 与难度历史选择最低正确档。Sol/高入口可向下降；Luna-max/更低入口可向上升。没有匹配历史时从不高于入口冷启动；0–24 分的小型低风险编辑仍先试 Spark-low。
- **学习：** receipt 有效的 Real PASS 保留当前档；两次匹配 PASS 才可向下降一级；质量失败向上升一级。失败后恢复成功的强档会被下一次精确匹配直接复用；实现与本地测试分别记忆。
- **操作故障：** 零结果故障只允许一次更强 fallback，不把它当质量失败学习。
- **Schedule：** 复合任务拆成可量化、责任明确的步骤并逐步选模；两到三个独立只读 source 先做成本准入，有依赖的多文件工作使用一个上下文 producer。
- **记忆：** Model Switch 与原生类别链接按项目 → Model Switch → 类别 → 共享类别保存每个终态 Ending；不读完整历史，也不用 JSON sidecar。receipt 结果可调整路线，无 receipt 的已知 assignment 只做可见观察，不参与自动升降级。

## 规则

- **Producer：** 显示分数、band、entry/selected；复用最低正确档。两次 PASS 降级；质量 FAIL 升级。
- **Prompt：** 可复用 Prompt 和持久 AI 指令加载 Prompt Skill。
- **路由：** 只有明确要求或当前端到端证据成立时才委派。
- **交付：** 先完成并返回主任务结果，再进行后台验证。
- **验证：** 每个独立检查使用评分、选模 End Task；全部 PASS。FAIL → Fix Task → 全新 End Task，最多三次。
- **文件：** 修改前回溯项目/模块/文件历史；修改后记录已验证结果。
- **记忆：** 修改历史用本地 JSONL；模型学习走原生类别链接，项目/任务等保持为字段。
- **模型：** 使用已保存梯级；主动本地更新时选择最高数字 GPT 家族；符合条件的小编辑优先 Spark-low；缓存不可用就保留原列表。
- **隐私：** secret、原始 Prompt/结果、receipt、ledger、cache 和临时文件留在本地。

## 📊 真实自适应 Benchmark：先完成，再后台验证

当前冻结 v47 比较：**无 Skill** 固定使用 `gpt-5.6-sol | ultra`；**有 Skill** 从 `gpt-5.6-luna | max` 进入，再按冻结历史逐步骤选模。主指标从正确路由已经冻结后开始：计入选中的 producer/graph 执行；入口匹配、controller、校准失败、retry/fallback/repair 和 Ending 全部单列。

<picture><source media="(max-width: 600px)" srcset="./management-skill/assets/readme/model-benchmark-example-mobile.svg"><img src="./management-skill/assets/readme/model-benchmark-example.svg" alt="当前 Direct 与 Auto 基准：所有结果和 Ending 通过；总体稳定执行时间和 token 降低，同时保留简单和中等档退化"></picture>

**6 组 A/B · 12 次运行 · 12/12 精确结果与 12/12 Ending PASS · 3/3 Sol 入口路由探针 PASS · 0 retry/fallback/repair**

| 档位 | Direct 稳定 token | Auto 稳定 token | 节省 | Direct 稳定执行 | Auto 稳定执行 | 节省 |
|---|---:|---:|---:|---:|---:|---:|
| 简单 | 32,654 | 93,448 | -186.176% | 22.896s | 17.561s | +23.301% |
| 中等 | 49,451 | 91,398 | -84.825% | 27.676s | 28.057s | -1.377% |
| 复杂 | 538,903 | 273,442 | **+49.260%** | 67.047s | 45.481s | **+32.165%** |
| **总体** | **621,008** | **458,288** | **+26.203%** | **117.619s** | **91.099s** | **+22.547%** |

**实测结论：正确率/证据 PASS；冻结路由后的总体性能 PASS。** 稳定执行节省 26.520 秒和 162,720 logical token。实际首结果时间更慢（`117.619s → 211.145s`），因为 120.046 秒的路由/controller 工作按定义不计入稳定态节省，并且单独公开。简单和中等档的 token 退化仍然保留；这只是本组冻结任务的证据，不是普遍结论或计费价格结论。

[查看精确 v47 报告。](./task-analyze-skill/TEST_AND_BENCHMARK.md) · [打开脱敏 benchmark 证据。](./task-analyze-skill/assets/model-routing-benchmark-example.json)

## 🧩 八个公开 Skill

- [`Task Analyze`](./task-analyze-skill/SKILL.md) — 路由策略、benchmark 和准入。
- [`Workflow`](./workflow-skill/SKILL.md) — 执行已准入的锁定路线。
- [`Prompt`](./prompt-skill/SKILL.md) — 可复用 Prompt 和持久 AI 指令入口。
- [`Code`](./code-skill/SKILL.md) — Python、C#、Unity C# 和已注册代码域。
- [`Project Memory`](./project-memory-skill/SKILL.md) — 项目/模块/文件回溯和验证记录。
- [`Verify`](./verify-skill/SKILL.md) — 结果之后的 Real Verify 和回归证据。
- [`Optimization`](./optimization-skill/SKILL.md) — 把稳定重复流程变成工具。
- [`Management`](./management-skill/SKILL.md) — 私有 profile 和公共镜像管理。

## 🛠️ 已注册执行域

- `general` · general · `workflow-skill` · active · Spark schedule: no · [rules](./task-analyze-skill/references/model-selection.md)
- `python` · code · `code-skill` · active · Spark schedule: source-eligible · [rules](./code-skill/references/python-rules.md)
- `csharp` · code · `code-skill` · active · Spark schedule: source-eligible · [rules](./code-skill/references/csharp-rules.md)
- `unity_csharp` · code · `code-skill` · active · Spark schedule: source-eligible · [rules](./code-skill/references/unity-csharp-rules.md)
- `code_unspecified` · code · `code-skill` · history-only · Spark schedule: source-eligible · [rules](./code-skill/references/spark-small-code.md)

## 安装

1. 把八个 Skill 文件夹放进 `~/.codex/skills/`。
2. 将 [`global-agents-entry-rule.md`](./task-analyze-skill/assets/global-agents-entry-rule.md) 合并到 `~/.codex/AGENTS.md`。
3. 正常启动 Codex；不安装生命周期 hook。

**隐私：** 镜像排除 auth、secret、私有 ledger、路由历史、cache、原始 Prompt/结果、receipt 和临时文件；每次发布都运行安全检查。

**镜像：** `qin-codex-skills` · `auto-best-model`
