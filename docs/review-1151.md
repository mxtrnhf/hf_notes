# Review of the 1.151 Ghidra annotations (working file)

**Working file on branch `review-1151-annotations`.** Everything about 1.151 lives here until the notes are reviewed; afterwards each section is moved into the normal docs
(see the `MOVE:` comments, they are notes to myself and are deleted when the move is done). Read-only: nothing was changed in either Ghidra program.
Tags as in `../README.md`: **[code]** read from a decompilation, **[guess]** inferred, **[tool]** produced by Ghidra's fuzzy matcher (a similarity score, not proof).

<!-- MOVE: after the merge this file is split. Rule of thumb: addresses and function roles go to systems.md / structures.md / engine-hge.md as 1.163 facts with the
     1.151 name as a "(1.151 name: ...)" tag; the method and the inventory go to setup.md (Ghidra section); the unmatched names go to open-questions.md. Delete this file after. -->

## What was compared

| | 1.151 (`/Highfleet.exe.unpacked.exe v1.151`) | 1.163 (`/Highfleet.exe.unpacked.exe v1.163`) |
|---|---|---|
| Functions | 5,200 | 5,115 |
| Symbols | 91,554 | 39,089 |
| Data types | 1,449 | 535 |
| Hand-named functions (not `FUN_`, `rep_`, `CFUN_`), from the function lists (each list was ~95% complete) | ~875 | ~560 |
| Of those names present in both programs | 535 | 535 |
| Names only in 1.151 / only in 1.163 | 354 / 25 | |
| Image base | `0x140000000` | `0x140000000` |

The `rep_<addr>_<name>` names are machine-propagated from one program to the other (the Version Tracking session `1.15TO1.16Test` or an earlier matcher run), so
they are not independent evidence. The ~875 hand names and the data types are the real annotation work.

<!-- MOVE: this table -> setup.md, Analysis section (one line: "1.151 program has more annotation; see roadmap/Ghidra sync"). -->

## Method
1. Listed every function in both programs; compared the hand names by text.
2. `bulk_fuzzy_match` from 1.151 to 1.163 (3,143 of 4,530 source functions returned a match; 558 of them hand-named). Of those 558: 188 score >= 0.99, 129 score 0.90-0.99, 241 score < 0.90.
3. For names that matter to our notes, opened the 1.163 target and checked it by decompiling.
4. **Scores below about 0.9 are unreliable.** Example: 1.151 `Get_Profile` at `0x14026ff50` matched 1.163 `0x1402924b0` (score 0.8166), but `0x1402924b0` is a 4-slot array
   accessor; the real 1.163 `Get_Profile_` is `0x140292a90` (the singleton our notes already use). Treat a low score as a candidate only.

<!-- MOVE: this "Method" + the unreliable-score warning -> setup.md, Pitfalls. -->

## 1.151 names that confirm what our 1.163 notes already say

