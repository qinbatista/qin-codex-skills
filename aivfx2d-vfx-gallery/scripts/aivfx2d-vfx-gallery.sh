#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/Users/qin/Documents/YofaGames/AIVFX2D"
GALLERY_DIR="$PROJECT_ROOT/Assets/VFXGallery"
GALLERY_HTML="$GALLERY_DIR/index.html"
MANIFEST="$GALLERY_DIR/vfx_gallery_manifest.json"
BUILDER="$PROJECT_ROOT/cache/unity-asset-store-vfx/tools/build_asset_store_vfx_gallery.py"

usage() {
  cat <<'USAGE'
Usage: aivfx2d-vfx-gallery.sh [--open|--summary|--rebuild]

--open      Open the local AIVFX2D VFX gallery HTML page.
--summary   Print gallery counts and key paths.
--rebuild   Rebuild the gallery HTML, manifest, inventory, and contact sheet.
USAGE
}

summary() {
  /usr/bin/python3 - "$MANIFEST" "$GALLERY_HTML" "$GALLERY_DIR/vfx_gallery_big_screenshot.png" <<'PY'
import json
import sys
from pathlib import Path

manifest = Path(sys.argv[1])
html = Path(sys.argv[2])
shot = Path(sys.argv[3])
if not manifest.exists():
    raise SystemExit(f"Missing gallery manifest: {manifest}")

data = json.loads(manifest.read_text(encoding="utf-8"))
summary = data.get("summary", {})
for key in [
    "generatedAt",
    "assetStorePackages",
    "assetStorePrefabs",
    "assetStoreVisible",
    "existingImported",
    "visibleCount",
    "hiddenHelpers",
    "verifiedClean",
    "verifiedWithNotes",
    "copiedPrefabPreviews",
]:
    print(f"{key}: {summary.get(key)}")
print(f"html: {html}")
print(f"bigScreenshot: {shot}")
PY
}

case "${1:---open}" in
  --open)
    if [[ ! -f "$GALLERY_HTML" ]]; then
      echo "Missing gallery HTML, rebuilding first: $GALLERY_HTML"
      /usr/bin/python3 "$BUILDER"
    fi
    open "$GALLERY_HTML"
    summary
    ;;
  --summary)
    summary
    ;;
  --rebuild)
    /usr/bin/python3 "$BUILDER"
    summary
    ;;
  -h|--help)
    usage
    ;;
  *)
    usage
    exit 2
    ;;
esac
