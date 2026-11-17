# The "500 global": one shared `500.0f` literal and every reader of it (1.163)

Roadmap item 2 (`MOD_ROADMAP.md`, "Decouple the 500 global"). The user found the effect live with
Cheat Engine on 1.151: editing one value changed **three** unrelated things at once — the engine
overheat trip, the length of the enemy's pre-fire gun laser, and rocket acceleration.

**Answer: it is not a variable, it is a pooled float literal.** 1.163 has exactly one `500.0f` in
the constant pool, at **`0x140352838`**, and **82 instructions** read it. Writing to it changes all of
them (which is what Cheat Engine did); *decoupling* means giving the chosen sites their own float,
not editing the pool entry.

* 1.151 counterpart: `0x1403263f4` (`00 00 FA 43`), read by 40+ instructions. The 1.151 site named in
  the roadmap, `0x140034230` (inside `creatureLogic` `0x1400335b0`), is
  `F3 0F 59 0D BC 21 2F 00` = `MULSS XMM1, [0x1403263f4]` — one of the pool's many readers, not the
  global itself.
* 1.163 pool neighbourhood (`inspect_memory_content 0x140352830`, all floats):
  `0x140352830` 300.0, `0x140352834` 400.0, **`0x140352838` 500.0**, `0x14035283c` 600.0,
  `0x140352840` 700.0, `0x140352844` 1000.0.
* Every reader listed below is a plain `OP xmm, dword ptr [0x140352838]` with the RIP-relative disp32
  as the **last 4 bytes** of the instruction, so a site can be retargeted at a mod-owned float by
  rewriting only those 4 bytes — provided the mod's float is within ±2 GiB (allocate near the image
  base, not in the mod DLL).

Method: `search_instructions operand_pattern=140352838` (82 hits, addresses and function names below
are from that listing, opcode bytes verified with `disassemble_bytes`/`search_instructions`), plus
`get_xrefs_to 0x140352838` for the cross-check. Function names are the names in the 1.163 Ghidra
database as of 2026-11-17.

## The three features, and the sites that belong to them

| feature | sites | instruction | what it does |
|---|---|---|---|
| **engine overheat trip** | `0x14002861c` `Engine_ApplyThrustForce` | `COMISS XMM0, [500]` | `T = part+0x2ec >= 500` -> store `+0x810 = 3.0` (lockout), return without force. The only overheat test in the game; `Part_Tick` only counts the lockout down. |
| **enemy pre-fire gun laser** | `0x14029d538`, `0x14029d540`, `0x14029d82a`, `0x14029d832` `BattleHud_DrawCombatMarkers` (`0x14029c5c0`, called from `combatEvents`) | `MULSS XMM6/XMM7, [500]` (two pairs) | end point of the per-gun aim line: `end = gunWorldPos + unit(aimPoint - hull) * 500`, drawn with `Gfx_DrawWorldLine` in red `0xFFDD2727` (cyan `0xFF00E4FF` for calibre logic 160, yellow `0xFFFFDE00` when the ammo flag `+0x164` is set). Gated on `0.0 < creature+0xad4` being **false**, i.e. **these lines are drawn for enemy ships only** — the "pre-fire laser". Two loops = gun groups 0 and 1 (`+0x13a8..13b0`, `+0x13c0..13c8`). |
| **rocket acceleration** | `0x1400348f2` (logic 130), `0x140034c0c` (logic 132) `creatureLogic` | `MOVSS XMM7/XMM9, [500]` | burn thrust: while `+0x3d4 > 0` (1.5 s), a force of `mass(+0x1d8) * 500` is applied along the body heading (`+0x8fc`) through vtable `+0x178` = **500 u/s² for 1.5 s**. Verified: `MOVSS XMM1,[RSI+0x1d8]; MULSS XMM1,XMM7` at `0x14003493f`, then `CALL [RBX+0x178]`. |
| **rocket path preview (same knob)** | `0x1402a02d6`, `0x1402a02e4`, `0x1402a04c4`, `0x1402a04d1` `BattleHud_DrawCombatMarkers` | `MULSS XMM13/XMM14/XMM6, [500]` | the dashed lime `sign_aim`-style **predicted trajectory** of a rocket weapon: it integrates `v += accel*dt` for `1.5 s` at the frame rate with gravity `9.82` (separate literal at `0x1402a02..`) and draws the path. **These must follow the real thrust value**, otherwise the reticle lies about where the rocket goes. |

Total: 11 of the 82 readers. The other 71 are unrelated (AI internals, aircraft, screens, GUI,
shipworks, city generation); see the table below.

## All 82 readers

`OP` column = how 500 is used (threshold / scale / offset / divisor). "not read" = the function was
not opened for this report; the role comes from its name and the instruction shape. Sites marked
**[gameplay]** could plausibly be worth a knob of their own later; the rest is UI/screen/editor code.

