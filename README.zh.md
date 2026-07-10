# qin-codex-skills

英文版: [README.md](./README.md)

## 技能图

```mermaid
%%{init: {"flowchart": {"nodeSpacing": 28, "rankSpacing": 54, "wrappingWidth": 240}}}%%
flowchart LR
  skill_task_analyze_skill["task-analyze-skill"] --> inside_task_analyze_skill["100% 触发的独立入口<br/>可多选模块<br/>任意入口模型边界<br/>简单/复杂显示<br/>逐节点路线<br/>结果生命周期<br/>运行时证明"]
  skill_workflow_skill["workflow-skill"] --> inside_workflow_skill["锁定路线执行控制器<br/>可多选模块<br/>锁定路线执行<br/>Main Goal / Ending Task 分流<br/>文本、Markdown 和 prompt 任务<br/>Python 和 C# 代码任务<br/>视觉和生成物<br/>全局 skill 编辑<br/>管理任务<br/>校准后的证据输出"]
  skill_code_skill["code-skill"] --> inside_code_skill["由锁定路线启动的执行者<br/>可多选模块<br/>Prompt Creating<br/>Karpathy Coding Guidelines<br/>Python Code Checker<br/>C# Minimal Style<br/>Easy Python/C# Spark"]
  skill_verify_skill["verify-skill"] --> inside_verify_skill["由锁定路线启动的执行者<br/>可多选模块<br/>UI Review<br/>本地脚本验证<br/>Skill 验证<br/>生成物验证<br/>真实证据和报告"]
  skill_optimization_skill["optimization-skill"] --> inside_optimization_skill["由锁定路线启动的执行者<br/>可多选模块<br/>Skill Optimization<br/>官方 skill 合规检查<br/>本地脚本转换<br/>引用资料抽取<br/>资产和模板"]
  skill_management_skill["management-skill"] --> inside_management_skill["由锁定路线启动的执行者<br/>可多选模块<br/>Codex Switch<br/>GitHub Sync<br/>隐私安全管理"]
  classDef skill fill:#111,color:#fff,stroke:#eee;
  classDef content fill:#2f2f2f,color:#fff,stroke:#666;
  class skill_task_analyze_skill,skill_workflow_skill,skill_code_skill,skill_verify_skill,skill_optimization_skill,skill_management_skill skill;
  class inside_task_analyze_skill,inside_workflow_skill,inside_code_skill,inside_verify_skill,inside_optimization_skill,inside_management_skill content;
```

## Main Goal 和 Ending Task

每个任务先进入独立 [`task-analyze-skill`](./task-analyze-skill/SKILL.md)；[`workflow-skill`](./workflow-skill/SKILL.md) 只执行返回的锁定路线。

```mermaid
flowchart TD
  A["用户请求"] --> B["Task Analyze：当前选择模型只做分析"]
  B --> C["workflow-skill 执行每节点模型 + effort"]
  C --> D["Mini Verify"]
  D -->|失败| C
  D -->|通过| E["立即显示主结果"]
  E --> F["后台派发 Ending Task"]
  F --> G["Real Verify"]
  F --> H["独立优化验证"]
  F --> I["报告 / 日志 / 文档 / 记忆"]
  G -->|发现正确性失败| J["通知用户并重新打开任务"]
```

- **Mini Verify：** 主结果的基础 gate。
- **主结果：** 请求工作完成且 Mini Verify 通过后立即显示。
- **Ending Task：** 结果之后运行 Real Verify、独立优化验证、报告、日志、文档和记忆；正确性失败必须通知并重新打开任务。

### Skill 内容一览

#### [`task-analyze-skill`](./task-analyze-skill/) · 工作流类 / Workflow

- **角色：** 100% 触发的独立入口
- **大功能：** 独立且 100% 触发的入口 skill：当前入口模型和 effort 只做 Task Analyze 路由，返回锁定的逐节点图谱，并使用本地 `model_experience.json` 的条件化汇总与 `success_model` / `failed_model` 边界。
- **可多选模块：** 任意入口模型边界; 简单/复杂显示; 逐节点路线; 结果生命周期; 运行时证明
- **选择规则：** 需要哪个模块就用哪个；同一个任务可以同时使用多个模块，不是单选，也不要运行无关模块。

