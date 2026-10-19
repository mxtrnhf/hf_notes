# Map aircraft groups, map-level intercepts and the fleet update (1.151 read, 1.163 mapped)

Status: **read from the 1.151 annotated decompilation and matched to 1.163; nothing run in game.** Tags: legend in `../../README.md`.
1.151 names are logdot's. Addresses are 1.163 (image base `0x140000000`) unless marked 1.151. Offset shifts between versions: [../version-differences.md](../version-differences.md).

## `CreateMapAircraftGroup` (1.151 `0x140109de0`, 1.163 `0x14010f8e0`) settles what `0x800000001047` is [code]
* It allocates **`New(0x340)`** and runs the `Mark` constructor on it, then sets the object's vtable, an 8-byte-aligned block at `+0x310..+0x320` zeroed, and a name string:
  the same shape as the 1.163 constructor `FUN_1400e4530` that the default factory uses for `0x800000001047`.
* It builds the object from a list of aircraft (each `GetShipPart(...)` stats lookup: it takes the **max `launched_speed`** and **max `launched_range`** of the group's members into
  the new object), computes a start position and heading from the launching fleet, sets fixed constants (timer 30.0, 100.0 / 1000.0 / 20.0 at `+0x174/+0x178/+0x17c`), links the
  fleet (`SetLink` at `+0x280`), appends the group to the profile's map-object vector `mapCrafts` (`+0x228/+0x230`), and calls `ComputeMapAircraftWeaponStrength`.
* **Conclusion:** `0x800000001047`, size 0x340, **is the MapCraft (map aircraft group)**; the Ghidra comment "Ground defense creatures?" in the 1.163 factory is wrong, and so is
  the name `createGroundDefenseCreatures??` in 1.151 if it was meant for this code (1.151 `0x140004950`; unchecked).
* **Profile layout shift (see [version-differences.md](../version-differences.md), Profile remap):** the first version of this bullet said the profile vector `mapCrafts` holds both Missiles and MapCrafts. That was wrong. The Profile
  layout moved by +0x48 between versions: in 1.151 Missiles are at `+0x1e0` and MapCrafts at `+0x228`; in 1.163 Missiles are at `+0x228` (the map-launch consumer pushes there) and MapCrafts at
  `+0x270` (`CreateMapAircraftGroup` pushes there). Ghidra's name `mapCrafts` at `+0x228` in the 1.163 program is a stale label.
* The function's fourth argument is an optional target object. If given, the MapCraft copies that object's link into `+0x268`, and its field `+0x338` takes either a fleet's `+0x4c8`
  or a MapCraft's `+0x300 + +0x304`, chosen by the mask tests `& 0x147` / `& 0x800000001047` on the linked object. So **a MapCraft's target can be a fleet or another MapCraft**,
  consistent with the target-type finding for the map-launch queue (`../mods/salvo.md`, "How the game launches strategic missiles").

### Group creation in 1.163 [code]
Matcher found no counterpart (score < 0.7), but the 1.163 call from `TryLaunchAiAircraftGroup` reaches `0x14010f8e0` (was named `rep_140109de0_...free`; now `CreateMapAircraftGroup` after the 2026-10-15 name port), so that is it.
* Same shape in both: `New(0x340)`, `Mark` constructor, group speed and range taken as the **maximum `launched_speed` (stats `+0x158`) and `launched_range` (stats `+0x160`)** over the members, start point from
  the launching fleet or the given target, constants set on the new object (1.163: turn rate `4.0` at `+0x2ac`, `60.0` at `+0x250`, `1.56` at `+0x254`, `30.0` at `+0x2b0`, `9000.0` at `+0x168`,
  `100.0`/`1000.0`/`20.0` at `+0x174/+0x178/+0x17c`, `type = 4` at `+0x29c`), then the group is added to the MapCraft vector and `loadAircraftWeaponsFromBotMenu` (1.151 `ComputeMapAircraftWeaponStrength`) fills the
  group's weapon totals at `+0x2fc/+0x304`.
* **New in 1.163:** if the group has no linked target, it scans the profile's `designs` list for an entry within distance 1.0 with `+0x2e8 > 1` and `+0x248 != 0` and links it. Unexplained; probably a
  base/landing target.