### combat / physics / ordnance

| site | function | OP | what it does |
|---|---|---|---|
| `0x14002861c` | `Engine_ApplyThrustForce` | COMISS | **overheat trip** (see above) |
| `0x1400348f2` | `creatureLogic` | MOVSS | **rocket thrust, logic 130** (cluster rocket, 1.5 s burn) |
| `0x140034c0c` | `creatureLogic` | MOVSS | **rocket thrust, logic 132** (300 mm rocket) |
| `0x1400448e9` | `creatureLogic` | SUBSS | missile-warning GUI element: `ammo/sprite field +0x154 - 500` next to `field +0x150 - 600` (the 600 is `0x140352840`), then styles `gui_std_click`/`gui_std_focus` and the `flash_large_shadow` animation are set up — the incoming-missile flash, not flight physics |
| `0x14029d538`, `0x14029d540`, `0x14029d82a`, `0x14029d832` | `BattleHud_DrawCombatMarkers` | MULSS x2 | **enemy pre-fire gun laser length** (see above) |
| `0x14029e943` | `BattleHud_DrawCombatMarkers` | MOVSS | third float argument to `renderGuiFlashes?` `0x140243cf0` (the HUD's per-body flash/glow renderer) — a size/scale, not physics |
| `0x14029f1d1` | `BattleHud_DrawCombatMarkers` | MOVSS | thruster glow: `intensity = thrust_field / 500` summed over the ship's thrusters (the `thrusters` loop at line ~1344 of the decompile) |
| `0x1402a02d6`, `0x1402a02e4`, `0x1402a04c4`, `0x1402a04d1` | `BattleHud_DrawCombatMarkers` | MULSS x2 | **rocket path preview acceleration** (see above) |
| `0x1401c7716` | `FX_SpawnExplosionDebris` | MOVSS | debris spawn spread/size scale — **not read**; purely visual |

### AI  **[gameplay]**

| site | function | OP | what it does |
|---|---|---|---|
| `0x140063857`, `0x140063860` | `AiShipTick` | MULSS x2 | x/y components of a point at 500 units along some direction (a waypoint / dodge offset) — not read further |
| `0x140063b90` | `AiShipTick` | MOVSS | `500 / (dist + k)` — an inverse-distance factor; not read further |
| `0x140063c75`, `0x140063c8c` | `AiShipTick` | MOVSS | two branches loading 500 into the same local; not read further |
| `0x140063ed4` | `AiShipTick` | MOVSS | not read |
| `0x140064812` | `AiShipTick` | MOVSS | not read |
| `0x140064e56` | `AiShipTick` | MOVSS | not read |
| `0x14006cf63` | `AiShip_SteerController` | MOVSS | 500 loaded as a max value next to `[RDI+0xd78]` and pushed as a stack argument to a vtable call — a clamp on the steering output, not read further |
| `0x14007b81a` | `AiWeaponController` (`0x14007a8d0`) | MOVSS | the group-1 branch for guns whose ammo `Stats+0x144 == 0x34` (calibre 52 = 220 mm rocket): passes 500 as an argument to the lead/predict call at `0x14007b833`-ish |
| `0x14006c24d` | `rep_140068980_...atan2f` (misnamed; an AI/rhetoric function) | ADDSS | 500 added to an angle/offset — not read further |
| `0x14006c611` | `Creature_TryDropBomb` | MOVSS | bomb-drop test offset — not read further |

### aircraft

| site | function | OP | what it does |
|---|---|---|---|
| `0x14000871f` | `Aircraft_CollectAvoidanceObstacles` | MOVSS | avoidance radius/weight |
| `0x14000c40d` | `AircraftLogic_Mode3_Bomber` | MOVSS | bomber-mode distance/altitude constant |
| `0x14000d680` | `AircraftLogic_Mode6_Default` | MOVSS | default-mode constant |
| `0x14000eda7` | `AircraftLogic_SetState` | MOVSS | state-entry constant |
| `0x14000f5f2` | `AircraftLogic_LaunchAAMissile` | COMISS | AAM launch range test `<= 500` |

All five: not read beyond the instruction; the aircraft layer only matters while planes are up.

### battle / campaign spawn plumbing

| site | function | OP | what it does |
|---|---|---|---|
| `0x1400ed4fc` | `initProfileMissiles?` | MOVSS | strategic-layer missile inventory init (a 500-scale) |
| `0x1400f0698` | `Escadra_UpdateEscortOffset` | MOVSS | escort formation offset scale |
| `0x1400f5ead` | `StrategicFleet_SelectPursuitTarget` | COMISS | pursuit range test on the map |
| `0x14011a8df` | `Escadra_UpdateContamination` | MOVSS | contamination spread scale |
| `0x14027b935` | `addShipsToSilentStrikeGRP?` | MOVSS | strike-group layout |
| `0x1402c9d42` | `SCR_COMBAT_SpawnPlayerShip` | MOVSS | battle-start offset (spawn / camera) |
| `0x1402ce656` | `SCR_COMBAT_ReturnToMap` | MOVSS | return-to-map layout |
| `0x1402cec87` | `SCR_COMBAT_SKIRMISH_ReturnShips` | MOVSS | skirmish return layout |
| `0x1402cfd90` | `SCR_CRAFTS_VS_CRAFTS` | MOVSS | craft-vs-craft mode layout |
| `0x1402d4d15` | `SCR_MISSILE_SpawnDefenders` | MOVSS | missile-defence spawn spread |
| `0x1402d6f2d` | `deployFromReserve` | MOVSS | reserve deploy offset |
| `0x1402d71d3`, `0x1402d71db` | `Battle_SpawnQueuedShipForSlot` | ADDSS/SUBSS | queued-ship slot x/y nudge (500 either side) |
| `0x1402ebcdd` | `Ground_SpawnAlongPath` | MOVSS | ground-unit path spawn spacing |
| `0x1402f1486`, `0x1402f1b0d`, `0x1402f281c`, `0x1402f2e71` | `generateCityLandscape` | SUBSS/MOVSS | city/terrain generation distances (**relevant to roadmap 7**) |

None of these are read in detail; they are map/screen geometry, not combat math.

### screens, maps, GUI, editors

| site | function | OP | what it does |
|---|---|---|---|
| `0x1400b00fc` | `mainDialogWithChoices` | ADDSS | dialog/text layout |
| `0x1400c753f`, `0x1400cc684`, `0x1400cdd14`, `0x1400ce1ce`, `0x1400cee04` | `somethingShipworks?` | MOVSS | shipworks editor view/panel math |
| `0x1400d95d2` | `displayinShipworks?` | MULSS | editor zoom/scale |
| `0x140108b32` | `displayAircraftStrategicMap` | MOVSS | map marker scale |
| `0x140138af5` | `!ClickFunc` | MOVSS | main click handler, layout constant |
| `0x140146b73` | `setupPropsSecondaryMapModes` | DIVSS | map-mode divisor |
| `0x1401a8b36` | `!FrameFunc` | MOVSS | per-frame layout |
| `0x1401c4915` | `Gui_BuildBayonetsPanel` | MOVSS | panel layout |
| `0x1401c6591` | `Dialog_BuildBriefingPanel` | MOVSS | briefing text layout |
| `0x1401d96db` | `setFontMaxSize?` | SUBSS | font metric |
| `0x1401dbf1a` | `Landing_BuildPrelandingPanel` | MOVSS | landing panel layout |
| `0x1401fd354` | `secondaryPrecombatButtons` | MOVSS | pre-combat button layout |
| `0x140203034` | `rep_1401e8a70_VCRUNTIME140::memmove` (misnamed) | MOVSS | GUI copy path, layout constant |
| `0x14021464d` | `rep_1401f85c0_HEAP::free` (misnamed) | MOVSS | GUI object teardown, layout constant |
| `0x140215489` | `rep_1401f9490_CRT-MATH::atan2f` (misnamed) | MOVSS | GUI/aim helper |
| `0x140229b81` | `renderStuffToMap?` | MOVSS | map render scale |
| `0x140236ae5` | `creditsScreen?` | MOVSS | credits scroll |
| `0x14026bec2` | `UpdateZoom` | MOVSS | zoom limits |
| `0x140287006` | `SomethingPreTask` | MOVSS | per-frame layout |
| `0x1402a0980` | `handleLandingGUI?` | MOVSS | landing HUD layout |
| `0x1402b5f66`, `0x1402ba377`, `0x1402be726`, `0x1402c066b`, `0x1402c0c44` | *(no function defined — undefined code inside the scene functions)* | MOVSS | scene/GUI code, not read |
| `0x1402c6d07` | `SomethingWithLevelSerias` | MOVSS | level-seria loading layout |
| `0x140303d97` | `VideoTask_RenderEditorScene` | DIVSS | editor render divisor |
| `0x140315c47` | `ShipCard_DrawBearingTrail` | MOVSS | ship-card trail length |

## Consequences for the decoupling

0. **The enemy aim laser is not decoupled, by user decision (2026-11-17):** the reticle must stay
   vanilla, so its four readers (`0x14029d538`/`d540`/`d82a`/`d832`) are deliberately left on the pool
   value. `hf_tuning` v0.3.0 removed the knob it briefly had.
1. Two knobs, 7 sites: `engine_overheat_threshold` (1), `rocket_acceleration` (6, the 2 thrust sites
   **plus** the 4 preview sites so the reticle stays truthful).
2. The remaining 75 readers keep reading the vanilla pool entry at `0x140352838` — untouched.
3. Do **not** write to `0x140352838` itself: that is the 1.151-era behaviour that coupled everything.
4. A site patch is 4 bytes (the disp32 at the end of the instruction), so the mod can keep the value
   in its own memory near the image base and even change it live.
5. Open / not verified: whether the two preview blocks use 500 anywhere else as a *drawing* step
   rather than the acceleration (the decompile shows it only in the two `v += a*dt` updates, so it is
   the acceleration); whether the AI's calibre-52 branch in `AiWeaponController` uses 500 as a *time*
   or a *distance* (not read); what `renderGuiFlashes?` does with its 500 (not read).
6. `MOD_ROADMAP.md` item 7 (docks) and item 14 (gravity) touch four readers here
   (`generateCityLandscape`) and the preview's own `9.82` literal respectively — no overlap, but worth
   remembering that the city generator shares this pool entry.
7. Built as `hf_tuning` v0.1.0 (`AI funnies\hf_tuning`): the values are floats in a page allocated
   next to the image base, and each site has only its disp32 rewritten (`end + disp = our float`).
   Nothing is written to `0x140352838`.
   **Trap that cost a play test (v0.2.0 → v0.3.0):** Windows rounds an unaligned `VirtualAlloc`
   reservation **down** to the 64 KiB allocation granularity. Scanning for a page by asking for the
   first byte of each free region (`BaseAddress + RegionSize`, i.e. the end of the image) always
   rounded back *into the image* and failed, so the page was never allocated and no scalar site got
   patched — while the hook features, which need no page, kept working. Candidates must be rounded
   **up** inside the region, and the allocation failure must not abort the whole mod.

## Per-`m_oid` overrides (v0.2.0, 2026-11-17)

Both remaining features are now also tunable per engine and per ammo item, which needs code rather
than a displacement rewrite. Both hooks are in `hf_tuning`; their sites:

* **engine overheat per `m_oid`** — hook on `0x140028614` `MOVSS XMM0,[RSI+0x2ec]` in
  `Engine_ApplyThrustForce` (8 bytes), resume at `0x14002861c` (the untouched `COMISS`). The callback
  returns `T + (scalar − per_oid)` so the vanilla `>= 500` compare tests the engine's own threshold.
  The `m_oid` is `Body +0x190` (EscadraString), read per call — no state to invalidate.
* **rocket acceleration per ammo `item_name`** — the rocket body carries **no** ammo identity:
  `FireShell`'s rocket cases build it inline (`New(0xa40)` + `Body_Constructor` + `CreateShell_`),
  never call `Body_InitializeCannonShell`, set no `+0x490` gun link and no `m_oid`; all they copy is
  `explosivePower`, `logic` (from `ammo->caliber`) and `ttl`, and NAR122 / 220 mm / NAR340 all share
  logic 130. The Ammo record is live at the four `body->logic = ammo->caliber` stores —
  `0x140030e90` (body RBX), `0x1400313c4` (RSI), `0x1400319d0` (RBX), `0x140031c46` (RSI), Ammo always
  in `R15`, six bytes `89 83/86 C4 03 00 00` — so a hook there stores `body → accel` in the mod's
  own map and the two burn sites (`0x1400348f2`, `0x140034c0c`) ask it. Entries are dropped when the
  burn timer `+0x3d4` reaches 0.
* The 300 mm rocket (logic 132) can also be launched as a *ship part* (`creatureLogic` state 0); that
  path never passes the four stores and keeps the scalar.
* **burn time (v0.4.0)** — `Body +0x3d4` (`m_logic_f2`) is the burn timer, and the vanilla 1.5 s is
  stored in four places: `0x140030e9d` (`FireShell` rocket case, body RBX), `0x1400313d1` and
  `0x140031c53` (`FireShell` rocket cases, body RSI), and **`0x14003538e` in `creatureLogic` state 0 of
  logic 132** — the 300 mm rocket does *not* set its burn in `FireShell` (case 0x36 sets only ttl and
  the `+0x4a8` link), so that state-0 store is the one that covers it, for both the fired and the
  part-launched path. Each store is replaced by a callback writing the configured value; the rocket
  glow particle life is read from `+0x3d4` right after the store, so the visuals follow.
* Interoperability: the hook sites are disjoint from `ammo_extended` (FireShell switch
  `0x1400302c8`), `hf_gun_mechanics` and `qol`; all three mods install through patchy-rs, whose
  `validate_patch_sources` / `ensure_patches_do_not_overlap_installed` make a same-bytes conflict a
  clean `SourceChanged` / `OverlappingPatch` error rather than corruption.

