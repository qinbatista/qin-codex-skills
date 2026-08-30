<div align="center">

# 🚀 Auto Best Model

**专用于 Codex · 每个任务评分 · 先完成主任务 · 真实证据或重要更新必须做 Ending**

**优势：** 简单任务快跑，复杂任务选择最低正确模型，主结果先交付，私有学习留在本地，最后独立验收。已保存的最高版本家族质量梯级 · 只有你主动要求本地模型更新时才刷新 · 0–24 分小型低风险编辑先经同会话结果门再试 Spark-low · 更大任务使用已保存的质量梯级

| 分数 | 档位 | 默认行为 |
|---:|---|---|
| 0–24 | Simple | 小型低风险工作先过同会话结果门，再试 `gpt-5.3-codex-spark|low` |
| 25–49 | Standard | 使用已保存的最低正确质量档 |
| 50–74 | Complex | 按能力使用已保存档；有依赖的工作保持同一上下文 |
| 75–100 | Advanced | 使用更强保存档，必要时拆成复合任务图 |

**冻结 v48 Benchmark：** Direct `gpt-5.6-sol|ultra` → Auto Best Model 入口 `gpt-5.6-luna|max`；20 次运行，0 retry/fallback/repair，4/4 Sol 入口探针 PASS。稳定执行 `267.692s → 94.534s`（**+64.686%**）；logical token `1,653,005 → 317,799`（**+80.774%**）。

[English](./README.md)

</div>

## 🔄 核心流程

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/core-flow-zh-mobile.svg">
  <img src="./management-skill/assets/readme/core-flow-zh.svg" alt="先评分并完成主结果，真实证据或重要更新会创建独立 projectless Ending">
</picture>

## ✅ 先完成主任务；真实证据或重要更新必须做 Ending

1. 每个任务按 0–100 评分，读取相关 Skill 并完成要求。代码只运行一次最小 Quick Check，然后返回 `CODE READY`。
2. 有真实 surface，或属于结构、非纯数值代码、思路、流程的重要更新时，必须发出 `ending-required`；重要更新还必须完成持久项目记忆。只有明确的纯数值小改动且没有其他 surface 才可 skip。
3. 唯一全局 projectless Ending 必须读回空项目上下文。Spark-xhigh 优先；真实额度、五小时或 provider 限制会记录限制时间与重试时间，冷却期间直接使用下一档更强主控，冷却结束后恢复 Spark 优先。
4. 失败时新建独立 projectless Repair Task，绝不发送、steer、中止、终止、handoff、移动或修改任何现有任务/session；若写入面由活动任务占用，Repair 只等待且不发消息打断。Ending 与 Repair 都保持可见。

## ⚡ 模型与私有学习

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/model-router-mobile.svg">
  <img src="./management-skill/assets/readme/model-router.svg" alt="基于 receipt 的最低正确模型路由">
</picture>

- **入口：** 步骤能力与难度历史选择最低正确档；Sol/高入口可下降，Luna-max/更低入口可升级。
- **学习：** 一次 PASS 保留；两次匹配 PASS 才试降一档；质量失败升一档；操作故障不按质量失败学习。
- **调度：** 复合任务分步骤路由；有依赖的多文件工作保持一个上下文 producer。
- **记忆：** Model Switch 与原生类别链接按项目 → Model Switch → 类别 → 共享类别记录；不用 JSON sidecar；项目/任务等保持为字段。

## 规则

- **Producer：** 显示分数、档位和路由；复用最低正确档。
- **Prompt：** 可复用 Prompt 和持久 AI 指令加载 Prompt Skill。
- **路由：** 只在明确要求或端到端证据成立时委派。
- **交付：** 先完成并返回主结果，再后台验证。
- **验证：** 三个真实 surface 才创建 Ending；否则明确 skip。
- **文件：** 修改前回溯项目/模块/文件历史；完成后记录验证结果。
- **记忆：** 本地 JSONL，可选 Obsidian；代码要求 symbol。
- **模型：** 使用保存梯级；主动更新才刷新；cache 缺失保留旧值。
- **隐私：** secret、原始 Prompt/结果、receipt、ledger 和 cache 留在本地。

## 📊 真实自适应 Benchmark：先完成，再后台验证

冻结 v48 比较 Direct `gpt-5.6-sol|ultra` 与从 `gpt-5.6-luna|max` 进入的 Auto Best Model；主指标只计算干净的稳定选中执行。

<picture><source media="(max-width: 600px)" srcset="./management-skill/assets/readme/model-benchmark-example-mobile.svg"><img src="./management-skill/assets/readme/model-benchmark-example.svg" alt="冻结 v48 的四档 Direct 与 Auto Benchmark"></picture>