| 1.151 name @ address | 1.163 function | Score | What it confirms in our notes |
|---|---|---|---|
| `CheckMapMotionEncounter` @ `0x1400e6e00` | `0x1400ec440` | 0.857 | `FUN_1400ec440` = do two map objects come within 1.0 during the next step (`systems.md`, engagements) [tool + code, we decompiled it] |
| `handleMissileIntercepts` @ `0x1400eba90` | `0x1400f11b0` | 0.868 | the map-level shooting parent `FUN_1400f11b0` (`systems.md`) [tool] |
| `runMissileandAircraftIntercept?` @ `0x14010b4d0` | `0x140111110` | 0.848 | the function that prints `MISSILE_INTECEPTED` and downs up to 3 crafts per pass (`systems.md`) [tool] |
| `UpdateStrategicFleet` @ `0x14010c3a0` | `0x140111ff0` | 0.762 | the fleet update `FUN_140111ff0`: refuel, cooldown countdown, consumer call, engagement trigger [tool, low score] |
| `selectMissileType` @ `0x140251950` | `0x140273640` | 0.890 | the map missile panel `FUN_140273640` with the four `MAPMODE_MISSILE_SW` switches [tool]; also the name used inside `FUN_140214c40` |
| `initProfileMissiles?` @ `0x1400e7890` | `0x1400eced0` | 0.722 | the map launch consumer `FUN_1400eced0` (the 1.163 program already carries this name) [tool, low score; verified by decompiling in 1.163] |
| `SetupStrategicMissileBattle` @ `0x1402aa830` | `0x1402d45c0` | 0.752 | state 1 of `SCR_MISSILE`: spawns defenders and the missiles from B[0] [tool, low score] |
| `CopyObject` @ `0x1401af8c0` | `0x1401bfd00` | 0.907 | the copy routine used for the class-size table in `structures.md` [tool] |
| `DynNewSerializable` @ `0x1401e8000` | `0x1402024e0` | 0.916 | the default-construction factory (Ghidra still calls it `Panel::Constructor` in 1.163) [tool] |
| `GetStats` family: `GetLaunchedRange` `0x1400462f0`, `GetLaunchedSpeed` `0x140046350`, `GetLaunchedSpeed2` `0x140046320`, `GetLaunchedHealth` `0x1400462c0`, `GetMissileAgility` `0x1400464f0`, `GetMissileAp` `0x140046520`, `GetMissileExplosive` `0x140046550`, `GetMissileFuzeType` `0x140046580`, `GetMissileRadarCone` `0x1400465b0` | not looked up | - | names the stats-record fields in `structures.md` (+0x158 launched_speed, +0x15c speed2, +0x160 range, +0x168 explosive, ...) [guess until opened] |
| `Creature::add_fuel` @ `0x14005ea20` | not looked up | - | a ship-level add-fuel; 1.163 notes use `FUN_1400ea980` for the fleet-level one [guess] |
| `renderMissilesOnMap` @ `0x1400e4360`, `traverseEscadraMissiles?` @ `0x1400e3860` | `0x1400e99d0`, `0x1400e8ee0` | 0.923, 0.714 | where the profile's map-object list is walked [tool] |
| `handleRefuelingNoises?` @ `0x1400f9190` | `0x1400fe8b0` | 0.894 | the `+0x468` refuel-animation function `FUN_1400fe8b0` in `systems.md`, sounds `refueling_start/loop/stop` [tool] |
| `setupHGEFunctionPointers` @ `0x1402bf650`, `CreateHGE` @ `0x1401730b0` | `0x1402eab80`, `0x14017ecc0` | 0.999, 0.990 | the HGE interface table setup in `engine-hge.md` [tool, high] |

<!-- MOVE: each row -> add "(1.151 name: X)" next to the matching FUN_ in systems.md / structures.md / engine-hge.md; the GetStats family -> structures.md stats record. -->

## New facts from reading 1.151 code

### `CreateMapAircraftGroup` (1.151 `0x140109de0`) settles what `0x800000001047` is [code]
* It allocates **`New(0x340)`** and runs the `Mark` constructor on it, then sets the object's vtable, an 8-byte-aligned block at `+0x310..+0x320` zeroed, and a name string:
  the same shape as the 1.163 constructor `FUN_1400e4530` that the default factory uses for `0x800000001047`.
* It builds the object from a list of aircraft (each `GetShipPart(...)` stats lookup: it takes the **max `launched_speed`** and **max `launched_range`** of the group's members into
  the new object), computes a start position and heading from the launching fleet, sets fixed constants (timer 30.0, 100.0 / 1000.0 / 20.0 at `+0x174/+0x178/+0x17c`), links the
  fleet (`SetLink` at `+0x280`), appends the group to the profile's map-object vector `mapCrafts` (`+0x228/+0x230`), and calls `ComputeMapAircraftWeaponStrength`.
* **Conclusion:** `0x800000001047`, size 0x340, **is the MapCraft (map aircraft group)**; the Ghidra comment "Ground defense creatures?" in the 1.163 factory is wrong, and so is
  the name `createGroundDefenseCreatures??` in 1.151 if it was meant for this code (1.151 `0x140004950`; unchecked).
* The profile vector `mapCrafts` (+0x228/+0x230) holds **both** Missile and MapCraft objects: the 1.163 map-launch consumer pushes its new Missile into the same vector. So
  `structures.md` "missiles +0x228/+0x230" is the right vector, but its name should be "map objects".
