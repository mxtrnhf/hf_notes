# Ghidra sweep 2026-10-29 — batch 8, agent 7 (`rep_*` re-match D, 0x140300000–0x140336FFF)

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.

Scope: every `rep_*` function whose entry is in **0x140300000–0x14032FFFF**
or **0x140330000–0x140336FFF**, minus agent 3's funclet addresses (nothing in
`funclet-ownership-2026-10-29.tsv`) and anything in 0x140337000+.

* Functions in the two ranges at start: **430**
* `rep_*` in the two ranges at start: **21** (not ~120 — the earlier passes of
  batches 6/7 had already renamed the rest)
* all 21 already had a q4 row from batch 6 (b7 re-checked the 5 EH funclets in
  q3), so this pass is a genuine re-match, not a first audit
* **15 renamed + plated**, **6 stale (sharpened)**, **0 unreadable**
* after the run: **6 `rep_*` left in scope** (see "Left stale")
* no `save_program`, tags, README/STATUS edits, commits or `create_function`

Audit table: `rep-audit-2026-10-29-q4.tsv` — appended 21 rows (file now 145
data rows, 5 columns). Prior rows were not rewritten.

## How identity was established

* **Listing script** (`run_script_inline`): entry, size, body MD5, embedded
  `rep_<target>` address, caller/callee names, referenced strings. Bodies were
  decompiled with `batch_decompile`/`decompile_function` ≤10 at a time; the four
  VideoTask bodies >0x2000 B (17–19 KB) were deliberately **not** decompiled and
  were named from caller-side proof (below), as b7-agent4 explicitly handed on.
* **Dispatcher proof for the four scene routines.** `VideoTask_Dispatch`
  (0x140300c20) was read in full. Its branches are mutually exclusive:
  `param_4 == 1` → fade; campaign (`IS_IN_CAMPAIGN_ || BOOL_147fc6fd2`) →
  0x14030a6b0; any of `DAT_147fc6fc8/fd4`, `IS_IN_ARCADE_BATTLE`, `f82`,
  `fda..fdd`, `fc9` → 0x1403050a0; otherwise (all clear) → 0x14030f250, except
  `IsInEditor` → 0x140300db0. That matches the branch→screen table already in
  `docs/findings/source-file-names.md` and the probe run
  (`docs/runs/probe-run-1.md`: main menu → 0x14030f250, ship editor →
  0x140300db0, fuel shop → battle branch 0x1403050a0).
* **CRT band proved by table position.** `mainCRTStartup` iterates
  `_initterm_e(0x1403521b8, 0x1403521e0)`. Dumping those five qwords gives
  `[0]=0, [1]=0x140334b70, [2]=0x140334c28, [3]=0x14033664e, [4]=0x1403345cc`.
  So 0x140334b70 and 0x140334c28 are **C initializers**, not `__scrt_*` main
  stages — which is why the old "exact `__scrt_*` stage" hunt was never going
  to converge. Their bodies were then read as initializers.
* **`sinf4` family proved by disassembly**, not decompilation: 0x140334de0 is
  18 B `CMP [0x1403c2e50],2; JGE 0x140335d60; JMP 0x140335420`
  (`__sse41_sinf4` / `__sse2_sinf4@@16`); 0x140334e43 is 13 B
  `SHUFPS XMM0,XMM1,0; ADDPS 0.0; JMP 0x140334de0`.

## Renamed (15)

| addr | new name | one-line proof |
|---|---|---|
| 0x140300db0 | `VideoTask_RenderEditorScene` | dispatcher editor branch only (`IsInEditor`); probe-run editor screen |
| 0x1403050a0 | `VideoTask_RenderBattleScene` | dispatcher battle-flag branch; docs call it the battle/city renderer; World_Render / DrawBattleShipPanel / Camera_ZoomByXPreset |
| 0x14030a6b0 | `VideoTask_RenderMapScene` | dispatcher campaign branch; MAP_SKY / MAPMARK_* / MAPMODE_FLEET / Map_RenderSkyLayers |
| 0x14030f250 | `VideoTask_RenderMenuScene` | dispatcher remaining branch; probe-run main menu → 0x14030f250; Gui_FlushDrawList |
| 0x140314290 | `MapMode_DrawRadarSweep` | full body: +0x43c sweep ×0.02, +0x444 2→1 on +0x448, +0x4d0 → 128 px, Fleet_DetectionStrength blips, 32-bin ring, MAPMODE_RADAR_* over MAP_MAP |
| 0x140315580 | `Hud_DrawZoomViewOverlay` | Hud_DrawZoomGrid + Hud_DrawNoiseFrame + SetAimRectZoom, ZOOM_LEVEL extents, campaign gate |
| 0x140315b40 | `ShipCard_DrawBearingTrail` | 500-float ring 0x148075fb0, +0.2/bin, indexed by (body+0x454)/2π·500, 64 bars, flips +0x474 |
| 0x140316230 | `VideoTask_LayoutShipCards` | 0x20-stride card records → 0x28-byte {pos,angle}, min/max rect into renderer +0x1e0/+0x188/+0x400; VideoTask.cpp:0x57c CHECK ERROR |
| 0x140318920 | `Physics_ShapeDistance` | two b2DistanceProxy + b2DistanceInput → b2Distance 0x14031fc30; callers b2Contact_Update + 0x140047ef0 |
| 0x140334b70 | `CRT_InitializeProcess` | `__xi_a[1]`; _set_app_type(2), _set_fmode, __p__commode, onexit tables, atexit thunk, argv, SList, __setusermatherr, locale, env |
| 0x140334c28 | `CRT_InitializeStdioOptions` | `__xi_a[2]`; ORs 0x24 into 0x140397200 and 2 into `CRT_LocalStdioScanfOptions`, returns 0 |
| 0x14033535c | `CRT_InitializeSListThunk` | `LEA RCX,[0x1480771f0]; JMP InitializeSListHead` via IAT 0x1403511d0; only caller 0x140334b70 |
| 0x1403353a4 | `CRT_GuardDispatchThunk` | walks guard-checker table 0x140381bb0, calls each through 0x1403519c8; caller 0x140334b70 |
| 0x140334de0 | `sinf4` | runtime dispatch to `__sse41_sinf4` / `__sse2_sinf4@@16` |
| 0x140334e43 | `sinf4_ScalarShim` | broadcast scalar + ADDPS 0.0 + tail-jump to `sinf4`; caller b2TimeOfImpact |

