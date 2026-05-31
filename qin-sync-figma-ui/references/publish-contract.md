# Figma Publish Contract

Use this reference only when implementing or debugging the Figma publish step.

## Queue Fields

`figma-publish-queue.json` contains:

- `versionId`
- `baselineHash`
- `uiChanged`
- `items[]`

Each item contains:

- `order`
- `slug`
- `label`
- `figmaLayerName`
- `pageVersionId`
- `baselineVersionId`
- `image`
- `contentHash`
- `boardHash`
- `changed`
- `x`
- `y`

## Publish Behavior

Publish each queue item as one independently selectable Figma image layer.

For Chrome-backed publishing:

1. Deselect current layer before paste.
2. Put the image bytes on the clipboard.
3. Paste once.
4. Set X/Y from the queue.
5. Rename the selected layer to `figmaLayerName`.
6. Continue with the next queue item.

Avoid using selected image replacement unless that is explicitly intended. Pasting while an image is selected can replace the existing image instead of creating a new layer.

## Verification

After publishing:

- Select all synced layers.
- The selected count must equal `items.length`.
- `remainingClipboard` must be `0`.
- The visible layer names must match queue `figmaLayerName` values.
- Keep the Figma tab open as the deliverable.
