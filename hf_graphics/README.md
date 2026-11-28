# HighFleet graphics knowledge base

[Notes home](../README.md) · [Evidence legend](../docs/README.md)

Graphics here means **native GUI, text, images, world overlays, ship previews,
render passes and their lifecycle**, not just buttons. Target: **Steam 1.163**,
preferred executable base `0x140000000`. No portability to 1.151 is implied.

## Start a new mod here

1. [Calling guide](calling-guide.md): which drawing route to choose, hook sites,
   ABI, coordinates, text/sprite state and failure rules.
2. [Native GUI cookbook](native-gui.md): build native-looking buttons and labels,
   route clicks and survive screen rebuilds without stale pointers.
3. [HUD and render targets](hud-and-panels.md): camera projection, rings, reticles,
   ship previews and the more dangerous temporary-state operations.
4. [Workspace reference catalog](sources.md): source files, useful symbols,
   evidence archives, duplicate checkouts and confidence limits.
5. [Library and tool proposal](library-and-tools.md): what can be extracted now,
   what still needs RE, and why a static crate alone cannot solve DLL hook conflicts.
6. [Validation checklist](validation.md): visual/lifecycle/compatibility checks.

## Consolidated reference notes

The 13 original `docs/rendering/` notes now live here. Old paths contain only
forwarding pages so existing workspace links remain navigable. The old overview
became `frame-overview.md`; this README is the new entry point. There was no
standalone `gui/` knowledge directory to rename. Raw datasets remain in their
existing data directory, linked below rather than duplicated.

| Topic | Reference |
|---|---|
| Frame and scene layers | [Overview](frame-overview.md), [pipeline](render-pipeline.md), [editor frame](editor-frame.md) |
| Fonts and text | [Font inventory, metrics and samples](fonts.md) |
| Images and resources | [Sprites and resource getters](images-and-sprites.md), [sprite blend byte and HUD opacity](sprite-blend-byte.md) |
| Native controls | [Early construction evidence](gui-elements.md), [pre-combat screen](precombat-screen.md) |
| Click routing | [ClickFunc](click-func.md), [archived analysis/corrections](click-func-analysis.md) |
| Combat HUD | [Callouts and colours](battle-hud-callouts.md), [ship panels](battle-ship-panels.md) |
| Probe observations | [Seam tests](seam-test-run-1.md), [UI events and screens](ui-events-and-screens.md) |
| Raw evidence | [GUI capture](../docs/data/rendering/gui-dump-precombat-ammo-2026-10-16.txt), [ClickFunc catalog](../docs/data/rendering/clickfunc-elements.tsv) |
| Engine, shaders and assets | [HGE interface](../docs/engine-hge.md), [native structures](../docs/structures.md), [formats](../docs/formats.md), [content](../docs/content.md) |
| General native hooking | [Hook rules](../docs/hooks.md), [hot-reload study](../docs/findings/engine/hot-reload-feasibility.md) |

## Evidence and maintenance

Compiled **2026-11-13** from existing notes and local source inspection, primarily
`highfleet-allies` commit `d44dd49b1a237da8d29878ddf317fea08eace98f`
(ally 1.2.4). This consolidation performed **no new live Ghidra verification,
in-game testing, code changes, deployment or library implementation**.

- **Source-checked** means the current local implementation was read. It does not
  mean the native ABI was independently re-derived or every path works in game.
- **Native evidence** links an earlier static-analysis record.
- **Game-confirmed** is used only where an existing user/report recorded it.
- **Proposal / unresolved** is not a supported API.
- Read the current guides before copying historical snippets. In particular,
  custom controls **can be freed**, `SetBackground_` **appends**, and B24 is
  **GLITCH-dependent**. Historical notes retain their original observations.
- Add durable new graphics findings here, with game version, source revision,
  native address/caller, ownership/thread requirements and validation status.
  Keep one canonical copy of each dataset/source file; link it from this index.
- Workspace links outside `hf_notes` work in this local directory layout, not in
  a standalone clone. The catalog also records portable repository paths.
