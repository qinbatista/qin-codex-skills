# qin-codex-skills

英文版: [README.md](./README.md)

## 技能图

```mermaid
%%{init: {"flowchart": {"nodeSpacing": 28, "rankSpacing": 54, "wrappingWidth": 240}}}%%
flowchart LR
  skill_code_skill["code-skill"] --> inside_code_skill["可多选模块<br/>Prompt Creating<br/>Karpathy Coding Guidelines<br/>Python Code Checker<br/>Unity C# Minimal Style<br/>Easy Code Spark"]
  skill_test_skill["test-skill"] --> inside_test_skill["可多选模块<br/>Done Means Tested<br/>Test PDF Report<br/>Code/API/CLI Tests<br/>UI/Browser Tests<br/>Image/Document/PDF Tests<br/>Comparison/Audit Reports"]
  skill_verify_skill["verify-skill"] --> inside_verify_skill["可多选模块<br/>UI Review<br/>本地脚本验证<br/>Skill 验证<br/>生成物验证<br/>PDF 证据检查"]
  skill_optimization_skill["optimization-skill"] --> inside_optimization_skill["可多选模块<br/>Skill Optimization<br/>官方 skill 合规检查<br/>本地脚本转换<br/>引用资料抽取<br/>资产和模板"]
  skill_workflow_skill["workflow-skill"] --> inside_workflow_skill["可多选模块<br/>文本和 Markdown 任务<br/>代码任务<br/>视觉和生成物<br/>全局 skill 编辑<br/>管理任务<br/>最终证据报告"]
  skill_management_skill["management-skill"] --> inside_management_skill["可多选模块<br/>Codex Switch<br/>GitHub Sync<br/>隐私安全管理"]
  classDef skill fill:#111,color:#fff,stroke:#eee;
  classDef content fill:#2f2f2f,color:#fff,stroke:#666;
  class skill_code_skill,skill_test_skill,skill_verify_skill,skill_optimization_skill,skill_workflow_skill,skill_management_skill skill;
  class inside_code_skill,inside_test_skill,inside_verify_skill,inside_optimization_skill,inside_workflow_skill,inside_management_skill content;
```

这是全局 Codex skills 的公开镜像和路由说明。顶部先展示主图，下面列每个 skill 的大功能、可多选模块和选择规则。

### Skill 内容一览

#### [`code-skill`](./code-skill/) · 代码类 / Code

- **大功能：** 合并 prompt、代码思路、Python、Unity C# 和小代码模块，按任务需要多选所有适用模块。
- **可多选模块：** Prompt Creating; Karpathy Coding Guidelines; Python Code Checker; Unity C# Minimal Style; Easy Code Spark
- **选择规则：** 需要哪个模块就用哪个；同一个任务可以同时使用多个模块，不是单选，也不要运行无关模块。

#### [`test-skill`](./test-skill/) · 测试类 / Testing

- **大功能：** 执行真实测试，并生成带输入、方法、输出和通过原因的 PDF 报告，跨代码、UI、图片、文档或 PDF 时组合证据路线。
- **可多选模块：** Done Means Tested; Test PDF Report; Code/API/CLI Tests; UI/Browser Tests; Image/Document/PDF Tests; Comparison/Audit Reports
- **选择规则：** 需要哪个模块就用哪个；同一个任务可以同时使用多个模块，不是单选，也不要运行无关模块。

#### [`verify-skill`](./verify-skill/) · 验证类 / Verification

- **大功能：** 检查 UI、脚本、生成物、skill 和工作流是否满足用户要求，跨类型任务可组合多个验证路线。
- **可多选模块：** UI Review; 本地脚本验证; Skill 验证; 生成物验证; PDF 证据检查
- **选择规则：** 需要哪个模块就用哪个；同一个任务可以同时使用多个模块，不是单选，也不要运行无关模块。

#### [`optimization-skill`](./optimization-skill/) · 优化类 / Optimization

- **大功能：** 把稳定重复的流程优化成本地脚本、引用资料、资产或模板，必要时组合多个优化路线来节省 token 和执行时间。
- **可多选模块：** Skill Optimization; 官方 skill 合规检查; 本地脚本转换; 引用资料抽取; 资产和模板
- **选择规则：** 需要哪个模块就用哪个；同一个任务可以同时使用多个模块，不是单选，也不要运行无关模块。

#### [`workflow-skill`](./workflow-skill/) · 工作流类 / Workflow

- **大功能：** 统一控制 Codex 任务拆分、目标检查、skill 路由、循环验证和最终证据，遇到混合任务时多选所需路线。
- **可多选模块：** 文本和 Markdown 任务; 代码任务; 视觉和生成物; 全局 skill 编辑; 管理任务; 最终证据报告
- **选择规则：** 需要哪个模块就用哪个；同一个任务可以同时使用多个模块，不是单选，也不要运行无关模块。

#### [`management-skill`](./management-skill/) · 管理类 / Management

- **大功能：** 统一管理 Codex 本地账号/Profile 操作和全局 skill 的 GitHub 同步，按需要使用一个或两个管理路线。
- **可多选模块：** Codex Switch; GitHub Sync; 隐私安全管理
- **选择规则：** 需要哪个模块就用哪个；同一个任务可以同时使用多个模块，不是单选，也不要运行无关模块。