**10 组 A/B · 20 次运行 · 20/20 预期结果和证据门 PASS · 4/4 Sol 入口探针 PASS · 0 retry/fallback/repair**

| 档位 | Direct token | Auto token | token 节省 | Direct 时间 | Auto 时间 | 时间节省 |
|---|---:|---:|---:|---:|---:|---:|
| Simple | 146,062 | 94,622 | **+35.218%** | 79.212s | 30.568s | **+61.410%** |
| Standard | 73,474 | 47,806 | **+34.935%** | 25.346s | 16.588s | **+34.554%** |
| Complex | 644,587 | 87,297 | **+86.457%** | 65.990s | 20.642s | **+68.720%** |
| Advanced | 788,882 | 88,074 | **+88.836%** | 97.144s | 26.736s | **+72.478%** |
| **All** | **1,653,005** | **317,799** | **+80.774%** | **267.692s** | **94.534s** | **+64.686%** |

**结果：每个档位和总体的两个主指标都下降。** 首结果总体更慢（`265.243s → 294.040s`）；Ending 不计入主指标（Direct `0.687s`、Auto `0.691s`、合计 `1.378s`）。Logical token 不是计费 token；冻结 cohort 不代表普遍保证。[方法报告](./task-analyze-skill/TEST_AND_BENCHMARK.md)当前标为 v47；对齐前以[脱敏 v48 JSON 证据](./task-analyze-skill/assets/model-routing-benchmark-example.json)为准。

## 🧩 八个公开 Skill

- [`Task Analyze`](./task-analyze-skill/SKILL.md) — 评分、路由、Benchmark 与准入。
- [`Workflow`](./workflow-skill/SKILL.md) — 执行已准入的锁定路线。
- [`Prompt`](./prompt-skill/SKILL.md) — 管理可复用 Prompt 与持久 AI 指令。
- [`Code`](./code-skill/SKILL.md) — 管理 Python、C#、Unity C# 与已注册代码域。
- [`Project Memory`](./project-memory-skill/SKILL.md) — 项目覆盖、回溯与验证记录。
- [`Verify`](./verify-skill/SKILL.md) — 结果后的 Real Verify 与回归证据。
- [`Optimization`](./optimization-skill/SKILL.md) — 将稳定重复工作变成工具。
- [`Management`](./management-skill/SKILL.md) — 管理私有 profile 与公共镜像。

## 🛠️ 已注册执行域

- `general` · general · `workflow-skill` · active · Spark schedule: no · [rules](./task-analyze-skill/references/model-selection.md)
- `python` · code · `code-skill` · active · Spark schedule: source-eligible · [rules](./code-skill/references/python-rules.md)
- `csharp` · code · `code-skill` · history-only · Spark schedule: source-eligible · [rules](./code-skill/references/csharp-rules.md)
- `unity_csharp` · code · `code-skill` · active · Spark schedule: source-eligible · [rules](./code-skill/references/unity-csharp-rules.md)
- `code_unspecified` · code · `code-skill` · history-only · Spark schedule: source-eligible · [rules](./code-skill/references/spark-small-code.md)

## 安装或更新

GitHub 发布版已经过维护者门禁；消费者安装或更新只 fresh download 并安全替换八个 Skill，保留用户全局 `AGENTS.md`，不重复 unit、platform、regression、parity、attestation 或 Ending 验证。替换已记录的 Codex 全局模板是独立的 `install-global-agents` 显式操作，带持久恢复点；`bridge-user-skills` 只预览官方用户 Skill 路径链接，必须加 `--apply` 才会创建。

- **macOS/Linux 首次安装或更新：** `stage="$(mktemp -d)" && git clone --depth 1 https://github.com/qinbatista/qin-codex-skills.git "$stage/qin-codex-skills" && python3 "$stage/qin-codex-skills/management-skill/scripts/sync_global_skills.py" deploy --source-dir "$stage/qin-codex-skills" && rm -rf "$stage"`。
- **Windows PowerShell 首次安装或更新：** `$ErrorActionPreference='Stop'; $stage=Join-Path $env:TEMP ("qin-codex-skills-"+[guid]::NewGuid()); try { git clone --depth 1 https://github.com/qinbatista/qin-codex-skills.git $stage; if ($LASTEXITCODE) { throw 'clone failed' }; py -3 "$stage\management-skill\scripts\sync_global_skills.py" deploy --source-dir $stage; if ($LASTEXITCODE) { throw 'deploy failed' } } finally { if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force } }`。保留无关本地 Skill 和私有 `task-analyze-skill/local/` 状态。

**隐私：** 公共镜像严格包含上面的八个 Skill，排除 auth、secret、私有 ledger、路由历史、cache、原始 Prompt/结果、receipt 和临时文件；发布前运行安全扫描。**镜像：** `qin-codex-skills` · `auto-best-model`