* The function's fourth argument is an optional target object. If given, the MapCraft copies that object's link into `+0x268`, and its field `+0x338` takes either a fleet's `+0x4c8`
  or a MapCraft's `+0x300 + +0x304`, chosen by the mask tests `& 0x147` / `& 0x800000001047` on the linked object. So **a MapCraft's target can be a fleet or another MapCraft**,
  consistent with the target-type finding for the map-launch queue (`systems.md`).

<!-- MOVE: this subsection -> structures.md (class code table: replace the "(unnamed)" part of the 0x800000001047 row with the confirmation; rename the vector to "map objects");
     the construction details -> systems.md (Engagements / air raid) only if kept short. Remove the Ghidra "Ground defense creatures?" comment from the 1.163 listing when annotations are synced. -->

### Names with no fuzzy match (candidates for manual carry-over)
The matcher (threshold 0.7) found **no** 1.163 counterpart for these 1.151 functions, so the code was probably rewritten: `CreateMapAircraftGroup` (`0x140109de0`),
`UpdateMapAircraftGroup` (`0x140111980`), `ComputeMapAircraftWeaponStrength` (`0x1400e69a0`), `ConfigureStrategicMissileForTacticalBattle` (`0x140241680`). All four are
about the air-group / strategic-missile code that the roadmap's AI items depend on. In 1.163 they are probably `FUN_` somewhere near `0x1400f....` to `0x14011....` (map-object block)
[guess]; find them by searching 1.163 for the strings and masks they use (`& 0x800000001047`, `mapCrafts` `+0x228`) rather than by similarity.

<!-- MOVE: -> open-questions.md ("find the 1.163 counterparts of the four air-group functions") and roadmap.md as a prerequisite for the strategic-AI items. -->

## Annotation themes in 1.151 that the 1.163 program lacks (354 names)
Reading the list by theme (names only; contents not yet opened except where marked above):
* **Level scripts:** one label per scenario inside the giant scenario function: `SomethingWithLevelSerias_SCR_MAP` (`0x140290a60`), `..._SCR_MISSILE` (`0x14029ebaf`), `..._SCR_BOMBERS`
  (`0x14029f2ed`), `..._SCR_CRAFTS_VS_MISSILE` (`0x14029f112`), `..._SCR_CRAFTS_VS_CRAFTS` (`0x14029f89e`), `..._SCR_COMBAT` (`0x14029d3df`), `..._SCR_CITY_GENERATED`, `..._SCR_EDITOR`,
  `..._SCR_EDITOR_EXTENDED`, `..._SCR_HALL`, `..._SCR_INTERMEDIA_01..03`, `..._SCR_RUINS`, `..._SCR_REINFORCE`, `..._SCR_PRESELECT`, `..._SCR_CREDITS`, `..._SCR_BUILDER`, `..._SCR_LEVEL_EDIT`,
  `..._SCR_EMPTYWORLD`, `..._SCR_COMBAT_TEST`, plus `case_01..10` blocks. The parent function `SomethingWithLevelSerias` is at `0x140289850`; our `FUN_1402ac970` is very likely its 1.163 version
  (address trend: other functions moved by +0x21000 to +0x23000 in this range) [guess]. This gives the **scenario map for `CraftsVsMissile` / `CraftsVsCrafts` / `Bombers`**, which `open-questions.md` lists as unread.
* **Creature logic split:** `creatureLogic` plus named pieces (`_shipExitLever`, `_spawn_despawn_w_SFX`, `_recoilRelated`, `_keepCreatureInViewport`, `_lessThan9BulletsThing`, `_selectTargetAndMoveAround`, `_landing_related?`).
* **Editor and shipworks:** `DefineEditorParts`, `loadShipworks?`, `DrawShipworksScreen`, `saveEditorDesigns?`, `memcmp_editor`, `EDITORCPP`, `ammoSelectButtonPress?` (relevant to the elevation mod and to the tooling roadmap).
* **Campaign, events and cities:** `handleEndgameContent`, `spawnEndgameShips?`, `spawnEndgameStrikeGroups?`, `Generate_Cities?`, `spawnGroundDefense`, `spawnTradeConvoy?`, `PlayerDiscoveredInCity`, `tarkhanInfoEventsHandler?`,
  `restOfEventsPrologueAntIsaiah` (the Khiva / end-game bug in the roadmap will start here; `handleEndgameContent` @ `0x1400a260b` in 1.151).
