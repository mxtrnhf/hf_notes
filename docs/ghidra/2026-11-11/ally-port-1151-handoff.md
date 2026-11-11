# Porting hf_ally (and hf_ai hook-style code) from 1.163 to 1.151 - handoff

Written 2026-11-11 for an agent porting the `highfleet-allies` mod family from
Steam 1.163 (the version the mods are built for) to Steam 1.151. This file is
self-contained: every address below was verified in the respective binary, and
the evidence pages live in the `hf_notes` repository under
`docs/ghidra/2026-11-11/` (full machine tables in `data/`: the function map
`modaddr_163_151.tsv`, the field/global map `fields_163_151.tsv`, the verified
pair tables `matched.tsv`..`matched4.tsv`).

Both binaries: image base `0x140000000`, x64, MSVC. The 1.151 Ghidra program
is `Highfleet.exe.unpacked.exe v1.51`, the 1.163 one is
`Highfleet.exe.unpacked.exe` in the `HighfleetServer` project.

## 1. What the mod family uses, and where it lives in 1.151

Function-level mapping (1.163 -> 1.151), all verified by identical/near
identical mnemonic bodies, mapped-callee/caller sets, or exact strings:

| purpose (hf_ally const) | 1.163 | 1.151 |
|---|---|---|
| ADD: creature add/remove (vtable) `ADD_RVA` | Creature_RegisterInWorldLists 0x14006bf60 | 0x1400687e0 |
| SPAWN: creature from template `SPAWN_RVA` | Creature_SpawnFromTemplate 0x1402672c0 | 0x1402454a0 |
| EXTRACT: ship back to fleet | rep_1401f3c10_APP:MoveVolume 0x14020ef30 | 0x1401f3c10 (same rep name) |
| BATTLE: arcade battle tick `BATTLE_RVA` | battleManagerTick 0x1402cc260 | 0x1402a52b0 (was handleRamming??) |
| DEPLOY `DEPLOY` + player deploy site `PLAYER_DEPLOY_CALLER` | deployFromReserve 0x1402d6e90 (call site 0x1402d6f7a) | 0x1402ad0b0 (was rammingCheckCollision??); site inside it, offset differs |
| SET_CONTROLLED | Profile_SetControlledShip 0x1402a7e30 | 0x140284160 Body_SetSlotOccupant (same functions, different name) |
| SET_LINK | SetLink 0x140194de0 | 0x140187120 SetLink |
| GET_PROFILE | Get_Profile? 0x140292a90 (3i tail-jump wrapper) | 0x14026ff50 Get_Profile (canonical getter) |
| CG dispatcher `PRECOMBAT_SEAM_TARGET` | TarkhanGUIDispatchOperator 0x140275850 | 0x140253b80 |
| precombat screen `PRECOMBAT_SEAM` 0x1402d88bb | buildPrecombatScreen 0x1402d7620 | mainPrecombatScreen 0x1402ad2e0 (equivalence; PRECOMBAT string sets match) |
| squad screen `PRECOMBAT_B1/B2_SEAM` 0x1402d752a/0x1402d75f2 | buildSquadPrecombatScreen 0x1402d73a0 (134i) | INLINED into mainPrecombatScreen 0x1402ad2e0; B2 seam = the TGDO call at 0x1402ae333; B1 region aligns near 0x1402ad8e5 - re-derive per-instruction at port time |
| operator new `GUI_NEW` | New 0x140334094 | 0x140309078 New |
| GUI ctor `GUI_CTOR` | GUI_2 0x14012a910 | 0x140121c30 GUI_2 |
| `GUI_SETPOS` | setXposYpos 0x1400520b0 | 0x14004fb90 setXposYpos |
| `GUI_SETBG` | SetBackground? 0x14001be50 | 0x14001b950 SetBackground? |
| `GUI_RESET` | resetGuiStrings 0x14015cc30 | 0x140151880 rep_CopyString (ICF fold collision, label kept) |
| `GUI_FIND` | FindGuiElement 0x1401a9170 | 0x140199890 FindGuiElement |
| `INPUT_TASK` | SomethingInputTask 0x14018dbf0 | 0x1401804a0 (365i vs 579i - 1.163 added features) |
| `CLICK_ENTRY` | !ClickFunc 0x14012f120 (13172i) | !ClickFunc 0x1401261d0 (12238i). NEVER decompile directly (crashes Ghidra); script-only |
| `TARGET_FN` | AiShip_ChooseTarget 0x140078b40 | 0x140074bb0 (was a CRT-free mislabel) |
| `FLUSH` | checkD3DEngineStatus? 0x140083b50 | 0x14007f300 |
| `GET_FONT` | LoadNameIntoMedia 0x1401703e0 | 0x1401648f0 (+ICF twins) |
| `STYLE_FONT` | Font_SetupByName 0x1401a8710 | 0x140198e70 rep_LoadNameIntoMedia (ICF fold) |
| `FONT_RENDER` | displayLableRotation? 0x14016eb40 | 0x140163050 |
| `PLAY_SFX` | playSFXSound? 0x1402e30e0 | 0x1402b7950 playSFXSound? |
| radio | PlayRadioSounds? 0x1402d5910 | 0x1402abb30 PlayRadioSounds? (whole body identical) |
| `AMMO_PRESS` | ammoSelectButtonPress? 0x14026f880 | 0x14024dcc0 |
| level loader (writes LEVEL_NAME) | SetLevelSeriaToLoad? 0x14025afd0 | 0x140239190 SetLevelSeriaToLoad? |
| dead nodes (telemetry detours) | CollectDeadNodes 0x1401be250 (sites 0x1401be274/0x1401be2f8) | CollectDeadNodes 0x1401ade20 (site offsets differ, re-derive) |
| fuel burn site | Creature_SetPartsOwnerRef 0x14007a160 (site 0x14007a210) | 0x140075bb0 |
| Shipworks TWR site (hf_ai) | displayinShipworks? 0x1400d6f70 (site 0x1400d7443) | 0x1400d1dc0 displayinShipworks? |
| hf_ai intercept hook | AiShip_BuildThreatList 0x1400625a0 (site 0x140062812: checkShipPartFlagActive call) | PopulateEngagementQueue 0x1400601a0; checkShipPartFlagActive 0x140047960 |
| hf_ai TICK/STEER/BOOST/ARM/ROLL/LAUNCH sites | all inside AiShipTick 0x140062f90 | all inside TacticalAI_MasterUpdate 0x140060b50 |
| hf_ai flare hook + CREATURE sites | CreatureUpdate 0x14007eb50 (hook 0x14007f864) | UpdatePlayerShipTactical 0x14007a2b0 |
| hf_ai RELEASE `RELEASE_RVA` | FireFlareLauncher 0x14002eed0 | LaunchFlare? 0x14002f6f0 |
| hf_ai LAUNCH | LaunchZenithAtOwnerTarget 0x14002ff60 | BindHardpointTarget 0x140030720 (51i vs 88i - moderate evidence, re-verify) |
| hf_ai FLARE_CRASH | creatureLogic 0x140033b90 (site 0x140036bb5) | creatureLogic 0x1400335b0 (2829i vs 5422i - huge drift, re-derive site) |
| hf_ai CREATURE_BODY / GetRootPart | Node_GetRootPart 0x140048fc0 | traverseLinkedListCreature? 0x140046c70 (identical body, flagged name clash) |
| hf_ai STATS `STATS_RVA` | GetStats 0x140281e00 | GetShipPart 0x14025fb50 (identical body, flagged name clash) |
| hf_ai DISTANCE | magnitudeCreatureBodyVector 0x14020fb80 | 0x1401f47f0 (same name) |
| hf_ai returnMass | returnMass 0x1400486e0 | 0x1400463c0 |
| hf_ai CHECK `CHECK_FN` | checkShipPartFlagActive 0x140049470 | 0x140047960 |

