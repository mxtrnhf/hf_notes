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
