<div align="center">

# 🚀 Auto Best Model

**专用于 Codex · 默认 inline · 有证据才路由 · 交付后再验证**

[English](./README.md)

从 **GPT-5.6** 开始测试 · 最新注册 Codex 模型：`gpt-5.6-luna` · `gpt-5.6-terra` · `gpt-5.6-sol`

</div>

## 🔄 核心流程

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/core-flow-zh-mobile.svg">
  <img src="./management-skill/assets/readme/core-flow-zh.svg" alt="核心流程：先展示完成结果，再由 Ending Real 验证结果">
</picture>

## 规则

- **Inline：** 普通任务使用当前 Codex 模型。
- **Prompt：** 可复用 Prompt 和持久 AI 指令加载 Prompt Skill。
- **路由：** 只有明确要求或当前端到端证据成立时才委派。
- **交付：** 先展示完成结果，再运行 Ending Real。
- **验证：** Ending Real 失败就修复；first-result 不包含它。
- **文件：** 修改前回溯项目/模块/文件历史；修改后记录已验证结果。
- **记忆：** 本地 JSONL 是权威来源；Obsidian 可选。
- **模型：** GPT-5.6 Luna → Terra → Sol；先调 effort；Spark 只用于已准入 tiny 任务。
- **隐私：** secret、原始 Prompt/结果、receipt、ledger、cache 和临时文件留在本地。

## 📊 历史 Benchmark

**Benchmark v5** · Direct/Global 都使用 `gpt-5.6-sol | ultra` · **6 组 A/B · 12 次运行 · 0 retry · 0 fallback · 0 repair**

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/model-benchmark-example-mobile.svg">
  <img src="./management-skill/assets/readme/model-benchmark-example.svg" alt="GPT-5.6 Direct 与 Global 历史 benchmark">
</picture>

> **77.292% 更少 task tokens** · **首次结果快 29.464%** · 仅该冻结样本 · 非计费 tokens · 不含 Ending Real

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
