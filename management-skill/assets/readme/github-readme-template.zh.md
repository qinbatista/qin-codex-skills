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

## 📊 三档生命周期 Benchmark：无 Skill vs 有 Skill

**已修正基线：** “无 Skill”只做用户要求的主任务，**验证 token = 0、验证时间 = 0**。“有 Skill”先返回主结果，再启动独立后台 Ending session。简单、中等、复杂三档共 18 个 session 均得到预期结果，但启用 Skill 后的完整生命周期在三档中都使用了更多时间和 token。

![三档生命周期 benchmark：无 Skill 基线验证为零，并对比有 Skill 的主任务和后台验证 token 与时间](./management-skill/assets/readme/lifecycle-skill-benchmark.svg)

### 中位数全貌

| 档位 | 工作负载 | 模型 | 无 Skill token | 有 Skill 主任务 | 有 Skill 验证 | 有 Skill 总计 | 无 Skill 时间 | 有 Skill 主任务 | 有 Skill 验证 | 有 Skill 总计 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 简单 | 精确算术 JSON | `gpt-5.6-luna \| low` | 13,017 | 19,044 | 19,115 | 38,159 | 2.790 s | 3.291 s | 3.456 s | 6.747 s |
| 中等 | 一个 Python 定价方法 | `gpt-5.6-terra \| medium` | 14,860 | 20,893 | 42,069 | 62,961 | 3.237 s | 4.370 s | 7.054 s | 11.423 s |
| 复杂 | 六文件依赖审计 | `gpt-5.6-sol \| high` | 30,869 | 55,269 | 43,443 | 98,712 | 11.597 s | 17.584 s | 12.775 s | 30.359 s |

蓝色基线在主任务结束后立即停止，不存在基线 Ending session。绿色条纹只属于启用 Skill 的模式，精确表示已完成主任务之后的后台验证成本。

### 全部运行证据

| 档位 | 配对 | 模式 | 主任务时间 | 验证时间 | 总时间 | 主任务 token | 验证 token | 总 token |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| 简单 | 1 | 无 Skill | 2.858 s | 0 | 2.858 s | 13,017 | 0 | 13,017 |
| 简单 | 1 | 有 Skill | 3.425 s | 3.529 s | 6.954 s | 19,044 | 19,115 | 38,159 |
| 简单 | 2 | 无 Skill | 2.722 s | 0 | 2.722 s | 13,017 | 0 | 13,017 |
| 简单 | 2 | 有 Skill | 3.156 s | 3.383 s | 6.539 s | 19,044 | 19,115 | 38,159 |
| 中等 | 1 | 无 Skill | 3.274 s | 0 | 3.274 s | 14,863 | 0 | 14,863 |
| 中等 | 1 | 有 Skill | 4.375 s | 5.826 s | 10.201 s | 20,880 | 42,008 | 62,888 |
| 中等 | 2 | 无 Skill | 3.200 s | 0 | 3.200 s | 14,856 | 0 | 14,856 |
| 中等 | 2 | 有 Skill | 4.364 s | 8.281 s | 12.645 s | 20,905 | 42,129 | 63,034 |
| 复杂 | 1 | 无 Skill | 13.141 s | 0 | 13.141 s | 30,816 | 0 | 30,816 |
| 复杂 | 1 | 有 Skill | 12.952 s | 13.685 s | 26.637 s | 43,031 | 43,957 | 86,988 |
| 复杂 | 2 | 无 Skill | 10.053 s | 0 | 10.053 s | 30,922 | 0 | 30,922 |
| 复杂 | 2 | 有 Skill | 22.215 s | 11.865 s | 34.080 s | 67,507 | 42,928 | 110,435 |

### 方法、结论与限制

- **设计：** 每档 2 组配对；12 个主任务 session + 6 个仅有 Skill 的 Ending session = 18 个独立 session；每档交替运行顺序。
- **一致性：** 每组使用相同输入、模型、effort 和只读 sandbox。无 Skill 使用 `--ignore-user-config`；有 Skill 加载当前全局配置，再启动独立 `ENDING_TASK_WORKER` session。
- **正确性：** 18/18 得到预期输出；0 reroute、retry、fallback、repair。
- **结论：** 三档完整生命周期全部 **FAIL**：简单/中等/复杂分别增加 +193.2% / +323.7% / +219.8% token，以及 +141.8% / +252.9% / +161.8% 时间。
- **限制：** 计时是完整 process/session 时间，不是首次可见结果延迟；logical token 不是计费 token；每档两组仅为描述性证据，不构成性能准入样本。

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