* The group's `+0x29c` type is `4`; map missiles use `1` to `3` (`3` = ground), so `+0x29c` is the map-object kind.

## `UpdateMapAircraftGroup` (the map aircraft group update)
### Where it is in 1.163 [code]
1.151 `UpdateMapAircraftGroup` is at `0x140111980`. Its 1.163 counterpart is at **`0x140117840`**: the prologue is identical in shape (`mov rax,rsp`, push rbp/rsi/rdi/r12-r15, `sub rsp,0x1b0`), the strings
`CraftsVsCrafts.seria` (`0x140360478`) and `CraftsVsMissile.seria` (`0x140360490`) are referenced from inside it, and the engagements section at the end of this page already calls it `FUN_140117840`. **The 1.163 program has no function
defined at `0x140117840`** (`get_function_by_address` finds none), which is why the fuzzy matcher found no counterpart. The same is probably the reason for the other "unmatched" air-group functions in
the air-group functions listed in [open-questions.md](../open-questions.md): the code exists but Ghidra never created functions there. (`find_code_gaps` on 1.163 lists 7,316 gaps, most of them small unwind fragments; real missing functions are a subset.)


### What the function does (read from the 1.151 annotated decompilation) [code]
* **Per frame, for each group:** run the children's logic; if the group's range-left value (`+0x24c`) is 0 the group disbands (children are removed); otherwise it flies. The group steers toward its target at a
  limited turn rate (`+0x2ac` = 4.0 from `CreateMapAircraftGroup`, scaled by dt), moves `speed * 0.001 * dt`, and **spends `+0x24c` by the distance moved**, so range left is "fuel". A timer at `+0x168` (cap `9000.0`)
  grows by `dt * 9000 / 300`.
* **Return state:** field `+0x338` (upper half) value `4` means "returning". When the group is farther than `rangeLeft - 100` from its home fleet it switches to returning. While returning (and when the
  support flags `petr_Support_` / a second flag are on) it calls `ReconcileMapAircraftGroupOwners`, and if it is within `20.0` of its home fleet it lands (`0x1400e65c0` in 1.151).
* **Engagements it starts (this is the missing link for the engagements section at the end):**
  * With the group's weapon total (`+0x2fc + +0x304`) above zero it scans the profile's MapCraft vector for an object on the **opposite side** (the product of the two `vtable+0x178` side values is `<= 0`),
    optionally restricted to its own target, and tests `CheckMapMotionEncounter` (the closest-approach test, `FUN_1400ec440` in 1.163). On a hit, and only if no engagement is pending (the global
    `loadAircraftMaps_`, our `DAT_143a11902`), it fills the side lists (A = the other object plus the group, plus every other MapCraft within `15.0` of either), and calls
    `SetLevelSeriaToLoad_("CraftsVsCrafts.seria")`.
  * Otherwise it scans the Missile vector the same way and, on a hit that is not a missile aimed at this group, builds the side lists (group plus other crafts that also meet the same missile) and calls
    `SetLevelSeriaToLoad_("CraftsVsMissile.seria")`. If that missile is the group's own target the group switches to returning.
* **So `CraftsVsCrafts`/`CraftsVsMissile` are loaded from here**, not from the fleet update; the fleet update starts `Missile.seria` and `Bombers.seria`. This answers the open question in `open-questions.md` about
  who sets up those two levels: it is the group update.

## Map-level intercepts (`runMissileandAircraftIntercept_`, `handleMissileIntercepts`)
`runMissileandAircraftIntercept_` is 1.151 `0x14010b4d0` and 1.163 `0x140111110` (the engagements section at the end uses the 1.163 address). The 1.163 copy is identical in structure. logdot's comment in both
copies: *"The probabilities are 75% of intercept for missiles, 66% for aircraft."* [code, both versions]

* **Missile kill:** among the Missile vector, for the entry that has the same target as the missile being processed (or the same stored position), `Random_Float(0,1) < 0.75` sets that missile's
  `launched_health` (`+0x2b0`) to 0, which kills it. If the roll fails, the loop breaks only when the missile still has health. The engagements section at the end has both rolls (75% missile, 66% craft).
* **Message and sound:** when the missile belongs to the opposing side (the two `vtable+0x178` side values have opposite signs) it prints `MISSILE_INTECEPTED` and plays `radio_kill_06`
  on the `MAPMODE_RADIO_HANDSET` gui element.
