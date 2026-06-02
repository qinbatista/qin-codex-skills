---
name: qin-windows-keyboard-remap
description: Use when Qin asks Codex to inspect, change, troubleshoot, or document Windows keyboard behavior, key swaps, hotkeys, PowerToys Keyboard Manager settings, AutoHotkey hooks, registry scancode maps, vendor keyboard tools, or Fn/Ctrl/Start/Alt/Arrow remaps. Apply before editing Windows keyboard config or writing helper scripts so Codex verifies what keys are actually visible to Windows, preserves existing remaps, cleans up failed attempts, and states when physical testing is required.
---

# Qin Windows Keyboard Remap

Use this as the Windows keyboard-remap baseline. Keyboard labels are not enough; first prove what Windows receives and which remapper currently owns the behavior.

## Trigger

Use this skill before Windows keyboard or hotkey changes involving physical keys, modifier keys, arrow keys, `Fn`, Start/Windows key, Alt, Ctrl, PowerToys Keyboard Manager, AutoHotkey, registry scancode maps, vendor remappers, or keyboard firmware tools.

## Workflow

1. Restate the requested behavior in terms of visible keys and target actions. For example, `Win+Left/Right -> Ctrl+Left/Right` means word-by-word cursor movement, while `Alt+Left/Right -> Home/End` means line start/end in many editors.
2. Inspect existing state before changing it: PowerToys Keyboard Manager config and process, vendor keyboard software, VIA/QMK/firmware tools, AutoHotkey scripts, scheduled tasks, startup entries, and registry scancode maps.
3. Preserve current remaps. Back up structured config files before editing, keep unrelated mappings, and document the exact rollback path.
4. Prefer the active remapper already installed on the machine. If PowerToys Keyboard Manager is installed and running, edit its structured config and restart/reload the Keyboard Manager engine instead of writing a custom low-level hook.
5. Clean up failed attempts before installing a replacement: stop old hook processes, remove scheduled tasks/startup entries, and delete stale generated scripts only when they were created for the failed remap.
6. Verify with a real key-event probe or user-assisted physical test. If Codex cannot receive physical keypresses in the current session, say that clearly instead of claiming the keyboard was tested.

## Guardrails

- `Fn` is often firmware-only and may not be visible to Windows. Do not promise Windows can swap or target physical `Fn` unless a probe, vendor tool, BIOS setting, VIA/QMK, or the keyboard manual proves it emits a visible event.
- Do not infer key identity from labels such as Start, Fn, Alt, or arrow icons. On Windows, "Start" usually means the Windows key (`LWin`/`RWin`), but keyboard firmware or vendor software can change that.
- Avoid registry scancode maps or custom AutoHotkey/PowerShell hooks for shortcut-level behavior unless simpler remapper tools cannot do it. Scancode maps are for base key swaps, not reliable modifier+arrow behavior.
- Do not break common Windows shortcuts such as `Win+Arrow` window snapping unless the user explicitly asks for that behavior to change.
- If the user says "switch", "swap", or "vice versa", write the mapping pair explicitly before applying it. Ambiguous modifier swaps are high-risk.
- Keep edits reversible and scoped to keyboard behavior. Do not alter unrelated PowerToys modules, vendor settings, shell shortcuts, or system policies.

## Known Qin Case

For Qin's current keyboard request, use this interpretation unless Qin corrects it:

- The primary desired swap is physical `Fn` with `Ctrl`.
- Do not treat Start/Windows key as the same thing as `Fn`. Start/Windows key remaps are only relevant if Qin explicitly asks for Start/Windows behavior.
- If physical `Fn` is not visible to Windows, do not fake an `Fn`/`Ctrl` swap with `Win`/Start mappings. Route to the keyboard firmware, BIOS setting, vendor keyboard software, VIA/QMK, or manual-confirmed hardware setting.
- Word-by-word movement is `Ctrl+Left` and `Ctrl+Right`; only map another shortcut to that after confirming the actual visible source keys.
- Move to line edges is usually `Home` and `End`; only map `Alt+Left/Right` to that if Qin confirms Alt should move most-left/most-right.

## Examples

- "Switch my Fn and Ctrl keys on Windows": inspect whether `Fn` is visible first; if not visible, route to firmware/vendor settings instead of a Windows-only remap.
- "Make Start+Arrow move word by word": preserve existing mappings, then map `Win+Left/Right` to `Ctrl+Left/Right` in the active remapper only if Qin explicitly asks for Start/Windows key behavior.
- "Alt should move most left and right": clarify whether this means line start/end, then map `Alt+Left/Right` to `Home/End` if confirmed.