`sinf4` was accepted despite the "short name" warning because the name is the
CRT symbol being re-matched, not an invented abbreviation.

## Left stale (6), sharpened

| addr | why it stays stale |
|---|---|
| 0x1403182a0 | Spawn/step **interval gate** over `_Xtime_get_ticks`, state at `QWORD_1403c2d78` `{int interval; int lastMs; handle}`. Called after every ship spawn in `BattleSpawner_SpawnShips` (0x1402d1a60) and in 0x1402d2d00 / 0x1402d22e0, so spawn cadence is clear; the exact unit/return contract is not (returns the sign of the elapsed ticks on the reset path). |
| 0x140336c80 | EH cleanup funclet (Array_DestroyRange24 + deallocate + rethrow); funclet table 0x148088ab8 / unwind 0x140385d7c. Owner unresolved from FuncInfo4. |
| 0x140336d20 | EH cleanup funclet (EhCleanup_InvalidParameterWrapper + DeleteArray56); table 0x148088adc / unwind 0x140385de4 / FuncInfo4 0x140385e20. |
| 0x140336df0 | EH cleanup funclet (EhCleanup_FreeWrapper + DeleteArray32); table 0x148088b0c / unwind 0x140386084. |
| 0x140336ea0 | EH cleanup funclet (2× memmove wrapper + rethrow); table 0x148088b30 / unwind 0x1403861e4. |
| 0x140336f00 | EH cleanup funclet (memmove wrapper + rethrow); table 0x148088b3c / unwind 0x14038622c. |

The five funclets sit in the 0x140336730+ band that agent 3 owns for the **EH
map**, but none of them has a row in `funclet-ownership-2026-10-29.tsv`, so
they were in my `rep_*` set and were re-read. They are deliberately left
unnamed: resolving their owner means walking the FuncInfo4 unwind data, which
is agent 3's assignment. Handing back the table/unwind addresses above so the
owner pass can name them.

## Notes / traps confirmed for this sub-range

* The four >0x2000 B VideoTask bodies have **no embedded function entry** at
  their `rep_<target>` address; the dispatcher branch is the only reliable
  identity source. Naming them by decompiled body would have been impossible
  within the size rule, and naming them by the embedded address would have been
  wrong (the targets are stale copies of 0x1402d5ce0 / 0x1402da020 /
  0x1402df4f0 / 0x1402e4160).
* `0x140334b70` is **not** `__scrt_common_main_seh`: mainCRTStartup already
  contains the init + `_initterm` + `Main` + `exit` sequence, and 0x140334b70
  is called *from* the `__xi_a` initializer table. The old stale row's
  "`_set_app_type` stage" reading came from the fake embedded label; the real
  identity is a process-wide initializer.
* `0x1403353a4` was labelled `_guard_dispatch_icall`, but its body is the
  guard-**check** walker over 0x140381bb0 (the dispatch itself is the 2-byte
  import thunk at 0x1403366f0). Named `CRT_GuardDispatchThunk` rather than
  `_guard_check_icall` to respect the name-collision rule (an existing
  `_guard_check_icall` would be a token subset).
* `b2` neighbours were already named from batch 7, which is what made
  0x140318920 provable as a GJK shape-distance wrapper instead of "FastFail?".

## Counts

* `rep_*` in scope: **21**
* renamed + plated: **15**
* stale label (sharpened): **6**
* unreadable: **0**
* `rep_*` left in scope: **6**