#### [`workflow-skill`](./workflow-skill/) · 工作流类 / Workflow

- **角色：** 锁定路线执行控制器
- **大功能：** 执行 Task Analyze 锁定的路线，按节点先尝试不同 effort 再切换模型；先运行 Mini Verify 再派发 Ending Task。
- **可多选模块：** 锁定路线执行; Main Goal / Ending Task 分流; 文本、Markdown 和 prompt 任务; Python 和 C# 代码任务; 视觉和生成物; 全局 skill 编辑; 管理任务; 校准后的证据输出
- **选择规则：** 需要哪个模块就用哪个；同一个任务可以同时使用多个模块，不是单选，也不要运行无关模块。

#### [`code-skill`](./code-skill/) · 代码类 / Code

- **角色：** 由锁定路线启动的执行者
- **大功能：** Spark 优先的活动注册代码域执行者；Python、普通 C#、Unity C# 是内置示例。小体量文本/代码先用 Spark-low，Spark 运行失败可安全回退静态方案。
- **可多选模块：** Prompt Creating; Karpathy Coding Guidelines; Python Code Checker; C# Minimal Style; Easy Python/C# Spark
- **选择规则：** 需要哪个模块就用哪个；同一个任务可以同时使用多个模块，不是单选，也不要运行无关模块。

#### [`verify-skill`](./verify-skill/) · 验证类 / Verification

- **角色：** 由锁定路线启动的执行者
- **大功能：** Mini Verify 在主结果前做基础检查；Real Verify 在结果后的 Ending Task 中执行，并把两次结果回填到原始的 receipt-backed 结果尝试。
- **可多选模块：** UI Review; 本地脚本验证; Skill 验证; 生成物验证; 真实证据和报告
- **选择规则：** 需要哪个模块就用哪个；同一个任务可以同时使用多个模块，不是单选，也不要运行无关模块。

#### [`optimization-skill`](./optimization-skill/) · 优化类 / Optimization

- **角色：** 由锁定路线启动的执行者
- **大功能：** 把明确要求、重复多次或明显可复用的流程变成本地脚本、引用资料、prompt、资产或模板，同时保持行为不变。
- **可多选模块：** Skill Optimization; 官方 skill 合规检查; 本地脚本转换; 引用资料抽取; 资产和模板
- **选择规则：** 需要哪个模块就用哪个；同一个任务可以同时使用多个模块，不是单选，也不要运行无关模块。

#### [`management-skill`](./management-skill/) · 管理类 / Management

- **角色：** 由锁定路线启动的执行者
- **大功能：** 处理 Codex profile 操作和全局 skill GitHub 同步，不暴露私人数据，并保留本地私有路由历史。
- **可多选模块：** Codex Switch; GitHub Sync; 隐私安全管理
- **选择规则：** 需要哪个模块就用哪个；同一个任务可以同时使用多个模块，不是单选，也不要运行无关模块。



## 运行规则

- 每个任务先进入 `task-analyze-skill`；入口模型和 effort 只做 Task Analyze 的边界分析与路由协调，不可作为全局默认，也不是 profile 字段。
- 每个活动的注册代码域都进入 `code-skill`；Python、普通 C#、Unity 项目中的 C# 是内置示例。
- 直接工具路线只有安装的工具 skill 和可观察的 Mini 检查：没有子模型、receipt 或自适应样本；模型路线保留准确 model|effort、receipt 与 Mini/Real 学习。
- 分发路线必须依序执行：`run-plan` -> 读取 Mini 通过结果 -> 显示完整的基本验证结果 -> `release-main-result <handoff>` -> `run-ending <handoff>`；显示结果前不得释放 Ending。
- 路由记账输出 `selected_pair`、`reason`、`trial`、`success_model`、`failed_model`；校准/冻结选择从边界推导并以 `trial=false` 复用。先调 effort，再换模型；仅验证失败、实质漂移、策略变化或明确重置才重新打开。
- 正确性是 gate；token 和耗时只是 receipt 证据，不能覆盖正确性或安全边界。
- Mini Verify 先记录原始结果尝试；Real Verify 后续更新同一个结果尝试，不会把 verifier 当作结果模型。
- Auth 和 GitHub 镜像维护进入 `management-skill` 内部路由；私有 ledger 不进入镜像。
