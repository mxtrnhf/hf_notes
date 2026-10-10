# highfleet-elevation  (repo `hf_elevation`, published)

Sets the **elevation** (`m_floor`) of the part held in the shipworks. Elevation decides who can block whom in arc/exhaust scans (`../systems.md`), so combined with
highfleet-qol's restored gun-arc blocking you can design guns that fire over your own hull.

* Keys while holding a part: **U** raise, **P** lower, **\\** give back to automatic (then drop it so the game recomputes). A text overlay shows floor, manual/auto, neighbours.
* Config `elevation.ini`: `max_floor`, `sync_children` (mounted parts follow their mount; otherwise a gun is buried under a raised block), `child_offset`, `overlay`.
* Mechanism: reads the editor's held-part pointer (global `0x1403c0d88`; editor-active flag `0x1403ef368`), clears bit `0x01` of `m_floor_type` (+0x9b0) and writes `m_floor` (+0x9b8). Polling, no detour.
* A ship saved with manual floors loads the same without the mod (the game honours saved values).
* Status: works [game]. Overlay is a separate transparent window (may not show in exclusive fullscreen). Other editor functions: wheel `FUN_1400bc5e0`, rotate `FUN_1400bdad0`, place `FUN_1400bbbf0`.