Same-function-different-name pairs where both names are meaningful (do not
"fix" them without talking to the 1.163-side owner): battleManagerTick was
handleRamming??; deployFromReserve was rammingCheckCollision??; Profile_SetControlledShip
= Body_SetSlotOccupant; buildPrecombatScreen = mainPrecombatScreen; AiShip_BuildThreatList
= PopulateEngagementQueue; CreatureUpdate = UpdatePlayerShipTactical; AiShipTick
= TacticalAI_MasterUpdate; FireFlareLauncher = LaunchFlare?; GetStats = GetShipPart;
Node_GetRootPart = traverseLinkedListCreature?; LaunchZenithAtOwnerTarget =
BindHardpointTarget (moderate); aircraftStateHandler = AircraftLogicStateMachine.

## 2. Data globals (labels already applied to the 1.151 Ghidra program)

| mod constant | 1.163 | 1.151 (label in program) |
|---|---|---|
| CLOCK / GAME_TIME | 0x143a119c0 | 0x143942540 CLOCK |
| HGE_PTR | 0x143a119e0 | 0x143921f70 HGE_PTR |
| CREATURES_BEGIN/END | 0x143faa5d8/5e0 | 0x143ed10d8/0x143ed10e0 |
| NEG_BEGIN/END | 0x143faa5f0/5f8 | 0x143ed10f0/0x143ed10f8 |
| AI_BEGIN/END | 0x143faa608/610 | 0x143ed1108/0x143ed1110 |
| POS_BEGIN/END | 0x143faa638/640 | 0x143ed1138/0x143ed1140 |
| ZERO_BEGIN/END | 0x143faa650/658 | 0x143ed1150/0x143ed1158 |
| GUI_ROOT | 0x147fc6f88 | 0x147eed960 GUI_ROOT |
| SCRIPTED_SCENARIO / RNG_SCENARIO | 0x147fc6fdb | 0x147eed9b5 SCRIPTED_SCENARIO |
| BATTLE_RESULT | 0x147fc7004 | 0x147eed9dc BATTLE_RESULT |
| WAVE_TIMER | 0x147fc7020 | 0x147eed9f4 WAVE_TIMER |
| RESERVE | 0x147fc73b0 | 0x147eedd78 RESERVE |
| ENEMIES_BEGIN/END | 0x147fc73d8/73e0 | 0x147eedde0/0x147eedde8 |
| ROSTER_BEGIN/END | 0x147fc7590/7598 | 0x147eedea8/0x147eedeb0 |
| (role-2 vote map, See ChooseTarget) | 0x147fc7550 | 0x147eede68 Role2_VoteMap |
| FRAME_DELTA (dt) | 0x1403c126c | 0x140391184 (co-label; primary name there is time_related_global?) |
| ARENA_X_HIGH / X_LOW / Y_LOW | 0x1403c2bc0/2bc8/2bcc | 0x140392c38/0x140392c40/0x140392c44 |
| INIT_DIM_B / INIT_DIM_A | 0x143a13e5c / 0x143a158fc | 0x14394293c / 0x1439443dc |
| CONTROLLED_LINKS | 0x143a1c260 | 0x14394ad40 CONTROLLED_LINKS |
| DeadNodeList (CollectDeadNodes) | 0x143a2de10 | 0x143954920 DeadNodeList |
| INIT_ONE / DEPLOY_AGGR (f32 1.0) | 0x1403524d8 | 0x1403263e8 F32_ONE |
| INIT_SCALE | 0x140354698 | 0x140328518 INIT_SCALE |

