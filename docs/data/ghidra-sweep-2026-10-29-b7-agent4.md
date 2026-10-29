# Ghidra sweep, batch 7 agent 4 — `rep_*` re-match in `0x140200000–0x140336FFF`

Program `Highfleet.exe.unpacked.exe` v1.163, project `HighfleetServer`.
Scope: every `rep_*` in `0x140200000–0x140336FFF` not listed in
`funclet-ownership-2026-10-29.tsv`. **349 `rep_*`** at start.
**9 renamed, all plated. 0 created, 0 unreadable (4 bodies >0x2000 left
un-decompiled by rule 6).** No `save_program`, no tags, no README/STATUS edits,
no commits.

| | before | after |
|---|---|---|
| `rep_*` in range | 349 | 338 |
| named (non-`rep_`) in range | 932 | 943 |
| `FUN_*` in range | untouched (agent 9's set) | — |

Appended **36 rows** to `rep-audit-2026-10-29-q3.tsv` (now 398 lines incl.
header): 9 `renamed` + 21 `stale` for addresses that were not yet in q3 + 6
`stale` q3 rows whose partial identity this pass improved.

## Headline: the range was already fully audited

Every one of the 349 in-scope addresses is already present in
`rep-audit-2026-10-29-q3.tsv` (b6 agent 4, `0x140200000–0x1402FFFFF`) or
`rep-audit-2026-10-29-q4.tsv` (b6 agent 5, the `0x140300000–0x140336FFF`
tail that b6 folded into its own run). The 22 addresses new *relative to q3*
are all in q4. So this was a true re-match, not a first pass: the prior verdict
on all 349 was `stale label`, and the value of this pass is (a) the 9 promotions
below, (b) an independent body check of a 30-address sample, and (c) resolving
several "unidentified" rows to concrete roles.

Two in-range `rep_*` were renamed by other agents **during** this pass
(`0x14026e240` → `Precombat_BuildAmmoSelectorRow`, `0x1402d4330` →
`Battle_InitPlayerRoster`), which is why 349 − 9 = 340 but the final count is
338.

## Method

`run_script_inline` listing: address, size, SHA-1 of the body bytes, embedded
target class (entry / inside-function / outside / no-address), direct callees,
referenced string literals, callers, data-xref count for all 349
(`/tmp/opencode/b7a4_before.tsv`). Body hash index over all 5,155+ functions:
no in-range `rep_*` has a byte-identical twin, confirming the b5/b6 result for
this sub-range again. Then `decompile_function` on ~30 candidates (always
≤0x2000 bytes), plus targeted reads of vtable/dispatch/callers. A name was
applied only when the body (or two independent caller-side sources) proved the
role; otherwise the row keeps `stale label` with a sharper partial identity.

### Operational note for the batch

The shared script bundle `/home/maksim/ghidra_scripts` was stuck in a permanent
compile-failure state ("hasn't changed, with 78 files failing") because several
`McpInline_*`/`PlateAudit`/Python-in-`.java` sources were deleted from disk
after failing once. **A subdirectory is its own bundle**: all of this pass ran
from `/home/maksim/ghidra_scripts/b7a4/` (own build state, immune to the other
agents' inline scripts). Recommended for any later batch.

## Renames (9)

All had an embedded label the body disproves.

### Menu / screen setup (5)

Each is a 570–684-byte GUI pass that walks `GUI_ELEMENTS`, finds
`<SCREEN>_BLACK`, copies its rectangle/scale fields (`+0x3d0/+0x3d4/+0x3d8/
+0x3e4/+0x478/+0x47c`) into the global shade variables (`DAT_143a1196c`,
`DAT_1403c0e58/5c`, `DAT_1403c12e8/ec`, `DAT_143a11970`) and links
`GLOBAL_143944470` to the element's `+0x498` link — i.e. it makes that backdrop
the active screen shade — then invokes the per-screen helper with the screen
name and `LocalFileReadAndUpdate(<name>)`, and clears `DAT_147fc6fcd`.

| addr | new name | evidence |
|---|---|---|
| 0x1402432f0 | `Menu_SetupLoadGameScreen` | `LOADGAME_BLACK` → shade globals; helper(`LOADGAME`) + `LocalFileReadAndUpdate("LOADGAME")` |
| 0x140243530 | `Menu_SetupQuitScreen` | same for `QUIT_BLACK`/`QUIT` |
| 0x140243770 | `Menu_SetupSaveGameScreen` | same for `SAVEGAME_BLACK`/`SAVEGAME` |
| 0x1402439b0 | `Menu_SetupSaveNameScreen` | same for `SAVENAME_BLACK`/`SAVENAME` |
| 0x140242e60 | `Menu_SetupTutorialScreen` | sets `+0x3cc = 10` on `LOGO_L`, `LOGO_R`, `ROLL_DESK`, then helper(`TUTORIAL`); the old `memcmp` label was already flagged wrong on 2026-10-17 |

Callers of all five: `!ClickFunc`, `Input_DispatchPadDirectionKey`,
`Dialog_HandleAnswerKey` (0x140242e60: `creatureLogic`).

### Game logic (3)

| addr | new name | body evidence |
|---|---|---|
| 0x140225c00 | `Volume_LoadAndRecenter` | `LoadSeriaFile` into a `New(0x128)` Node, name `"ROOT_LOAD_VOLUME"`, `AssignRandomId(1)`, then subtracts the mean position of all class-`0xf` children and adds the caller's `Vec2` target, re-centring the volume. Strings `ERR: load_volume failed to load from file %s`, `APP::load_volume %s break (unable to remove objects from volume)`. |
| 0x140268de0 | `City_EnterSuppliesScreen` | gated by profile property `CALCULATE_FUEL`; picks the profile design nearest `PLAYER_ESCADRA_` and writes the fuel figure `((d+300)*1000*escadra[+0x4a8]/escadra[+0x494]-escadra[+0x498])` (clamped ≥0) to `CURRENT_LOCATION+0x26c`; then resets the map view bounds, `Fleet_SetVolume(0)`, `supplyRoom()`, sets `DAT_147fc6fc9 = 1` (bc9 = the supplies/shop screen per `docs/rendering/ui-events-and-screens.md`) and plays `Floor` / `gas_lamp_02`. |
| 0x1402a8ed0 | `Profile_UnlockShip` | looks a design up by name (`+0x152`) in the global name tree `DAT_143a1c220` and the active profile tree (`profile+0x430`); if the entry's `+0x30` is 0 and the design's `+0x339` announce byte is clear, `displayOnUI_` with key `UNLOCK_SHIP`, then writes `1.0f` to `+0x30`. |

### Render (1)

| addr | new name | body evidence |
|---|---|---|
| 0x14030e670 | `VideoTask_RenderFadeScene` | `Gfx_DrawFullscreenQuad`, grey→green ramp from `cosf`/`powf`/`sinf` of the frame phase scaled by `ZOOM_LEVEL`, pushed into the render property block, then a 40,000-record loop in 100-element rows emitting `Gfx_QuadRenderEx` quads coloured by the ramp. Reached only when `VideoTask_Dispatch` (0x140300c20) receives index 1 — the colour-fade branch. |

## Promoted identities, not renamed (6 q3 rows + the 21 new-to-q3)

The rows are in the TSV; the notable ones:

* **0x140314290** (4,840 B, read): strategic-map **radar sweep**. Radar angle
  `PLAYER_ESCADRA_+0x43c` advances `0.02*DAT_1403c2db0` per frame, mode `+0x444`
  goes 2→1 when the `+0x448` timer expires, detection range `+0x4d0` gives the
  scale `128/range`, then every profile ship/craft/item inside the radius is
  drawn and the `MAPMODE_RADAR_SHORT`/`MAPMODE_RADAR_GROUND` buttons are pressed
  over `MAP_MAP`. Left `stale` because the caller-facing name is not proven.
* **0x140315580** (1,469 B, read): **HUD zoom-view overlay** —
  `Hud_DrawZoomGrid` + `Hud_DrawNoiseFrame` + `SetAimRectZoom` with
  `ZOOM_LEVEL`-scaled extents, prebloom/outline shader coloured from
  `Get_Profile()->enigmaKey9` and the `DAT_143a11994/119d0` phase.
* **0x140315b40** (1,140 B, read): **500-bin bearing trail** — a 500-float ring
  at `0x148075fb0` advanced `+0.2` per bin, multiplied by HGE `Random_Float`,
  indexed by `(body+0x454)/2π*500`, 0x100 quads coloured by the ring value;
  per-body index stored at `+0x474`.
* **0x140316230** (1,919 B, read): ship-card/HUD **transform-vector builder** —
  `Vector_Resize40` over the 0x20-stride `DAT_148021ca8`, per-record virtual
  `+0x18`, 0x28-byte `{pos,angle}` tuples, 5-pair vector into
  `DAT_143a13998+0x1e0`, min/max rect from corners `[0x17]/[0x2d]/[0x43]`.
* **0x1403182a0** (138 B) timer/delta-clamp helper around `_Xtime_get_ticks`
  (10,000 ticks = 1 ms); **0x140318920** (211 B) builds two `b2DistanceProxy`
  plus a `b2DistanceInput` and calls `b2Distance`, discarding the output
  (wrapper only, no stock b2 name).
* **0x140293dc0 / 0x140293ea0** (218/234 B, read): remove a node from the
  doubly-linked list at `owner+0x2c0` whose `std::string` member (`+0x50` and
  `+0xb0` respectively) equals the key, decrement `owner+0x2c8`, free the node
  and call its virtual deleting destructor. Two keyed lists on one owner.
* **0x1402e3580** (4,845 B, read): sound-name normaliser — copies the name,
  strips the last 3 chars (`_NN` take suffix), matches ~30 base names
  (`bladaway`, `ricochet`, `war_attack`, `krank_*`, `voice_alert`, `manhit`, …)
  and rolls HGE `Random_Int(1,N)` per name. **No return value or side effect
  could be proven** (the copy is local and tidied at the end), so it stays
  `stale` — this is the one lead that a later pass should revisit with the
  caller (`pageSpecialEffect?`) in view.
* **0x1402898f0 / 0x140289970 / 0x140289ca0** (read): member destructors called
  only from `Location_Destructor` (vector `+0x18..+0x28` + object `+0x8`;
  a second variant with a different element dtor; and vtable-slot-`+0x48` object
  plus two `std::list`s). Naming still needs the `Location` member offsets.

## The `0x140300000–0x140336FFF` tail (new relative to q3)

* 5 `VideoTask` scene routines stay `stale`: `0x140300db0` (17,122 B, editor
  branch), `0x1403050a0` (19,645 B, battle branch), `0x14030a6b0` (16,304 B,
  campaign/map branch), `0x14030f250` (17,814 B, title/loading branch) — all
  >0x2000 so not decompiled — plus `0x14030e670`, which was read and renamed.
  The branch→screen mapping is now anchored by
  `docs/rendering/ui-events-and-screens.md` and
  `docs/findings/source-file-names.md`, so a later pass can name them from
  dispatch + screen table if the parent accepts caller-side proof for bodies
  that are deliberately not decompiled.
* **0x140336c80 / d20 / df0 / ea0 / f00**: five 60–90-byte `_CxxThrowException`
  **EH handler funclets** (delete a buffer / restore via memmove, then
  `_CxxThrowException(0,0)`). Each is referenced from the `.pdata`/funclet block
  `0x148088ab8–0x148088b3c`, unwind `0x140385d7c`, `0x140385de4`
  (FuncInfo4 `0x140385e20`), `0x140386084`, `0x1403861e4` (FuncInfo4
  `0x140386208`), `0x14038622c` (FuncInfo4 `0x140386240`), handler
  `__CxxFrameHandler4`. **Owner not resolved** — the packed FuncInfo4 layout was
  not decoded; these are the 5 `/EH` objects b6 agent 9 deferred to "agent 1",
  but they sit below `0x140337000` and are not in the ownership TSV, so they are
  in this range. Hand-off: whoever decodes the FuncInfo4 (agent 1 has the
  tooling for `0x140337000+`) can name them `<Owner>_EhCleanup_<n>`.
* `0x140334b70` (182 B) is the MSVC **GUI-app startup stage**:
  `_set_app_type(2)`, `_set_fmode(0x4000)`, `__p__commode`,
  `__scrt_initialize_onexit_tables(1)`, `_initterm` over the empty xi table,
  `atexit`, `_configure_narrow_argv`, `__setusermatherr`, `_configthreadlocale`,
  `_initialize_narrow_environment`, failure `__scrt_fastfail(7)`.
  `mainCRTStartup` is separate at `0x140334c54`, so this is a startup helper;
  no exact CRT symbol name provable.
* `0x140334c28`, `0x140334de0`, `0x140334e43`, `0x14033535c`, `0x1403353a4`
  are 13–60-byte CRT thunks/initialisers (details in the TSV).

## Counts

* renamed: **9**, all plated
* stale label recorded (carried + re-checked): **340**; 36 rows appended to q3
* unreadable: **0**
* bodies >0x2000 deliberately not decompiled: **4** (`0x140300db0`,
  `0x1403050a0`, `0x14030a6b0`, `0x14030f250`), catalogued structurally
* `rep_*` left in range: **338** (340 expected minus the 2 renamed by other
  agents mid-pass)
* functions created: **0**

## Hand-offs

1. The 4 big `VideoTask` scene bodies: accept caller-side names
   (`VideoTask_RenderEditorScene` / `BattleScene` / `MapScene` / `TitleScene`)
   or read them with the >0x2000 rule lifted. Branch conditions are in
   `VideoTask_Dispatch` 0x140300c20.
2. The 5 EH handler funclets at `0x140336c80–0x140336f00`: decode FuncInfo4
   `0x140385e20` / `0x140386208` / `0x140386240` for the owner.
3. `0x1402e3580` sound-name normaliser: the caller `pageSpecialEffect?` and the
   HGE `Random_Int` result are needed to decide whether this is a *selector*
   (returns an int in EAX that Ghidra typed away) or a pure filter.
4. `0x140314290` radar sweep: the caller set (6 sites incl. two vtable-like data
   refs) should pin the name.