* **Craft down:** for the MapCraft that shares the missile's target it takes up to **3** of the group's children and rolls `< 0.66` for each; a hit calls the damage slot (`vtable+0x208` in 1.151,
  `+0x210` in 1.163) with `100.0`; then it prints `CRAFT_DOWN <n>`. Matches the engagements section at the end ("at most 3 crafts per pass, about 2/3 chance each"; `vtbl+0x210`).
* **Differences 1.151 -> 1.163:** only vtable slot numbers and the Profile vector offsets (see [version-differences.md](../version-differences.md)). The probabilities are unchanged, so the roadmap items on evasive manoeuvres and
  on defenders would change these two constants or add a per-fleet modifier here.

## The fleet update (`UpdateStrategicFleet`, 1.151 `0x14010c3a0`, 1.163 `0x140111ff0`)
Very large (2,072 decompiled lines in 1.151; the matcher scored 0.76 against `FUN_140111ff0`). Read by pattern (calls, strings, constants), not line by line. [code]

* **Four level loads exist, split between two places.** The fleet update calls `SetLevelSeriaToLoad_` with `"Missile.seria"`, `"Bombers.seria"` and **`"Combat.seria"`** (fleet against fleet). The two craft levels
  (`CraftsVsCrafts`, `CraftsVsMissile`) are started from `UpdateMapAircraftGroup` (previous section). The engagements section at the end lists `Missile`, `Bombers` and `Combat.seria` (fleet against fleet).
  Before each load the function fills the side lists (the same global vectors as in the engagements section at the end; in 1.151 `DAT_143944488`/`DAT_1439443c0`) and stores the bearing in a global (`DAT_147eed998`, the camera/approach angle).
* **Missile launch hand-off confirms the cooldown field.** `if (field_0x508 == 0.0) initProfileMissiles_(fleet) else countdown`: in 1.151 the **missile** cooldown is `+0x508` and the consumer is
  `initProfileMissiles_` (the same name as the 1.163 map-launch consumer `FUN_1400eced0`). In 1.163 it is `+0x50c` (shift +4), and the aircraft cooldown is `+0x510` ([ai-aircraft-launch.md](ai/ai-aircraft-launch.md)).
* **Refuel inside the same function:** the rate expression `fuelingProgress * 200.0` is visible in 1.151, matching `../mods/refuel.md` (`RATE = 200` at a type-4 station) and the `MULSS` sites patched by
  highfleet-refuel. `handleRefuelingNoises_` is called when the refuel flag is on (1.163 `0x1400fe8b0`).
* **Sounds the update plays** (all by name): `mission_end` (radio, at most once per 3 seconds via `GetTicks___`), `turbine_01`, `pump`, `pump_on`, `pump_off`, `engine_rocket_03`, `engine_ignit_int`,
  `env_horn`, `env_ship_landing`. GUI element `MAPMODE_THRUST_SLIDER` is read twice. For the roadmap item "audio cue when aircraft intercept": the existing intercept cue is `radio_kill_06`
  on `MAPMODE_RADIO_HANDSET` (previous section), so reusing it for the aircraft-intercept level load in `UpdateMapAircraftGroup` is a one-line idea.
* Other named calls visible in it (1.151 names): `traverseEscadraMissiles_` (x3), `somethingEvacPods` (x3), `rescueMinigame_`, `shipKill_`, `handleLootHazards`, `miscMapSomething2_`,
  `CheckMapMotionEncounter` (x2), `CreateShell_`, `displayTextOnCreature_`, `validateFloatArray_`, `CreateTriggerVal` (x2, `"TUTORIAL"`).
* logdot's only comments in it: `/* TUTORIAL */` and *"ship curr detached at 460. Maybe somecount at 461??"* (a Body field `shipCurrDetatched?` at `+0x458`/`+0x461`, 1.151 numbering).

## Live-test recipe
* Breakpoints on the two `SetLevelSeriaToLoad_` calls inside `0x140117840` (search the function for the strings `CraftsVsCrafts.seria` at `0x140360478` and `CraftsVsMissile.seria` at `0x140360490`) show which engagement starts and the side lists A/B (`0x143a158e0`, `0x143a159c0`).
* Breakpoint inside `0x140111110` at the two `Random_Float` compares: read the roll against `0.75` (missiles) and `0.66` (aircraft).