* **Combat model:** `calcDMGPercentage`, `Projectile_ExplodeAndCluster` (`0x14002c170`; cluster TTL item in the roadmap), `FireGun/FireGuns/FireShell`, `rammingCheckCollision??`, `handleRamming??`, `checkJammed?`, `handleIRST?`, `handleBurnDMG?`.
* **AI aircraft:** `TryLaunchAiAircraftGroup` (`0x1400ea210`), `aircraftStateHandler`, `changeAircraftState?`, `configure_plane_aa_missiles/bombs/gun/rockets`, `checkAircraftOutOfBounds`, `launchAircraft?`, `LaunchFlare?`
  (`0x14002f6f0`; flares and the flare crash in the roadmap).
* **HGE interface:** `Resource_*`, `System_*`, `Input_*`, `Channel_*`, `Effect_*`, `Stream_*`, `Timer_*`, `Random_*`, `Ini_*` (the whole HGE vtable, 1.163 only has `setupHGEFunctionPointers` named): `engine-hge.md` interface table.

<!-- MOVE: Level scripts -> systems.md (Engagements, scenario state machines) and open-questions.md; AI aircraft + combat model + endgame -> roadmap.md as "where to start" pointers
     under the matching bug/AI item; HGE interface -> engine-hge.md; the rest stays here until opened. -->

## Not done yet
* The 1,449 data types in 1.151 (535 in 1.163) have not been opened: the structs (`Body`, `Escadra`, `Missile`, `Profile`, `ShipPart`, ...) are the biggest carry-over gain.
* None of the 354 names was opened except `CreateMapAircraftGroup`.
* Comments, plate comments and bookmarks of 1.151 not reviewed.
* Nothing was written to either Ghidra program. Carrying names/types across needs a checkout and saving the shared project; wait for the review by logdot.

## How automatable is the type transfer? (checked, nothing changed)

**Short answer: names and function signatures yes (mostly), struct layouts no (needs a per-region offset remap and verification).**

Facts [code, from `search_data_types` / `get_struct_layout` on both programs]:
* 1.163 already has the project categories that 1.151 has (`_Body`, `_Escadra`, `_Missile`, `_Profile`, `_Creature`, `_AircraftLogic`, `_Link`, `_Node`, `_GUI`, ...). The types were
  ported once (Version Tracking), including `.conflict` duplicates (`Body.conflict`, `BodyVFTABLE.conflict`, `DLL<Body>.conflict`) that should be cleaned up. 1.151 additionally has
  `hge.h` / `hge.h/functions`, `hge.pdb`, `unzip.h`, `zlib.h`, `ioapi.h`, `bass.h`, `mfobjects.h`, `rpcndr.h`, `tapi.h`, `wtypes.h`, `New Category` and `HighFleet` (the HGE
  interface and library headers; 1.163 lacks them).
* **The ported 1.163 `Body` struct is the wrong size.** Ghidra says 2,568 bytes (0xa08); the game allocates **0xa40** (`New(0xa40)`, `structures.md`). 1.151's struct is 2,576 (0xa10).
  So 1.163 has about 0x38 more bytes than the struct models.
* **Offsets drift by region, not by a constant.** `floorType`/`floor` are at 0x980/0x988 in the 1.151 struct, at 0x978/0x980 in the 1.163 struct, but the game-verified 1.163
  offsets are `+0x9b0` (`m_floor_type`) and `+0x9b8` (`m_floor`) (`structures.md`). `weaponAmmoAmount` is 0x84c in 1.151 and +0x858 in 1.163. So the struct fields past about
  +0x2f0 are partly stale in the 1.163 program and **copying 1.151's struct over would put names on the wrong offsets**.
