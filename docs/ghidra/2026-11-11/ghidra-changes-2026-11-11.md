# Ghidra changes, 2026-11-11 (bulk port of v1.163 annotations into the v1.151 program)

Program: `Highfleet.exe.unpacked.exe v1.151` (project `HighfleetServer`),
image base `0x140000000` — **this pass changes the 1.151 program**, not
1.163. Source of every change below is the sibling program
`Highfleet.exe.unpacked.exe v1.163` (state as of 2026-11-11, after the
October sweeps and the 2026-11-05 friendly-fire pass). No code bytes were
changed; only function names, plate comments, signatures, and data types.

Full method, evidence and caveats: [port-163-to-151-report.md](port-163-to-151-report.md).
Raw data and scripts: [data/](data/) (`matched.tsv` is the complete
address pair table).

## Function names, plate comments, signatures

- **1,404 rename + plate ports** of 1.163-named functions onto their 1.151
  twins (`FUN_*`/`rep_*`/`CFUN_*` targets only; nothing already named was
  touched). Match tiers: 1,280 unique mnemonic-hash + instruction-count,
  64 distinctive-string-set, 60 anchored-callee propagation (two rounds).
  Result: 1.151 went from 961 to 2,366 named functions (20% -> 48%);
  `FUN_*` 1172 -> 566, `rep_*` 2776 -> 1977.
- **1,333 plate comments** copied verbatim (4 targets already had a plate;
  they kept it).
- **488 signatures** rebuilt: 94 onto functions whose committed parameters
  already matched storage-for-storage, plus 394 reconstructed with
  `DYNAMIC_STORAGE_FORMAL_PARAMS` on functions whose parameters were never
  committed (only for hash-tier pairs - identical instruction streams make
  the calling-convention placement safe). 31 non-hash pairs with custom
  1.163 signatures were left unnamed-sig on purpose (version-affected bodies
  may pass arguments differently).

## Data types

- **270 structures + 10 unions + 1 enum** (`b2ShapeType`) created verbatim
  from the 1.163 DTM (categories preserved, e.g. `_Box2D/`, `_Shader/`,
  `_Containers/`, `auto_structs/`), with field comments intact. Each carries
  a description: "Ported verbatim from Highfleet v1.163 program
  (2026-11-11). Offsets are 1.163 values; classes changed between 1.151 and
  1.163 may differ - see docs/porting-1151-1163.md".
- Dependency cycles (b2Body/b2Fixture/b2World, the HashMap family, the
  DLL/SentinelList family) were broken with empty shells first, fields
  second, so all 280 import candidates resolved.
- 5 structs initially came out short because a referenced class exists in
  1.151 only as a placeholder (`CReObject` in 1.151 is 1 byte vs 40 in
  1.163); `CSGlitch` got explicit tail padding, the other four rebuilt to
  their exact declared lengths.

## What was deliberately NOT ported

- 19 structures that exist under the same name in both programs but with
  different sizes (`Body` 2624 vs 2576, `Creature` 6736 vs 6443, `Profile`
  1512 vs 1380, `Escadra` 1560 vs 1536, `Ammo` 392 vs 360, `Panel`, `GUI`,
  `ObjectList`, vtables...). The 1.151 definitions are the ones modelled
  against 1.151 memory and were left untouched; the full size table with the
  delta analysis is in the report.
- Plate/sig of non-hash matched pairs where the twin is clearly
  version-affected (31 sigs, see above), and one propagation candidate
  rejected by spatial-delta consistency
  (`aircraftStateHandler` 163 `0x14000fbc0` -> candidate `0x1400d51d0`,
  +0xC5210 against a local expectation within ~0x1000; almost certainly a
  same-body false positive, the real 1.151 twin is not yet found).
- 6 hash-tier candidates dropped for duplicate name/target collisions, and
  164 named-1.163 functions whose 1.151 counterpart keeps logdot's own
  earlier name were not overwritten.

## Caveats

- Everything here is static cross-version matching. The mnemonic-hash tier
  is strong (identical instruction sequences), the string and propagation
  tiers are per-candidate evidential (see `matched.tsv` column `tier`/`ev`).
  No in-game validation was performed - no mod touches these annotations.
- Ported structure layouts are 1.163 values. For the version-changed classes
  (Body/Profile/Escadra/Ammo record/stats record weapon block) the zone
  tables in [porting-1151-1163.md](../../porting-1151-1163.md) still apply;
  treat ported `_Shader`/`b2*`/`_Containers`/auto_struct types as identical
  across versions only until a read of the 1.151 code confirms the field.
- The 1.151 scan for `aircraftStateHandler` (and other unmatched
  version-affected functions: `FireGun` twins already exist by name in 1.151)
  remains open; the propagation tier stalls below 3 anchored callees.

## Rounds 2 and 3 (same day, after the check-in)

Three further passes were applied and checked in after the first round:

