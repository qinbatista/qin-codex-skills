# 紫微报告生产规范

## 文件职责

- `templates/`: 固定报告结构、占位符、输出标准。
- `private/profiles/`: 个人出生资料、校验记录、命盘锚点、十二宫数据。
- `private/charts/`: 固定命盘事实和十二宫表。
- `private/calculations/`: 固定推算过程、工具校验、手工锚点复核。
- `private/analysis/`: 解析文本和命理判断。
- `private/adjustments/`: 每个人的局部偏好、修正历史和调整记录。
- `private/reports/`: 面向阅读的最终 PDF 或成品。
- `private/previews/`: PDF 或页面预览图，用于检查排版。
- `scripts/`: 可重复执行的生成脚本。
- `docs/`: 项目级说明、系统地图和局部生产约定。

## Profile 规则

Profile 只存事实数据：

- 出生输入、历法、公历换算、时辰、性别、时区。
- 交叉验证记录。
- 四柱、命宫、身宫、五行局、命主/身主、来因宫、四化。
- 十二宫、星曜、神煞、大限、小限。
- 输出偏好，例如 `readable_pdf_required: true`。

不要把解释性段落、年度判断、建议文案写进 profile。

## 产物分离规则

- `chart`：命盘事实，不写解释。
- `calculation`：固定推算和交叉验证，不写解释。
- `analysis`：解释性文本，不改动出生资料，不重复完整排盘表。
- AI 交叉验证读取顺序：profile -> calculation -> chart -> analysis。

## 模板规则

模板适用于正式 PDF、续算更新、analysis 文件和聊天中的局部询问。每次紫微斗数解读都默认沿用同一结构；局部询问可以压缩篇幅，但不要改成完全散文式回答。

标准顺序：

1. 星盘摘要：大概星盘、核心锚点、chart/calculation 路径。
2. 结论总览：一句话总览和本次问题的直接结论。
3. 命运全景：人生主轴、事业、财富、关系、迁移、身心状态。
4. 宿命解构：命宫与身宫、四化链路、三方四正、六大领域。
5. 当前大限：阶段主题、机会、风险、建议。
6. 流年影像：目标年份关键词、机会窗口、风险窗口、行动策略。
7. 未来五年推演：年度主线、事业、财富、关系、状态、关键建议。
8. 流月时局行事历：月份范围、时局主题、适合行动、谨慎事项、关键词。
9. 解析边界：未计算项、流派差异、现实决策边界。

PDF 固定五段：

1. 命运全景
2. 宿命解构
3. 流年影像
4. 未来五年推演
5. 流月时局行事历

模板可以包含占位符、表格结构、写作要求，但不存个人事实数据。

## PDF 规则

- 当 profile 或用户指令标记 `readable_pdf_required` 时，最终交付必须包含 PDF。
- 最终 PDF 是解读优先版：正文以命运全景、宿命解构、流年、未来五年、流月等解释为主。
- PDF 首页只放大概星盘摘要，例如出生资料、命宫/身宫、命主/身主、五行局、生年四化和本地星盘文件路径。
- 完整十二宫星盘优先保存在 `private/charts/{profile_id}_chart.md`，作为本地方便阅读和 AI 交叉验证的 Markdown 文件，不把完整星盘表作为 PDF 主体。
- PDF 生成后至少验证：文件存在、页数、文件类型、首页或关键页预览。
- PDF 文档优先使用中文字体，避免乱码。
- 聊天回复只给简短摘要和 PDF 路径，不用长篇替代 PDF。

## 命名规则

用稳定、可追溯的文件名：

- `private/profiles/{profile_id}_profile.yaml`
- `private/charts/{profile_id}_chart.md`
- `private/calculations/{profile_id}_calculation.md`
- `private/analysis/{profile_id}_analysis.md`
- `private/adjustments/{profile_id}_adjustments.md`
- `private/reports/{profile_id}_profile.pdf`
- `private/reports/{profile_id}_reading.pdf`
- `templates/destiny_production_report_template.md`

`profile_id` 应包含出生资料核心锚点，例如 `destiny_<year>_<calendar>_<month>_<day>_<time>_<gender>`。