NOT yet mapped (needs an xref pass from their 1.163 writers): LEVEL_NAME
0x1403c1390, GUI_LIST/GUI_COUNT 0x143a13ac8/13ad0, MEDIA_RES 0x143a119e8,
BODIES/BODY_COUNT 0x143a33c90/0x143a51150, AIRCRAFT_SELECTOR 0x1403bd008,
RETREAT_POINT 0x147fc7638, SCENE_SELECTOR 0x147fc6fc4,
CURRENT_LOCATION/PLAYER_ESCADRA 0x143a11940/0x143a13eb0, AMMO_LIST_BEGIN
0x143a13be0 (interp approx 0x1439426e0, verify), VC_BASE/AIM 0x1403c0dc0/0x1403c0dc8,
ZOOM_LEVEL 0x1403c11cc, INIT_F2/INIT_F3 0x148075ce8 (vtable-adjacent f32s -
redo per the 1.151 GUI layout), BG_MINUS_ONE 0x1403524ec.

## 3. Creature field offsets changed between builds - the port contract

The Creature/Part layouts are NOT identical. Verified by aligning 18 matched
twin functions and voting on displacement immediates:

| field (hf_ally/hf_ai constant) | 1.163 | 1.151 | status |
|---|---|---|---|
| side float `OFF_SIDE` | +0xad4 | +0xa9c | verified (7/8 votes) |
| target link `OFF_TARGET_LINK` | +0xaf8 | +0xac0 | verified |
| target node `OFF_TARGET` | +0xb00 | +0xac8 | verified |
| retarget timer `OFF_RETARGET` | +0xb28 | +0xaf0 | inferred (family delta -0x38) |
| waypoint x/y `OFF_WAYPOINT_*` | +0xbf0/+0xbf4 | +0xb88/+0xb8c | verified at the STEER site |
| fire-flag bytes `OFF_FLAGS` | +0xbbc..+0xbc0 | +0xb54..+0xb58 | verified (+0xbbe inferred +0xb56) |
| aggression `OFF_AGGRESSION` | +0xbc4 | +0xb5c | verified (15/15) |
| fuel at start `OFF_FUEL_AT_START` | +0xbd0 | +0xb68 | 2/3 votes |
| driver state `OFF_STATE` | +0xbdc | +0xb74 | verified, sites annotated |
| launch cooldown `OFF_LAUNCH_CD` | +0xd60 | +0xcf0 | 2/3 votes |
| role/mode `OFF_MODE_D70` | +0xd70 | +0xcfc | verified (12/12) |
| order `OFF_ORDER` | +0xc98 | +0xc30 | 2/2 votes |
| part cooldown/cooldowns `OFF_PART_*` | +0x848/+0x858/+0x860 | +0x834/+0x844/+0x84c | 0x848 inferred |
| fuel/capacity `OFF_FUEL(_CAPACITY)` | +0x1638/+0x1640 | +0x1588/+0x1590 | verified |
| position `OFF_POS_X/Y` | +0x1840/+0x1844 | +0x1784/+0x1788 | verified |
| weapons pair (ChooseTarget -20) | +0x15e8/+0x15ec | near +0xc0c/+0xc10 | UNRESOLVED: widths changed, manual review needed |
| active flag | +0x48 | ? | UNRESOLVED |

