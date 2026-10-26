# highfleet-elevation  (repo `old_standalone/hf_elevation`, published)

> Merged into the QoL fork; upstream PR state in [../../STATUS.md](../../STATUS.md). Standalone repo `old_standalone/hf_elevation` (published as `highfleet-elevation`) is the pre-merge version. See [qol.md](qol.md).

Sets the **elevation** (`m_floor`) of the part held in the shipworks. Elevation decides who can block whom in arc/exhaust scans (section "How elevation and firing arcs work" below), so combined with
highfleet-qol's restored gun-arc blocking you can design guns that fire over your own hull.

* Keys while holding a part: **U** raise, **P** lower, **\\** give back to automatic (then drop it so the game recomputes). A text overlay shows floor, manual/auto, neighbours.
* Config `elevation.ini`: `max_floor`, `sync_children` (mounted parts follow their mount; otherwise a gun is buried under a raised block), `child_offset`, `overlay`.
* Mechanism: reads the editor's held-part pointer (global `0x1403c0d88`; editor-active flag `0x1403ef368`), clears bit `0x01` of `m_floor_type` (+0x9b0) and writes `m_floor` (+0x9b8). Polling, no detour.
* A ship saved with manual floors loads the same without the mod (the game honours saved values).
* Status: works [game]. Overlay is a separate transparent window (may not show in exclusive fullscreen). Other editor functions: wheel `FUN_1400bc5e0`, rotate `FUN_1400bdad0`, place `FUN_1400bbbf0`.
* **QoL port (fork branch `elevation`, PR #20, rebased onto upstream main and force-pushed 2026-10-16 as `aafbf6e`; pull request state: [../../STATUS.md](../../STATUS.md)):** section `elevation` of `qol.json` (`enabled` (allowed here: no vanilla-equivalent value), `max_floor`, `sync_children`, `child_offset`, `hint` = `native`|`window`|`off`, `keys.raise`/`lower`/`auto` as key names such as `U`, `F5`, `Backslash`). 1.163 only. The user installed the DLL and reported it works [game]. The hint is drawn natively inside the game (next paragraph; [../rendering/render-pipeline.md](../rendering/render-pipeline.md)); the GDI overlay window remains as the `hint: window` fallback. Remove the standalone `elevation.dll` when using it; `elevation.ini` is no longer read.
* **Native hint (2026-10-14, QoL fork branch `elevation`):** the readout is now drawn inside the game by wrapping the editor label-pass call at `0x140303fb4` (see [../rendering/render-pipeline.md](../rendering/render-pipeline.md)), with the game's own font `fixed_16` (white, scale 1.0, right-aligned at x=1880, y=24 of the 1920x1080 frame; first tried `dinpro_14_bold`, too bold) [game: user confirmed it appears in all editor states]. Setting `hint` in the `elevation` section: `native` (default), `window` (the old transparent overlay window and polling threads, also the automatic fallback when the hook site bytes do not match, e.g. when another mod patched it [game]) or `off` (keys still work, nothing drawn). In `native` mode key polling and floor writes run in the same hook on the game thread; keys only react while the game window has the keyboard focus. Font notes: [../rendering/fonts.md](../rendering/fonts.md).

## How elevation and firing arcs work [game unless marked]
Moved from the retired `systems.md` (2026-10-19).

* Solver `FUN_140256a90` sets `m_floor` from `m_floor_type` and neighbours. Bits: `0x01` auto-recompute, `0x02` neighbours must be strictly higher, `0x04`/`0x08` neighbour-count variants,
  `0x10` force floor 3. A part without `0x01`/`0x10` keeps its saved floor. An automatic part rises by 1 when every connection-slot neighbour is at or above it, repeating until stable
  (bumping attached non-socket children). Saved ships contain floors 1-3.
* Arc scan `Body::ScanSectors` `0x140052340`: 360 one-degree rays via `World_RaycastBodies` `0x140239f30`; a hit writes 0 to that degree's `m_sectors` entry. `UpdateEngineCovered`
  `0x14001c4a0` averages the engine cone into `m_mdl_covered`. The gun test is on the **shooter**: a non-gun shooter is not floor-tested (every body blocks), a gun shooter skips a body when `shooterFloor > candidateFloor`. Both floors get +1 when the body's master is null or type 7 (the candidate's +1 is new in 1.163, see [../findings/elevation-rules-1151-vs-1163.md](../findings/elevation-rules-1151-vs-1163.md)).
* Gun arc blocking is restored in 1.163 by highfleet-qol: it detours `FireGun` (inject `0x140032f22`, exit `0x140032ef0`, return `0x140032f29`), reads the gun's 360 `m_sectors`
  (requires stats +0x128 != 0), maps the gun angle relative to the root to a sector and blocks on 0.0.
