---
name: qin-windows-keyboard-remap
description: Use when Qin asks Codex to inspect, change, troubleshoot, or document Windows keyboard behavior, key swaps, hotkeys, PowerToys Keyboard Manager settings, AutoHotkey hooks, registry scancode maps, vendor keyboard tools, or Alt/Ctrl/Start/Fn/CapsLock/Arrow remaps. Apply before editing Windows keyboard config or writing helper scripts so Codex verifies what keys are actually visible to Windows, preserves existing remaps, cleans up failed attempts, and states when physical testing is required.
---

# Qin Windows Keyboard Remap

Use this as the Windows keyboard-remap baseline. Keyboard labels are not enough; first prove what Windows receives and which remapper currently owns the behavior.

## Trigger

Use this skill before Windows keyboard or hotkey changes involving physical keys, modifier keys, arrow keys, `Fn`, Caps Lock, Start/Windows key, Alt, Ctrl, PowerToys Keyboard Manager, AutoHotkey, registry scancode maps, vendor remappers, or keyboard firmware tools.

## Workflow

1. Restate the requested behavior in terms of visible keys and target actions. For example, `Win+Left/Right -> Ctrl+Left/Right` means word-by-word cursor movement, while `Alt+Left/Right -> Home/End` means line start/end in many editors.
2. Inspect existing state before changing it: PowerToys Keyboard Manager config and process, vendor keyboard software, VIA/QMK/firmware tools, AutoHotkey scripts, scheduled tasks, startup entries, and registry scancode maps.
3. Preserve current remaps. Back up structured config files before editing, keep unrelated mappings, and document the exact rollback path.
4. Prefer the active remapper already installed on the machine. If PowerToys Keyboard Manager is installed and running, edit its structured config and restart/reload the Keyboard Manager engine instead of writing a custom low-level hook.
5. Clean up failed attempts before installing a replacement: stop old hook processes, remove scheduled tasks/startup entries, and delete stale generated scripts only when they were created for the failed remap.
6. Verify with a real key-event probe or user-assisted physical test. If Codex cannot receive physical keypresses in the current session, say that clearly instead of claiming the keyboard was tested.

## Guardrails

- `Fn` is often firmware-only and may not be visible to Windows. Do not promise Windows can swap or target physical `Fn` unless a probe, vendor tool, BIOS setting, VIA/QMK, or the keyboard manual proves it emits a visible event.
- Do not infer key identity from labels such as Cmd, Command, Start, Fn, Alt, or arrow icons. On Windows, `Cmd`/Command or "Start" usually means the Windows key (`LWin`/`RWin`), but keyboard firmware or vendor software can change that.
- Avoid registry scancode maps or custom AutoHotkey/PowerShell hooks for shortcut-level behavior unless simpler remapper tools cannot do it. Scancode maps are for base key swaps, not reliable modifier+arrow behavior.
- Do not break common Windows shortcuts such as `Win+Arrow` window snapping unless the user explicitly asks for that behavior to change.
- If the user says "switch", "swap", or "vice versa", write the mapping pair explicitly before applying it. Ambiguous modifier swaps are high-risk.
- Keep edits reversible and scoped to keyboard behavior. Do not alter unrelated PowerToys modules, vendor settings, shell shortcuts, or system policies.

## Known Qin Case

For Qin's current Windows keyboard preference, use this interpretation unless Qin corrects it:

- Global key swap: physical `Alt` and physical `Ctrl` should be switched on both left and right sides, so physical `Alt+C` and `Alt+V` behave as copy/paste.
- Word-by-word movement: physical Start/Windows key plus left/right arrow should act like `Ctrl+Left` and `Ctrl+Right`.
- Line jump: the Alt-function arrow behavior should go to line start/end, meaning `Alt+Left`/`Alt+Right` should become `Home`/`End`. Because Qin also wants global `Alt`/`Ctrl` swapped, include both `Alt+Arrow` and `Ctrl+Arrow` line-jump shortcut mappings when using PowerToys so the behavior survives remap order.
- Caps Lock preference: physical Caps Lock should act as momentary Left Shift (`Caps Lock -> Left Shift`) so tapping Caps Lock can toggle Chinese/English when the active Chinese IME uses tapped Shift for that toggle, while held physical Shift still behaves as uppercase.
- Do not try to switch Start with physical `Fn` unless Qin explicitly asks again and a key-event probe proves `Fn` is visible to Windows. If `Fn` is not visible, route to keyboard firmware, BIOS setting, vendor keyboard software, VIA/QMK, or manual-confirmed hardware setting.
- Do not replace the global `Alt`/`Ctrl` key swap with shortcut-only copy/paste mappings unless Qin explicitly asks to remove the key swap.

PowerToys key codes for the current preference:

- Key swaps: `164 -> 162`, `162 -> 164`, `165 -> 163`, `163 -> 165`, `20 -> 160`.
- Word jump shortcuts: `91;37 -> 162;37`, `91;39 -> 162;39`, `92;37 -> 162;37`, `92;39 -> 162;39`.
- Line jump shortcuts: `164;37 -> 36`, `164;39 -> 35`, `165;37 -> 36`, `165;39 -> 35`, plus `162;37 -> 36`, `162;39 -> 35`, `163;37 -> 36`, `163;39 -> 35`.

## Examples

- "I want Alt+C/V to copy/paste": keep the global `Alt`/`Ctrl` key swap, not shortcut-only copy/paste, unless Qin explicitly says shortcut-only.
- "Caps Lock should switch Chinese/English": map Caps Lock to Left Shift (`20 -> 160`) and keep physical Shift normal for uppercase.
- "Make Start+Arrow move word by word": preserve existing mappings, then map `Win+Left/Right` to `Ctrl+Left/Right` in the active remapper.
- "Alt should move most left and right": map Alt-arrow line jump and also cover Ctrl-arrow line jump when the global Alt/Ctrl swap is active.
- "Switch my Start and Fn keys": do not fake this in PowerToys unless a probe proves `Fn` is visible to Windows.
