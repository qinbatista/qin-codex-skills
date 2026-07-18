<div align="center">

# 🚀 Auto Best Model

**专用于 Codex · 先完成并返回主任务 · 再由独立后台任务验证**

[English](./README.md)

已保存的最高版本家族质量梯级 · 只有你主动要求本地模型更新时才刷新

当前目录推导的优先生产模型：`gpt-5.3-codex-spark` · 简单=`low` · 复杂=`high`

</div>

## 🔄 核心流程

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/core-flow-zh-mobile.svg">
  <img src="./management-skill/assets/readme/core-flow-zh.svg" alt="核心流程：先完成并返回主任务，再启动独立且不阻塞的后台 Ending Task">
</picture>

## ✅ 先完成主任务，再后台验证

这是整个生命周期最重要的结构规则：

1. **主任务先完成用户要求的工作**，只运行与实现相称的本地基础检查。
2. **立即返回已完成结果。** 不让用户被验证、轮询或修复流程卡住。
3. **另开 `End Task-<任务名>` 独立 Codex 后台任务。** 它只读审计已有证据，绝不阻塞已经完成的主任务。
4. **Ending 只返回 PASS 或准确失败。** 不向用户提问、不等待、不轮询、不调用重型 API，也不在 Ending 内修复；失败后另开新的修复任务。

主工作与 Ending 验证刻意使用不同任务会话。“后台”表示主结果一返回，用户就能继续工作；它不表示跳过验证。

## ⚡ 模型与私有学习

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/model-router-mobile.svg">
  <img src="./management-skill/assets/readme/model-router.svg" alt="目录推导优先生产模型与完整质量梯级，并在私有 Obsidian 中学习">
</picture>

- **优先：** 合格文字/代码使用自适应目录优先生产模型：简单 `low`，复杂 `high`；精确只读、图像/混合和纯工具任务保持 inline。
- **操作故障：** 零结果、零 token 时，使用 Obsidian 当前上下文选择的质量模型档位。
- **质量故障：** 先返回已完成结果；独立后台 Ending 记录 receipt 对应的失败，再由新的修复任务使用不同验证者。
- **学习：** Ending 结果更新宽泛项目/Skills `Model Switch.md` 页面；project/task/module/file/symbol 仅是字段，不创建层级笔记。

## 规则

- **Producer：** 合格文字/代码用自适应目录优先生产模型；精确只读、图像/混合和纯工具任务保持 inline。
- **Prompt：** 可复用 Prompt 和持久 AI 指令加载 Prompt Skill。
- **路由：** 只有明确要求或当前端到端证据成立时才委派。
- **交付：** 先完成并返回主任务结果，再进行后台验证。
- **验证：** 交付后另开不阻塞的 `End Task-<任务名>`；first-result 不包含它。
- **文件：** 修改前回溯项目/模块/文件历史；修改后记录已验证结果。
- **记忆：** 修改历史用本地 JSONL（可投影 Obsidian）；私有学习用宽泛项目/Skills `Model Switch.md`，仅字段，不建层级笔记。
- **模型：** 普通任务只读已保存 JSON；主动本地更新时选择最高数字 GPT 家族，缓存不可用就保留原列表。
- **隐私：** secret、原始 Prompt/结果、receipt、ledger、cache 和临时文件留在本地。

## 📊 真实自适应 Benchmark：先完成，再后台验证

两边都从 `gpt-5.6-sol | ultra` 开始。**无 Skill** 一直使用 Sol-ultra，完成主任务后停止：验证 token/时间都是 **0**。**有 Skill** 通过 receipt 证明的 producer 或 schedule 返回完整主结果，再启动独立只读 Ending 任务；Ending 永不阻塞交付。

![六组真实 A/B：分别显示无 Skill、Auto 控制器、自适应 producer 或 schedule，以及仅属于 Auto 的条纹 Ending 成本](./management-skill/assets/readme/lifecycle-skill-benchmark.svg)

| 档位 | Auto 路线 | 无 Skill token | Auto 控制器 | Auto producer | Auto 前台 | Token 结果 | 无 Skill 时间 | Auto 时间 | 时间结果 | Auto Ending |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 简单 · 4 tests | Spark-low | 291,499 | 179,430 | 252,534 | 431,964 | 多 48.187% | 134.659s | 100.856s | **快 25.103%** | 92,114 / 82.598s |
| 中等 · 6 tests | Spark-high | 464,397 | 176,040 | 467,556 | 643,596 | 多 38.587% | 167.086s | 145.307s | **快 13.035%** | 92,658 / 39.845s |
| 复杂 · 3 sources | 3× Spark-low → Terra-medium | 508,084 | 137,152 | 445,040 | 582,192 | 多 14.586% | 158.780s | 107.498s | **快 32.298%** | 119,322 / 66.184s |
| **全部 6 组** | receipt 证明的 graph | **1,263,980** | **492,622** | **1,165,130** | **1,657,752** | **多 31.153%** | **460.525s** | **353.661s** | **快 23.205%** | **304,094 / 188.627s** |

**模型切换与 schedule 确实工作。** Producer 单独看整体少 **7.821% token**；复杂 graph 单独看少 **12.408% token**，记录的关键路径快 **72.583%**。但 Sol 控制器又增加 492,622 token，因此真实的前台 token 策略结论是 **FAIL**，不能伪装成胜利。顺序加上 Ending 后，Auto 多 **55.212% token**、慢 **17.754%**；但用户早已收到主结果。

**正确性：** 12/12 主结果完全正确；所有本地 Mini Test 通过；6/6 独立 Ending 返回 PASS。每档两组只用于确认本次代码结构修改，不代表六组性能准入。Logical token 是运行用量，不等于计费 token。

[查看完整 Benchmark 报告与每次运行。](./management-skill/assets/readme/lifecycle-skill-benchmark.md)

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

<!-- EXECUTION_DOMAIN_TABLE -->

## 安装

1. 把八个 Skill 文件夹放进 `~/.codex/skills/`。
2. 将 [`global-agents-entry-rule.md`](./task-analyze-skill/assets/global-agents-entry-rule.md) 合并到 `~/.codex/AGENTS.md`。
3. 正常启动 Codex；不安装生命周期 hook。

**隐私：** 镜像排除 auth、secret、私有 ledger、路由历史、cache、原始 Prompt/结果、receipt 和临时文件；每次发布都运行安全检查。

**镜像：** `qin-codex-skills` · `auto-best-model`
