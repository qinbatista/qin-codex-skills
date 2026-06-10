# 紫微任务重启清单

## 从已有人物重新开始

1. 找到对应 profile：`private/profiles/{profile_id}_profile.yaml`。
2. 读取固定推算：`private/calculations/{profile_id}_calculation.md`。
3. 读取固定命盘：`private/charts/{profile_id}_chart.md`。
4. 读取解析：`private/analysis/{profile_id}_analysis.md`。
5. 读取同名调整档：`private/adjustments/{profile_id}_adjustments.md`。
6. 读取模板：`templates/destiny_production_report_template.md`。
7. 如果要推演或解读，读取 `references/inference-logic.md`。
8. 如果要生产 PDF，读取 `references/report-production.md`。
9. 检查 profile 的 `verification.status` 是否为 `locked`。
10. 如果出生资料有任何变化，先重排并更新 profile、calculation、chart，再重新生成 analysis/report。
11. 若 `readable_pdf_required: true`，最后必须生成 PDF 并验证预览。

## 从新人物开始

1. 先确认：公历/农历、闰月、性别、出生时辰、时间基准、出生地/真太阳时。
2. 用两条独立路径校验历法转换。
3. 用 Zi Wei Dou Shu 引擎排盘，并手工核对关键锚点。
4. 在 `private/profiles/` 创建 profile，不直接写解读。
5. 需要报告时再套模板生成 PDF。

## 重启时不要做

- 不要直接沿用上次解释来替代排盘。
- 不要把个人偏好写进全局规则，除非它适用于所有紫微任务。
- 不要在流年、流月资料未计算时编造具体月份判断。
