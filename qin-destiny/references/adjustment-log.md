# 紫微工作流调整记录

## 调整归档规则

每次用户提出新口径，先判断范围：

- 全局规则：适用于所有紫微排盘、推演、报告生产的规则，写入本 skill 或本目录 references。
- 个人规则：只属于某个人或某个 case 的偏好、修正、资料变化，写入对应 `private/adjustments/{profile_id}_adjustments.md` 或 `private/profiles/{profile_id}_profile.yaml`。
- 模板规则：改变报告结构、章节、输出标准，写入模板和 report-production 参考文档。
- 资料修正：改变出生日期、性别、时间、地点、历法，必须先更新 profile 并重新排盘。

## 准确性反馈分类

当用户说“不准”“要改”“这里错了”“需要修改”时，先判断问题范围，再写入对应文件：

- 整体不准：如果反馈适用于紫微推演方法、排盘校验流程、报告结构、AI 读取顺序或所有人的通用写法，更新本 skill 或 `references/` 中的对应文档。
- 个人不准：如果反馈只针对某个人的出生资料、个案经历、已生成解析、局部偏好或某个具体判断，更新 `private/adjustments/{profile_id}_adjustments.md`，必要时同步更新该人的 profile/chart/calculation/analysis。
- 资料不准：如果反馈涉及出生年月日、时辰、性别、时区、真太阳时、闰月或历法口径，先更新 profile，再重新生成 calculation、chart、analysis 和 PDF。
- 模板不准：如果反馈是章节顺序、输出格式、PDF 展示或生产交付方式，更新模板和 `references/report-production.md`。

不能把个人偏差写成全局规则；也不能只在聊天里接受修正而不落到文件。

## 已固定的全局经验

- 用户可能用简写日期，必须确认是农历还是公历。
- 若用户纠正历法、性别或时间基准，旧盘作废，重新排盘。
- 排盘必须交叉验证：历法转换、时辰索引、命身宫、五行局、紫微/天府、四化。
- 模板与个人资料分离；profile 不存解释性文案。
- 当 profile 标记 `readable_pdf_required`，交付必须生成可读 PDF。
- 最终 PDF 采用解读优先版：PDF 只放大概星盘摘要和重点解读，完整星盘保存在本地 chart Markdown 供阅读和交叉验证。
- 紫微斗数解读模板不是个人模板；所有正式报告、续算更新和局部询问都默认使用同一解读结构，局部询问只压缩篇幅。
- 固定生产报告结构为：命运全景、宿命解构、流年影像、未来五年推演、流月时局行事历。
- 准确性反馈必须先分类：整体不准写全局 skill/reference，个人不准写 private adjustments。

## 2026-06-09 通用解读模板

- 范围：模板
- 准确性分类：模板不准
- 用户要求：把前面的紫微星盘输出结果做成通用紫微斗数解读模板；每次更新或询问都使用这个模板；它不是个人模板。
- 反馈证据：用户明确说明“不是个人的模版，是紫微斗数的解读模版”。
- 已更新文件：
  - `~/.codex/skills/qin-destiny/references/report-production.md`
  - `~/.codex/skills/qin-destiny/references/inference-logic.md`
  - `~/.codex/skills/qin-destiny/references/adjustment-log.md`
- 对后续生产的影响：正式报告、续算更新和聊天里的局部询问，都默认套用“星盘摘要、结论总览、命运全景、宿命解构、大限、流年、未来五年、流月、解析边界”的结构；单点问题可压缩，但不能脱离模板证据口径。

## 未来调整记录格式

追加记录时使用：

```markdown
## YYYY-MM-DD 调整标题

- 范围：全局 / 个人 / 模板 / 资料修正
- 准确性分类：整体不准 / 个人不准 / 资料不准 / 模板不准
- 用户要求：
- 反馈证据：
- 已更新文件：
- 对后续生产的影响：
```
