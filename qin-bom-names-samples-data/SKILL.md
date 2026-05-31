---
name: qin-bom-names-samples-data
description: Use when the user says "BOM names samples data" or asks for reusable MuseAI BOM-name sample circled images, default BOM-name testing samples, or Fabric/Trims/Labels/Artwork circle-image assets with BOM result JSON for agent testing.
---

# BOM Names Samples Data

Use this skill to reuse the saved MuseAI BOM-name sample assets from the 2026-05-01 default BOM-name test run.

## Asset Set

Canonical asset folder:
`/Users/qin/.codex/skills/qin-bom-names-samples-data/assets/bom_names_samples_data/20260501_133530`

Manifest:
`assets/bom_names_samples_data/20260501_133530/manifest.json`

Contents:
- `input_default_bom_name_front_garment.png`: default source garment image.
- `bom_name_agent_5run_again_report.pdf`: visual PDF report from the original run.
- `report_page_1.png`, `report_page_2.png`: rendered report pages.
- `summary.json` and `bom_name_agent_5run_again_manifest.json`: original run metadata.
- `attempt_1` through `attempt_5`: each attempt includes `fabric_circles.png`, `trims_circles.png`, `labels_circles.png`, `artwork_circles.png`, `result.json`, `status.json`, and per-type result JSON files.

## Usage

- When the user says "BOM names samples data", load this asset folder first.
- Use `attempt_5` as the screenshot-matching default sample unless the user asks for all attempts.
- Use all five attempts for repeated regression or comparison testing.
- Treat these assets as BOMNameAgent sample data for Fabric, Trims, Labels, and Artwork circle review testing.
- Do not paste or persist raw base64 from these images; pass file paths or encoded payloads only inside the test call that needs them.

## Default BOM-Names Image Report

When the user asks for the default BOM names image report, use the generated-asset evidence layout from the user's reference report, such as:
`/Users/qin/QinProject/Muse/MuseAI/data/cache/qin-test-pdf-report/bom_extract_image_attempt3_flat_front_20260501_165125/bom_extract_image_attempt3_report.pdf`.

- Build an image-first A3 landscape PDF, not the generic compact table report.
- Include an overview page with run id, source image, result/log paths, and per-type counts.
- For each BOM row, show the cropped source/reference image next to the final generated BOM asset image.
- Each evidence card should show the BOM name, type, pass/warning status, source side, coordinates, cropped reference label, generated asset label, and the generated asset path or URL when useful.
- Group several evidence cards per page when they fit cleanly, matching the `Generated BOM Assets 1-4` style from the reference PDF.
- Keep type headers color-coded and easy to scan: Fabric blue, Trims orange, Labels green, Artwork purple.
- Save the report, rendered preview pages, manifest, raw run logs, agent logs, cropped source/reference images, final generated images, result JSON, stdout, and stderr under the report run cache.
- Circled BOMNameAgent images can be included as supporting source evidence, but they are not the main default report. The main evidence is crop image versus final generated image for each BOM row.
