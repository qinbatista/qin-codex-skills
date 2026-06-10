---
name: qin-destiny
description: Use when the user asks for Zi Wei Dou Shu / 紫微斗数 birth-chart work, including 排盘, 命盘, 十二宫, 命宫, 身宫, 四化, 大限, 流年, or requests that Zi Wei Dou Shu calculations be cross-validated.
---

# Zi Wei Dou Shu Cross-Checked Charting

Use this skill for 紫微斗数排盘 or chart-reading tasks.

## Reference Routing

Load only the reference needed for the task:

- For interpretive logic, report reasoning, 宿命解构, 流年, 未来五年, or 流月行事历, read [references/inference-logic.md](references/inference-logic.md).
- For templates, profiles, PDF delivery, naming, or production artifacts, read [references/report-production.md](references/report-production.md).
- For user corrections, new style rules, or future adjustments, read [references/adjustment-log.md](references/adjustment-log.md) and update the proper global or local adjustment file.
- For accuracy feedback such as "不准", "要改", "这里错了", or "需要修改", first classify whether the problem is global logic or person-specific, then record it in the proper file.
- For starting over from a known person/case, read [references/restart-checklist.md](references/restart-checklist.md).

## Required Intake

Before finalizing a chart, determine or state assumptions for:

- Calendar type: solar/Gregorian or lunar/农历. If lunar month could be leap, confirm normal vs 闰月.
- Birth sex/gender used for 大限顺逆.
- Birth time and time zone. If birth place is missing, state whether using clock time or 真太阳时.
- School/library basis when outputs can vary by school.

If the user corrects any intake field, discard the previous chart and recalculate from scratch.

## Verification Workflow

For chart construction, cross-check these anchors before giving the result:

1. Convert the input date through at least two independent routes when possible, such as `lunar-python`, `sxtwl`, an almanac source, or a second Zi Wei Dou Shu library.
2. Verify 时辰 index manually: 子=0, 丑=1, 寅=2, 卯=3, 辰=4, 巳=5, 午=6, 未=7, 申=8, 酉=9, 戌=10, 亥=11.
3. Generate the chart with a Zi Wei Dou Shu engine such as `iztro`/`iztro-py`.
4. Independently check key anchors: 命宫, 身宫, 五行局, 紫微星落宫, 天府星落宫, 年干四化.
5. Report assumptions and any unresolved ambiguity before interpretation.

Do not present interpretive conclusions until the base chart is locked.

## Output Shape

Prefer concise Chinese output:

- Input assumptions and conversion result.
- Cross-check summary.
- Core anchors: 命宫/身宫, 命主/身主, 五行局, 四柱, 四化.
- Twelve-palace table with 宫名、宫干支、主星、辅星、杂曜、长生/博士/将前/岁前、大限.

If sex/gender is unknown, provide the fixed natal star layout and mark 大限 as pending.

## Production Artifacts

For repeatable report production, keep files separated:

- Template document: fixed report sections, prompts, placeholders, and output standards.
- Profile data file: birth input, normalized calendar data, verification notes, chart anchors, and palace data only.
- Chart file: fixed natal chart facts and palace table only.
- Calculation file: deterministic calculation trace and cross-validation anchors only.
- Analysis file: interpretive text only; it must cite chart and calculation evidence.
- PDF output: when a profile or user instruction marks `readable_pdf_required`, generate a readable PDF artifact as the delivery file.

Do not store interpretive prose in the profile data file. Recalculate and update the profile first when any birth input changes.