- **Round 2 (147 pairs)**: 95 *group* tier — whole ICF-merged groups where the
  1.163 side is uniformly named and the 1.151 group is uniformly unnamed,
  ported member-for-member by sorted address (this also absorbed the 6
  "duplicate name" pairs the round-1 uniqueness rule had rejected, e.g. both
  `VectorStride48_InsertMove` instances); 23 *strings2* (>=60% string-set
  overlap + anchored-callee support + 25% score margin); 29 *prop2*
  (relaxed >=2 anchored callees). Includes `Body_AreaDamageFromBlast`
  `0x14002cdc0 -> 0x14002dca0` - exactly the porting guide's anchor pair.
- **Round 3 (96 pairs)**: repaired a format bug that had silently dropped the
  3,063 `port_work/M.json` anchor pairs from the anchor map (short vs
  16-digit address keys); with the full anchor set, 47+1 more
  callee-propagation matches and a new **caller-vote tier** (48): >=3 of the
  target's 1.163 callers map to 1.151 functions that call the same candidate,
  best unique with margin, spatial-delta consistent. Examples:
  `Effect_Add*Param` family, `Body_SetHealth`, `RbTree_DestroySubtree`.
- **Inline comments (1,378)**: all PLATE(68)/POST(1310) comments of 1.163
  sitting on instructions of identical-body pairs (tiers hash/group), ported
  by instruction index with the mnemonic sequence guaranteed equal by the
  tier. 80 target instructions already had a comment and kept it. PRE/EOL
  comments on non-identical pairs were deliberately not ported (index mapping
  is unsafe when the bodies differ).

Cumulative state after round 3 (live audit): 2,609 of 4,923 functions named
(53%), 1,723 functions carry plate comments, plus 1,378 inline comments.
Remaining rejects of interest: `aircraftStateHandler` (163 `0x14000fbc0`) -
the only content-supported candidate (`0x1400d51d0`) is spatially impossible
and no other candidate shares even one anchored callee; the true 1.151 twin
needs a decompile-level comparison. `Profile_GetActive`, `Vec2_WorldToScreen`,
`Trail_DrawLayer` and four more caller-vote candidates were rejected by
spatial delta with thin content evidence.

## Round 4: mod-function port (2026-11-11, second save)

Same-session round driven by the mods: extracted every hard-coded 1.163
address from `hf_ally/src` and `hf_ai/src` (42 code sites, 40 unique containing
functions plus 2 missed by the first pass, `PlayRadioSounds_` and the level
loader), and resolved where each lands in 1.151.

Method for the 34 functions without an existing pair: mnemonic-sequence
matching. Ghidra listing scripts (`DumpMn163/DumpMn151/DumpMn163c/DumpMn151b/c`)
dumped per-instruction mnemonic strings for all targets and all 1.151
candidates (spatial-delta window +/-0x40000..0x60000, instruction-count band,
1,351 unique candidates). Ranking by shared 8-gram fingerprints, confirmation
by full LCS over the mnemonic sequence plus mapped-callee set identity;
`!ClickFunc` / `creatureLogic` and the other giants were script-only, never
run through the MCP decompiler. Description: `mod-port-2026-11-11.md`, data:
`data/modaddr_163_151.tsv`.

Renames applied in 1.151 (3, current names replaced; old names recorded in
the plates):

- `0x1402a52b0`: handleRamming?? -> **battleManagerTick** (163 `0x1402cc260`,
  LCS 274/292 + identical mapped callee set; hf_ally BATTLE_RVA target).
- `0x1402ad0b0`: rammingCheckCollision?? -> **deployFromReserve** (163
  `0x1402d6e90`, LCS 118/130 + callee anchor; hf_ally DEPLOY target; the
  hf_ally source documents this exact 163 function formerly carrying the
  same old name).
- `0x140074bb0`: rep_...CRT-HEAP...::free (mislabel) ->
  **AiShip_ChooseTarget** (163 `0x140078b40`, LCS 466/540 + decompile
  cross-check: role-2 bombing branch, sensor-list walk, 20000/distance
  scoring).

Verified-equivalent pairs recorded without renaming (1.151 side already
carries a meaningful name): buildPrecombatScreen=mainPrecombatScreen,
AiShip_BuildThreatList=PopulateEngagementQueue, CreatureUpdate=
UpdatePlayerShipTactical, AiShipTick=TacticalAI_MasterUpdate,
Profile_SetControlledShip=Body_SetSlotOccupant, FireFlareLauncher=LaunchFlar?,
GetStats=GetShipPart, Node_GetRootPart=traverseLinkedListCreature?,
LaunchZenithAtOwnerTarget=BindHardpointTarget (moderate, flagged),
resetGuiStrings/Font_SetupByName/Get_Profile? (ICF-fold collisions).

No 1.151 twin: `buildSquadPrecombatScreen` - the standalone squad precombat
screen (secondaryPrecombatButtons dispatcher seams) is a 1.163 feature;
TarkhanGUIDispatchOperator has one precombat caller in 1.151 vs two in 1.163.

Also resolved today (earlier rounds had already renamed them; a stale local
audit had said otherwise): Creature_RegisterInWorldLists,
Creature_SpawnFromTemplate, CollectDeadNodes, Creature_SetPartsOwnerRef - all live and
correct.