* 1.151 names more fields than 1.163 does (for example `aircraft_loudout?`, `m_mdl_fuel`, `m_mdl_pump`, `fFireCharge`, `fFireRateTimer`, `fFireDelay`, `bFireStatus`, `aircraft_logic`), which are exactly the
  kind of names our notes would like (weapon timers, fire status).

What each piece needs:

| Piece | Automatable? | How / blocker |
|---|---|---|
| Function names and signatures (the 354 only-in-1.151 hand names, plus signatures) | **Mostly yes** | Ghidra's Version Tracking (a session `1.15TO1.16Test` already exists in the local project): exact/similar function matches, then "apply markup". Matches below ~0.9 need a human check (see Method). |
| Global labels and data names | **Mostly yes** | Same VT markup, via data matches. |
| Plain/enum types, typedefs, `hge.h`-style function types | **Yes** | `clone_data_type` / copy between programs; no layout problem. |
| **Struct layouts (`Body`, `Escadra`, `Missile`, `Profile`, `Creature`, ...)** | **No (semi-manual)** | Offsets moved. Needs a remap table per struct (1.151 offset -> 1.163 offset), built from matched functions or from our game-verified offsets in `structures.md`, then `modify_struct_field` / `resize_struct`. The bridge has the tools (`create_struct`, `modify_struct_field`, `resize_struct`, `set_*_type`), but nothing infers the remap. |
| Comments (plate/EOL) | **Partly** | VT markup copies them for matched functions only. |

Tooling notes:
* The MCP has `import_data_types`, `clone_data_type`, `run_script_inline` / `run_ghidra_script` (arbitrary Ghidra scripts, so a custom transfer script is possible), and an archive-ingest
  function that is **disabled** unless `GHIDRA_MCP_ARCHIVE_URL` is set (it would send data to an outside service; leave it disabled).
* Every write needs the shared project checked out and saved; do it only after logdot's review, and in small batches that can be undone by versions.

Suggested order when the time comes (cheapest first, each a separate Ghidra version so it can be reverted):
1. Delete the `.conflict` types in 1.163 (check nothing references them first).
2. VT markup of function names and signatures for matches >= 0.99, then 0.9-0.99 spot-checked.
3. Import the `hge.h` types and HGE function pointer names (feeds `engine-hge.md`).
4. Struct by struct (start with `Body`, `Escadra`, `Missile`): build the remap from `structures.md` offsets, resize to the real object size, then bring over names.

