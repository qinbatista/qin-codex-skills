<div align="center">

# 🚀 Auto Best Model

**专用于 Codex · 合格文字/代码使用自适应生产模型 · 例外保持 inline · 交付后再验证**

[English](./README.md)

已保存的最高版本家族质量梯级 · 只有你主动要求本地模型更新时才刷新

当前目录推导的优先生产模型：`gpt-5.3-codex-spark` · 简单=`low` · 复杂=`high`

</div>

## 🔄 核心流程

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/core-flow-zh-mobile.svg">
  <img src="./management-skill/assets/readme/core-flow-zh.svg" alt="核心流程：先展示完成结果，再由 Ending Real 验证结果">
</picture>

## ⚡ 模型与私有学习

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/model-router-mobile.svg">
  <img src="./management-skill/assets/readme/model-router.svg" alt="目录推导优先生产模型与完整质量梯级，并在私有 Obsidian 中学习">
</picture>

- **优先：** 合格文字/代码使用自适应目录优先生产模型：简单 `low`，复杂 `high`；精确只读、图像/混合和纯工具任务保持 inline。
- **操作故障：** 零结果、零 token 时，使用 Obsidian 当前上下文选择的质量模型档位。
- **质量故障：** 已产出就先返回；Ending 自动记录 receipt 对应的失败，再用不同验证者开启新的质量档修复。
- **学习：** Ending 结果更新宽泛项目/Skills `Model Switch.md` 页面；project/task/module/file/symbol 仅是字段，不创建层级笔记。

## 规则

- **Producer：** 合格文字/代码用自适应目录优先生产模型；精确只读、图像/混合和纯工具任务保持 inline。
- **Prompt：** 可复用 Prompt 和持久 AI 指令加载 Prompt Skill。
- **路由：** 只有明确要求或当前端到端证据成立时才委派。
- **交付：** 先展示完成结果，再运行 Ending Real。
- **验证：** Ending Real 在交付后运行；first-result 不包含它。
- **文件：** 修改前回溯项目/模块/文件历史；修改后记录已验证结果。
- **记忆：** 修改历史用本地 JSONL（可投影 Obsidian）；私有学习用宽泛项目/Skills `Model Switch.md`，仅字段，不建层级笔记。
- **模型：** 普通任务只读已保存 JSON；主动本地更新时选择最高数字 GPT 家族，缓存不可用就保留原列表。
- **隐私：** secret、原始 Prompt/结果、receipt、ledger、cache 和临时文件留在本地。

## 📊 当前 Benchmark

**Benchmark v6** · Direct/Global 都使用 `gpt-5.6-sol | ultra` · **6 组 A/B · 12 次运行 · 0 retry · 0 fallback · 0 repair**

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/model-benchmark-example-mobile.svg">
  <img src="./management-skill/assets/readme/model-benchmark-example.svg" alt="当前 GPT-5.6 Direct 与 Global benchmark，策略性能门禁失败">
</picture>

> **85.284% 更少 task tokens** · **整体首次结果快 8.629%** · 12 个结果全部正确 · 策略门禁 **FAIL**：Medium 计时仅赢 1/2 组

> 冻结只读 bootstrap 样本；此处不满足 Spark 条件 · 非计费 tokens · 不含 Ending Real

[脱敏 benchmark 证据](./task-analyze-skill/assets/model-routing-benchmark-example.json)

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