Data globals used by the mods (LEVEL_NAME, RESERVE, CREATURES_BEGIN, CLOCK,
CONTROLLED_LINKS, BODIES, arena bounds, FRAME_DELTA, GUI_LIST, RETREAT_POINT,
RNG_SCENARIO, AIRCRAFT_SELECTOR, ~45 total) were NOT ported; that needs a
separate global-label pass.

Program saved once after the renames (second check-in of the day).

## Round 5: no-twin re-audit, field/global mapping (2026-11-11, third save)

Two parts, both driven by review feedback.

### Part A: the same inlining/correction check on every "no twin" verdict

The buildSquadPrecombatScreen "no twin" claim was wrong and the same check
was applied to the full reject pile (rounds 1-3 reject lists recovered by
re-running round3.py in a sandbox - reproducible, FINAL 96):

- *buildSquadPrecombatScreen 0x1402d73a0*: INLINED into
  mainPrecombatScreen 0x1402ad2e0. 127/134 instructions align; epilogue POPs
  match mainPrecombatScreen's tail; the B2 dispatcher seam (0x1402d75f2)
  maps to the TGDO call at 0x1402ae333. The earlier "1.163-only" statement
  in the round-4 report was an instruction-count-band artifact and is
  retracted (erratum added to mod-port-2026-11-11.md).
- Renames applied (identical/near-identical bodies; the spatial-delta guard
  had false-rejected them; content evidence overrides):
  Hull_CreateAntennaChain 0x140047e60 (LCS 109/113; was rep_140047e60_New),
  Vector8_PushBackRealloc 0x1400b4dd0 (9/9; ICF fold of 4, caller-voted),
  LinkedList_ClearFree 0x1400eaef0 (31/31; was a CRT-free mislabel),
  RbTree_ClearFreeResetHeader 0x1401ac200 (29/29; same),
  Vec2_WorldToScreen 0x14019e6e0 (28/28; was SetAimRectZoom???).
- aircraftStateHandler (round-1 leftover): 1.151 twin IS
  AircraftLogicStateMachine 0x14000f890 - 129/129 instructions identical.
  The round-1 content candidate (0x1400d51d0) was wrong. Equivalence recorded
  in the plate, no rename (both sides already meaningfully named).
- Still open after content checks: Aircraft_CollectActiveCraft,
  Profile_GetActive, Trail_DrawLayer, Gfx_BuildFullscreenProjection (candidates
  not confirmed by body similarity) and String_Tidy (byte-identical ICF group
  of seven 151 copies; mapped callers call none of them, no unique member).
- New verified pairs recorded in data/matched4.tsv.

### Part B: field/global mapping for the mod port (fields_163_151.tsv)

Full-instruction dumps (address + mnemonic + operand text) for 18 matched
anchor pairs; LCS alignment with traceback; displacement votes for creature
field offsets and direct [addr] reference votes for data globals. Key
results now applied in the 1.151 program:

- 32 data-global labels with provenance plates (CLOCK, HGE_PTR, all ten
  creature-list sentinels CREATURES/NEG/AI/POS/ZERO, GUI_ROOT,
  SCRIPTED_SCENARIO, BATTLE_RESULT, WAVE_TIMER, RESERVE, ENEMIES_BEGIN/END,
  ROSTER_BEGIN/END, Role2_VoteMap, FRAME_DELTA, arena bounds, INIT_DIM_A/B,
  CONTROLLED_LINKS, DeadNodeList, F32_ONE, INIT_SCALE). FRAME_DELTA coexists
  with the pre-existing primary label time_related_global? at 0x140391184.
- Creature field migration table (1.163 offset -> 1.151 offset), the
  mod-critical contract: side 0xad4->0xa9c, target link 0xaf8->0xac0, target
  node 0xb00->0xac8, retarget timer 0xb28->0xaf0 (family-delta inference),
  steering waypoint 0xbf0/0xbf4->0xb88/0xb8c (exact STEER site match),
  fire-flag bytes 0xbbc-0xbc0->0xb54-0xb58, aggression 0xbc4->0xb5c,
  fuel at start 0xbd0->0xb68, driver state 0xbdc->0xb74, launch cooldown
  0xd60->0xcf0, role/mode 0xd70->0xcfc, order 0xc98->0xc30, part fields
  0x848/0x858/0x860->0x834/0x844/0x84c, fuel 0x1638/0x1640->0x1588/0x1590,
  position 0x1840/0x1844->0x1784/0x1788. Unresolved: the ChooseTarget weapons
  pair 0x15e8/0x15ec (moved near 0xc0c/0xc10 with a width change - needs
  manual review at port time) and the 0x48 active flag.
- Six EOL landmark comments at the 1.151 hook-site counterparts (waypoint
  writes, state-forced writes, target reads), e.g. the hf_ai STEER site:
  163 0x140064a8d (creature+0xbf0) -> 151 0x140061cbd (creature+0xb88).

Program saved once after all of part A + part B (third check-in of the day).