<!-- MOVE: this whole section -> roadmap.md under "Ghidra side" (it is the plan), with the facts about struct size drift also added to setup.md Pitfalls ("the 1.163 Body struct in Ghidra
     is 0xa08, the object is 0xa40; do not trust field offsets past ~0x2f0 in the Ghidra struct, use structures.md"). -->

## Body remap, 1.151 -> 1.163 (first pass, read-only)

**Method.** Both `copyOverBody` functions were decompiled (1.151 `0x140017f60`, 1.163 `0x140017e70`). The 1.163 copy routine names offsets directly (`param_2 + 0x...`); the 1.151 one uses
the struct's field names, whose offsets come from the 1.151 `Body` struct. Pairing is by field meaning (same name/role, same size, same position in the statement groups), checked
against the offsets our notes verified in 1.163 (`structures.md`). The ctors (`createNewBody`, 1.151 `0x1400157c0`, 1.163 `0x140015690`) were used for the zero/-1.0 init patterns only.
Tags: **[V]** 1.163 offset is also verified in `structures.md` (game or code); **[C]** 1.163 offset read from the copy routine and paired by role; **[?]** uncertain.

### The shift is piecewise constant, not one number

| 1.151 offset range | 1.163 shift | Evidence |
|---|---|---|
| `0x000` .. about `0x1f8` | **0** | vtable, class name, `m_code`, `state`, `m_id`, owner, name, position/velocity/angle at `0x128..0x13c`, stats index `0x188`, `m_oid` `0x190`, density..dragAngle `0x1d0..0x1e0`, layer `0x1f0` all equal [V] |
| about `0x20c` (center) | **+4** | `centerX/Y` 0x20c -> 0x210 [C] |
| about `0x2a8` .. `0x7f0` | **+0x10** | collisions/ttl/health block, slots, spasm, `logic*`, sectors, `count` block, `mdl_fuel`, `mdl_fss` (rows below) |
| about `0x828` .. `0x860` (weapon/ammo area) | **+0xc** (some fields +0x10) [?] | a 4-byte field is missing in 1.163 between `mdl_fss` and `mdl_covered`; see "unresolved" |
| about `0x980` .. `0xa30` (floor, edRotate, aircraft logic) | **+0x30** | `floorType`, `floor`, `edRotate`, aircraft logic pointer |
| tail flags (`isFocusable` ...) | **+0x38** (struct end 0xa10 -> 0xa40 is +0x30; see note) | |

Total size: 1.151 object ends at `0xa10`; 1.163 at `0xa40` (+0x30), consistent with the last zone being +0x30 (the extra +0x38 seen for the aircraft logic pointer is explained by the
two pointers `aircraft_logic`/`aircraftLogic` in 1.151 collapsing into one at `0xa20` in 1.163).

### Anchor pairs (1.151 name @ offset -> 1.163 offset)

| Field (1.151 name) | 1.151 | 1.163 | Shift | Basis |
|---|---|---|---|---|
| `className`, `m_code`, `state`, `m_id` | 0x08, 0x28, 0x48, 0x78 | same | 0 | [V] |
| `positionX/Y`, `velocityX/Y`, `angle`, `angleVelocity` | 0x128..0x13c | 0x128..0x13c | 0 | [V] copy routine |
| `part_index` (stats index) | 0x188 | 0x188 | 0 | [V] |
| `moid` | 0x190 | 0x190 | 0 | [V] |
| `density`, `friction`, `mass`, `dragLinear`, `dragAngle` | 0x1d0..0x1e0 | 0x1d0..0x1e0 | 0 | [V] copy routine |
| `layer` | 0x1f0 | 0x1f0 | 0 | [V] |
| `centerX/Y` | 0x20c | 0x210 | +4 | [C] |
| `collisions`, `timeToLive`, `ttlDesolveTime` | 0x2a8, 0x2b0, 0x2b4 | 0x2b8, 0x2c0, 0x2c4 | +0x10 | [C] |
| `health`, `maxHealth` | 0x2b8, 0x2bc | 0x2c8, 0x2cc | +0x10 | [V] (`m_health`/max) |
| `healthLock`, `contamination` | 0x2c0, 0x2c4 | 0x2d0, 0x2d4 | +0x10 | [C] |
| `explosive`, `explosiveType`, `explosiveTemperature` | 0x2cc, 0x2d4, 0x2d8 | 0x2dc, 0x2e4, 0x2e8 | +0x10 | [C] |
| `burnHp` | 0x324 | 0x334 | +0x10 | [C] |
| `slots` (vector begin) / `slotsEnd?` | 0x340 / 0x348 | 0x350 / 0x358 | +0x10 | [V] (slot vector) |
| `slotType` | 0x358 | 0x368 | +0x10 | [C] |
| `spasmCode` | 0x360 | 0x370 | +0x10 | [C] |
| `collisionSensor` | 0x37c | 0x38c | +0x10 | [C] |
| `logic`, `isLogicActive` | 0x3b4, 0x3b8 | 0x3c4, 0x3c8 | +0x10 | [V] (`m_logic_active` 0x3c8) |
| `logicF1..F4`, `logicI1..I4` | 0x3c0.., 0x3d4.. | 0x3d0.., 0x3e4.. | +0x10 | [V] |
| `logic_editor` | 0x4e0 | 0x4f0 | +0x10 | [C] |
| `sectors` / `endSectors` | 0x4f8 / 0x500 | 0x508 / 0x510 | +0x10 | [V] (`m_sectors`) |
| `count` | 0x798 | 0x7a8 | +0x10 | [V] (`m_count`) |
| `isLoot`, `isBlueprint`, `isWheel`, `isLeg` | 0x79c, 0x79d, 0x79f, 0x7a0 | 0x7ac, 0x7ad, 0x7af, 0x7b0 | +0x10 | [V] (blueprint flag 0x7ad) |
| `m_mdl_fuel` | 0x7e8 | 0x7f8 | +0x10 | [C] |
| `mdl_fuel` (double, copied as two words) | 0x7f0 | 0x800 (second word 0x804) | +0x10 | [C]; our notes' "current fuel +0x804" is the upper word of this double [?] |
| `mdl_fss` | 0x7f8 | 0x808 | +0x10 | [C] |
| `mdl_covered` | 0x83c | **0x848** | **+0xc** | [V] (`m_mdl_covered` 0x848) |
| `weaponAmmoAmount` | 0x84c | **0x858** | **+0xc** | [V] (`m_weapon_ammo_amount` 0x858) |
| `isCrtScreen` | 0x878 | 0x878 | **0** | [C] (copy routine reads 0x878 in 1.163) [?] |
| `floorType`, `floor` | 0x980, 0x988 | 0x9b0, 0x9b8 | +0x30 | [V] (`m_floor_type`, `m_floor`) |
| `lightColorR..A`, `lightFade`, `ambient` | 0x9c8.. | 0x9fc..? | +0x30 | [?] by zone |
| `edRotate` | 0x9f8 | 0xa28 | +0x30 | [V] (`m_ed_rotate` 0xa28) |
| `aircraftLogic` pointer | 0x9f0 (and 0x9e8) | 0xa20 | +0x30 | [C] |
| `helpInex` / flags (`isFocusable`...) | 0x9fc.. | 0xa34..0xa3d | +0x38 / +0x30 | [C] copy routine bytes at 0xa38..0xa3d |

<!-- MOVE: the anchor table + shift zones -> a new "Version differences (1.151 vs 1.163)" subsection of structures.md (Body), once confirmed by logdot's review. The shift-zone table is
     also what the Ghidra struct rebuild (see "How automatable ...") will use. -->

### What this tells us
* **Mostly mechanical.** About 75% of the named Body fields fall in the +0 / +0x10 / +0x30 zones and can be mapped by adding a constant per zone. Only the weapon/ammo area
  (`0x828..0x880` in 1.151) and the `aircraftLogic`/lighting tail need individual attention.
* **The notes' offsets are self-consistent with this table** at every anchor I could cross-check (health, count/blueprint, logic, sectors, floor, edRotate, covered, weapon ammo): good
  evidence that `structures.md` is right for 1.163 and that the stale part is the Ghidra struct, not the notes.
* **A field the notes could correct.** `mdl_fuel` is a **double** copied as two words (0x800/0x804) in 1.163; `structures.md` lists "the part's current fuel is Body +0x804" (it appears in the
  stats row). If that is the high word of the double, reading it as a float/int there is wrong; confirm by reading a fuel part in game before changing the notes.

### Unresolved (need a second look)
1. The `+0x10` -> `+0xc` change between `mdl_fss` (0x7f8) and `mdl_covered` (0x83c): which field disappeared, and where. Compare 1.151 `m_mdl_pump` (0x828), `field_0x82c`, `mdl_turbine` (0x834),
   `field_0x838` with the 1.163 copies at 0x838, 0x83c, 0x848, 0x84c (the counts match, the offsets do not map by a single constant).
2. `isCrtScreen` at 0x878 in both versions (shift 0) conflicts with the +0xc zone around it: probably a field was inserted just before it that cancels the shift. Verify by reading the 1.163 constructor bytes around 0x860..0x880.
3. Lighting fields (`lightColor*`, `lightFade`, `ambient`) and the `aircraft_logic` / `aircraftLogic` pair: assigned by zone only.
4. All fields in the `(unnamed)` rows of the 1.151 struct (about 60% of its size). They have no names to carry, so the remap matters only for resizing, not for naming.

### Next step for the struct transfer
Resize the 1.163 `Body` struct to `0xa40`, then lay fields at the **1.163** offsets above (not at the 1.151 offsets), then bring the 1.151 names across. Do it as a Ghidra script or by hand with
`modify_struct_field`, but only after logdot's review and a checkout. No changes were made to either program.
