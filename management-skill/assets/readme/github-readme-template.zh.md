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
3. **每个独立真实 test、API check 或 render 都另开一个全局 projectless、独立评分并选模的 `End Task-<任务名>-<检查>`。** 通过绝对项目路径访问文件，不把验证任务塞进项目分类。
4. **每个 Ending 必须执行分配的真实检查，所有必需检查都要 PASS。** PASS 先写入持久证据，再自动归档自己；归档可能直接结束 worker turn。FAIL/BLOCKED 保持可见。FAIL 会建立包含准确错误的 Fix Task（全局 projectless），再由全新的 End Task 重跑；最多修复三次。

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
- **记忆：** Ending 结果更新宽泛项目/Skills `Model Switch.md` 页面；project/task/module/file/symbol 仅是字段，不创建层级笔记。

## 规则

- **Producer：** 显示分数、band、entry/selected；复用最低正确档。两次 PASS 降级；质量 FAIL 升级。
- **Prompt：** 可复用 Prompt 和持久 AI 指令加载 Prompt Skill。
- **路由：** 只有明确要求或当前端到端证据成立时才委派。
- **交付：** 先完成并返回主任务结果，再进行后台验证。
- **验证：** 每个独立检查使用评分、选模 End Task；全部 PASS。FAIL → Fix Task → 全新 End Task，最多三次。
- **文件：** 修改前回溯项目/模块/文件历史；修改后记录已验证结果。
- **记忆：** 修改历史用本地 JSONL（可投影 Obsidian）；私有学习用宽泛项目/Skills `Model Switch.md`，仅字段，不建层级笔记。
- **模型：** 使用已保存梯级；主动本地更新时选择最高数字 GPT 家族；符合条件的小编辑优先 Spark-low；缓存不可用就保留原列表。
- **隐私：** secret、原始 Prompt/结果、receipt、ledger、cache 和临时文件留在本地。

## 📊 真实自适应 Benchmark：先完成，再后台验证

当前冻结 v46 比较：**无 Skill** 固定使用 `gpt-5.6-sol | ultra`；**有 Skill** 从 `gpt-5.6-luna | max` 进入，再按冻结历史逐步骤选模。所有 adaptive child/graph 都计入，只排除 Luna 入口 controller。

<picture><source media="(max-width: 600px)" srcset="./management-skill/assets/readme/model-benchmark-example-mobile.svg"><img src="./management-skill/assets/readme/model-benchmark-example.svg" alt="当前 Direct 与 Auto 基准：所有结果和 Ending 正确，但性能策略门槛失败"></picture>

**6 组 A/B · 12 次运行 · 12/12 精确结果与 12/12 Ending PASS · 0 retry · 0 fallback · 0 repair**

| 档位 | Direct token 中位数 | Auto token 中位数 | 配对 token 节省 | Direct 首结果 | Auto 首结果 | 配对时间节省 |
|---|---:|---:|---:|---:|---:|---:|
| 简单 | 25,881.5 | 29,091.5 | -30.064% | 13.430s | 19.831s | -50.694% |
| 中等 | 16,366 | 36,632.5 | -123.834% | 10.545s | 34.323s | -225.472% |
| 复杂 | 263,445.5 | 138,267 | **+44.428%** | 32.375s | 56.927s | -79.224% |

**实测结论：正确率 PASS；性能策略 FAIL。** 复杂任务带动总任务 token 降低 33.269%，但 Auto 总体慢 97.127%，简单和中等任务也都退化。因此证据否定“普遍节省”的结论；logical token 不等于计费 token。

[查看精确 v46 报告。](./task-analyze-skill/TEST_AND_BENCHMARK.md) · [打开脱敏 benchmark 证据。](./task-analyze-skill/assets/model-routing-benchmark-example.json)

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
