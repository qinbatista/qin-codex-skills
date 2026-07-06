---
name: aivfx2d-vfx-gallery
description: Open, rebuild, inspect, or summarize the local AIVFX2D VFX gallery. Use when the user asks to view all AIVFX2D VFX, preview imported VFX, open the gallery webpage, rebuild the VFX gallery index/contact sheet, or find where AIVFX2D VFX preview images and manifests are stored.
---

# AIVFX2D VFX Gallery

## Project Paths

- Project root: `/Users/qin/Documents/YofaGames/AIVFX2D`
- Gallery HTML: `/Users/qin/Documents/YofaGames/AIVFX2D/Assets/VFXGallery/index.html`
- Gallery manifest: `/Users/qin/Documents/YofaGames/AIVFX2D/Assets/VFXGallery/vfx_gallery_manifest.json`
- Big screenshot/contact sheet: `/Users/qin/Documents/YofaGames/AIVFX2D/Assets/VFXGallery/vfx_gallery_big_screenshot.png`
- Formal imported VFX root: `/Users/qin/Documents/YofaGames/AIVFX2D/Assets/VFX/ImportedAssetStore`
- Download/build cache: `/Users/qin/Documents/YofaGames/AIVFX2D/cache/unity-asset-store-vfx`

## Rules

- Treat `Assets/VFX/ImportedAssetStore` as the formal Asset Store VFX collection.
- Keep one VFX prefab in one folder under each package's `VFX/` directory.
- Do not add shader-only, code-only, documentation-only, demo scene-only, or audio-only assets to the formal VFX gallery.
- Do not scan historical WallImpact trial/version folders into the gallery. They belong in cache/review workflows unless the user explicitly asks for them.
- Prefer the gallery manifest and verification reports over ad hoc folder guesses.

## Commands

Use the bundled script for repeatable operations:

```bash
/Users/qin/.codex/skills/aivfx2d-vfx-gallery/scripts/aivfx2d-vfx-gallery.sh --open
/Users/qin/.codex/skills/aivfx2d-vfx-gallery/scripts/aivfx2d-vfx-gallery.sh --summary
/Users/qin/.codex/skills/aivfx2d-vfx-gallery/scripts/aivfx2d-vfx-gallery.sh --rebuild
```

Run `--open` to launch the local gallery page. Run `--rebuild` only after imports, verification, or preview assets change.

## Reporting

When reporting status, include the visible VFX count, hidden helper count, clean verification count, notes count, and the absolute gallery/screenshot paths. If Unity verification reports material or missing-script notes, state that honestly instead of calling those VFX fully clean.