## Engagements: map to battle [game unless marked]
Moved from the retired `systems.md` (2026-10-19).

* Loader `FUN_14025afd0(level, bool, bool)` stores the name (global `DAT_1403c1390`), sets **`DAT_143a11902 = 1`** (an engagement is pending; blocks a second one in the same pass), then `FUN_1402db350`.
* Four global vectors of smart-refs describe the sides: **A `0x143a158e0`** (ours), **B `0x143a159c0`** (the other side), C `0x143a158b0`, D `0x143a13de8`.
* Observed: `Missile.seria` (a missile threatens our fleet): A=[Escadra], B=[Missile]. `Bombers.seria` (air raid): A=[**MapCraft**, one object carrying the planes], B=[Escadra].
  `CraftsVsMissile.seria` / `CraftsVsCrafts.seria` are started from the map aircraft group update `FUN_140117840` (two `SetLevelSeriaToLoad_` calls, side lists built from objects within 15.0); `Combat.seria` (fleet against fleet) is started from the fleet update beside `Missile` and `Bombers` [code, [findings/map-air-groups.md](map-air-groups.md)]. None of the craft flows observed in game yet.
* Trigger for `Missile.seria` (inside `FUN_140111ff0`): the first missile for which `FUN_1400ec440` is true and sides are opposed wins; the lists are cleared, **that one missile** goes into B,
  nearby friendly fleets into A, the loader is called. A volley of three therefore produced three fights in a row.
* Scenarios are state machines inside the giant `FUN_1402ac970` (branch by `LVL_SCRIPT` name). `SCR_MISSILE` at `0x1402c4baf`; state byte-table `0x1402c7a00`, offsets `0x1402c79e4`.
  State 1 (`0x1402c4dfc`) calls **`FUN_1402d45c0`**: sorts the defender fleet's ships, spawns up to 4 (`FUN_1402672c0`), then reads **only B[0]**: `for i < B[0]+0x248` it creates a
  missile with `EditorParts_DefinePart(0x143a139f0, string at B[0]+0x2b8, level, 1)` at a random offset, calls `FUN_140263700` on each new body to pick its target ([strategic-missile-target-assignment.md](strategic-missile-target-assignment.md)), then zeroes the count of the **original** map Missile (`[0x143a159c0]+8`, not a copy) [code, 2026-10-19].
  On leaving the scene the exit handler **`FUN_1402d4f20`** (1.151 `0x1402ab190`) adds the number of surviving spawned bodies (vector `DAT_147fc73d8..DAT_147fc73e0`, 0x18 bytes per entry) back into that Missile's `+0x248`, if its class code is `0x400000001047` (Missile); so missiles that were not used return to the map as a count [code, 2026-10-19].
* So a salvo fights as one only if the first missile's count is the sum; pushing extra list entries is ignored [game].
* Map-level shooting: `FUN_140111110` (from `FUN_1400f11b0`) first rolls **75%** to kill a missile aimed at the same target (`MISSILE_INTECEPTED`, sound `radio_kill_06` on `MAPMODE_RADIO_HANDSET`), then downs at most 3 crafts per pass with a **66%** roll each (`CRAFT_DOWN`, `vtbl+0x210`) [code]. Both probabilities are literal `Random_Float` compares, unchanged since 1.151.

## Ground defense (`AADefense`, class `0x80007`) [code, 1.151 read]
Moved from the retired `systems.md` (2026-10-19).

1.151 `createGroundDefenseCreatures__` (`0x140004950`) builds an `AADefense` object (logdot: "This 0x80007 only shows up for ground defense creatures") with a linked `Runner` creature and `MDL_WHEEL_01` wheels. `AADefense::FireMissile__` (`0x140005370`) is its state machine: it needs one part each of categories `0x10` (ammo), `0x20` (gun) and `0x800` (generator/quarters) plus at least two wheels, then flies a `MDL_MISSILE_01` (TTL 60.0, layer 7) at the nearest hostile within `500.0` when its reload timer (`+0x12c`, base `30.0` at `+0x128`) is zero. The 1.163 comment "Ground defense creatures?" on `FUN_1400e4530` is wrong: that constructor builds the MapCraft (0x340).