Struct-level sizes also changed (the 19 differing structs incl. Creature,
Profile, Body, GUI were deliberately never merged in the bulk type import) -
never assume any 1.163 offset; use this table and the full data TSV.

## 4. Porting procedure (per hook)

1. **Entry hooks** (ADD, SPAWN, BATTLE, DEPLOY, INPUT_TASK, CLICK): read the
   first ~12 bytes at the 1.151 entry above and update the mod's prologue
   constants + validation patterns. Mechanically: open the given address in
   Ghidra, copy the byte pattern, re-encode in the Rust `*_PROLOGUE` arrays.
2. **Callee functions** (pure calls with prologue check): same - update
   address + prologue bytes.
3. **Mid-function sites** (STEER, BOOST, ARM/ARM_CALL, COOLDOWN, ROLL,
   LAUNCH_ADDRESS, flare hook, dead-node detours, PLAYER deploy call site,
   PRECOMBAT seams):
   - Open the 1.151 containing function from the table above.
   - Use the 163 instruction as the *semantic* template (grep the 1.163
     listing for the site's operands - e.g. STEER: `movss [r14+0xbf0], xmm9`
     with the surrounding cmp/jcc pattern).
   - Find the equivalent instruction in the 1.151 function: grep by the
     *migrated* displacement (waypoint = `[r14+0xb88]` inside
     TacticalAI_MasterUpdate) or by the nearby landmark EOL comments placed
     in the 163->151 round (e.g. "1.163 twin 0x140064a8d ... -> here
     creature+0xb88" at 0x140061cbd is the hf_ai STEER site).
   - Re-derive the trampoline against the 1.151 register/stack state at that
     instruction: the stack slot abstractions (rbp+0x28 / rbp+0x48-style in
     BOOST_COMMAND) must be re-measured - layouts differ wherever 1.163 added
     code frames.
   - Prefer byte-pattern search of a 8-16 byte signature around the new site
     at runtime (like the mods do for prologue validation) over hard-coding
     the new absolute address where possible.
4. **Fields**: replace every `OFF_*` constant with the 1.151 offset from
   section 3. For the unresolved two (weapons pair, active flag) determine
   them with a runtime probe or a fresh decompile pass before use.
5. **Globals**: replace addresses from section 2; for the unmapped list, do
   an xref pass first (find their 1.163 writers in Ghidra, map the writer via
   `modaddr_163_151.tsv`, read the referenced 1.151 address from the twin's
   listing).

## 5. Validation ladder (same as the mods do today)

1. All prologue/signature checks must fail-safe (log + disable) when bytes do
   not match; the mods already do this - keep it.
2. Log-only build first (v0.1.x-style): hook everything, change nothing,
   verify the spawn/creature/battle logs produce sane values via the new
   offsets.
3. Field sanity gates: e.g. `side` must be small floats (-1..1),
   `waypoint` must be near ship coordinates, fuel must decrease monotonically
   during battle. These catch a wrongly migrated offset immediately.
4. Only then enable behavior (ally spawning etc.), one feature at a time.

## 6. Known traps

- ICF folding: several small functions exist in multiple byte-identical
  copies in 1.151 (e.g. the String_Tidy family has seven). When picking a
  call target, prefer the member confirmed by call-site evidence (recorded
  in data/matched2.tsv / matched3.tsv "via ..." notes).
- The spatial-delta heuristic used in bulk matching has both false rejections
  (five corrected in round 5) and a known false-acceptance guard; trust body
  evidence over address proximity.
- `!ClickFunc` (0x1401261d0) and `creatureLogic` (0x1400335b0) are enormous;
  only touch them through Ghidra scripts (listing iteration), never the MCP
  decompile path.
- The 1.151 `Creature` layout has NO datatype in the Ghidra DTM - offsets
  live in plates/comments and in `fields_163_151.tsv`; do not trust generic
  struct imports.
- Names that look wrong but are intended: `GetShipPart` == 163 `GetStats`,
  `traverseLinkedListCreature?` == 163 `Node_GetRootPart`,
  `BindHardpointTarget` == 163 `LaunchZenithAtOwnerTarget` (moderate),
  `PopulateEngagementQueue` == 163 `AiShip_BuildThreatList`. Flagged, not
  "fixed", in the 1.151 program.

## 7. Remaining unknowns / worth doing next

- The four content-unconfirmed no-twin leftovers: Aircraft_CollectActiveCraft
  (best candidate rep-free 0x14026d620, LCS 0.60), Profile_GetActive
  (rep_14007d750, LCS 0.69), Trail_DrawLayer (no candidate), Gfx_BuildFullscreenProjection
  (no candidate). None are mod-critical.
- The remaining ~45 mod globals of section 2's "not yet mapped" list.
- Payload verification of the GUI recipe constants (INIT_F2/F3 are adjacent
  to a vtable pointer in 1.163; the 1.151 GUI class layout differs).
- In-game validation of this whole round has NOT been performed - everything
  here is static-analysis evidence.
