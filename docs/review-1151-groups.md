# 1.151 annotation review, by function group (working file)

Local branch `review-1151-annotations` only. Continuation of `review-1151.md`: one section per group of 1.151 functions I read, with the 1.163 counterpart and what it adds to our notes.
Read-only on both Ghidra programs. Tags: **[code]** read from a decompilation, **[guess]**, **[tool]** fuzzy match. 1.151 names are logdot's.

<!-- MOVE: each group section goes to the doc named in its own MOVE comment; delete this file afterwards. Track progress in REINTEGRATION.md. -->

## Profile remap, 1.151 -> 1.163 (the world singleton): +0x48 for the vector block [code]
`Get_Profile` (1.163 `0x140292a90`, `Get_Profile_`) returns the `Profile`. The Ghidra `Profile` struct is the same size (1,380 bytes) and identical in both programs, which is a stale copy:
its vectors moved in 1.163.

| Vector | 1.151 (Ghidra name, offset) | 1.163 offset | Evidence |
|---|---|---|---|
| Escadras (fleets): begin/end | `escadras` `+0x1b0`/`+0x1b8` | `+0x1f8`/`+0x200` | `structures.md` already lists the friendly-fleet list at `+0x1f8/+0x200` [notes] |
| Missiles (map missiles): begin/end | `Missiles`/`MissileEnd` `+0x1e0`/`+0x1e8` | `+0x228`/`+0x230` | the map-launch consumer `FUN_1400eced0` pushes the new Missile at `+0x228` (end `+0x230`, cap `+0x238`) [code]; `structures.md` already says "missiles +0x228/+0x230" |
| MapCrafts (map aircraft groups): begin/end | `mapCrafts` `+0x228`/`+0x230` | `+0x270`/`+0x278` | 1.163 `CreateMapAircraftGroup` (`0x14010f8e0`) pushes the new group at `+0x270` (end `+0x278`, cap `+0x280`) [code] |
| `explosions`, `designs`, `items`, ... | `+0x1f0`, `+0x210`, `+0x278` | +0x48 presumably | [guess] |

* **Consequence for `structures.md`:** it says "fleets +0x270/+0x278". By this table `+0x270` is the **MapCraft** vector, and the fleet vector is the `+0x1f8` one. Two different readings of the same code
  gave "fleets" for `+0x270`; check one writer or iterator of `+0x270` before editing the notes. (A MapCraft stores its target at `+0x270` as well, which may have caused the mix-up; that is a field of the
  MapCraft object, not of the Profile.)
* Ghidra's stale label `mapCrafts` at `Profile+0x228` in the 1.163 program is really the Missile vector; the real MapCraft vector has no name there.
* Same method as the `Body` remap (`review-1151.md`): pair a function present in both versions, compare the offsets it uses.
* **Decisive confirmation (group 3 below):** `runMissileandAircraftIntercept_` is present in both versions. In 1.151 it walks `Profile.Missiles` (the missile-kill loop with the 75% roll) and then
  `Profile.mapCrafts` (the craft-down loop with the 66% roll); in 1.163 the **first** loop walks `+0x228/+0x230` and the **second** `+0x270/+0x278`. Same code, same roles, so Missiles `+0x1e0 -> +0x228` and
  MapCrafts `+0x228 -> +0x270` [code].

<!-- MOVE: this section -> structures.md ("Map missile" section, world singleton line) after the "+0x270 is fleets or MapCrafts" check. Also add to the 'Version differences' subsection. FLAG for logdot. -->

## Group 1: strategic AI aircraft launch

### `TryLaunchAiAircraftGroup` (1.151 `0x1400ea210`, 1.163 `0x1400ef910`) [code]
Present in both versions and almost identical; the 1.163 copy is still named by the machine-propagated `rep_1400ea210_...` and is a good name to apply. What it does (it decides when an AI fleet launches its
aircraft against a detected target):

* Preconditions (all must hold): a target exists; the fleet has aircraft (`count` > 0, 1.151 `+0x4e8`, 1.163 `+0x4ec`); distance to the target `< range * 0.45`
  (range at 1.151 `+0x4f0`, 1.163 `+0x4f4`); the aircraft cooldown is 0 (1.151 `+0x50c`, 1.163 **`+0x510`**); the fleet state float at `+0x188` is 0; the target's field `+0x78` is below a limit; and distance `> 200`.
* **The limit on the target's `+0x78` was raised from `480.0` (1.151) to `1200.0` (1.163).** Whatever that field is (a detection or range value of the target), the AI now launches against much
  more distant targets.
* **How many aircraft:** all of them (`count`). If `count > 10`, a coin flip (`Random_Int(0,1)`) halves it. The loop then builds the list of aircraft, picking loadouts by weight from the `PLANE_TLL` table, until
  `count` is used up, and passes the whole list to `CreateMapAircraftGroup`. So the AI launches **one group containing all (or half of) its aircraft at once**: this is exactly the roadmap bug
  "Strategic AI deploys all aircraft upon player detection within strike range, leaving none for defensive interception". A fix is a limit on the group size (for example keep a reserve) at that loop.
* After the launch: cooldown `1800.0` (`0x44e10000`) is written to the aircraft cooldown, and a time stamp `hourCount + 24` (1.151 `+0x518`, 1.163 `+0x528`) is stored.
* **Fleet field shifts** in this function: count `+0x4e8 -> +0x4ec`, range `+0x4f0 -> +0x4f4`, aircraft cooldown `+0x50c -> +0x510`, time stamp `+0x518 -> +0x528`, state `+0x188 -> +0x188`. The missile-launch
  cooldown (`+0x50c` in 1.163, which `highfleet-salvo` patches) is therefore a **different** field from the aircraft cooldown (`+0x510`); in 1.151 the missile cooldown is `+0x508`.

<!-- MOVE: -> roadmap.md (Strategic AI item 1: "all aircraft launched" with the location and the knobs) and systems.md (new subsection "Strategic AI aircraft launch"); the fleet field shifts -> structures.md fleet row. -->

### `CreateMapAircraftGroup` (1.151 `0x140109de0`, 1.163 `0x14010f8e0`) [code]
Matcher found no counterpart (score < 0.7), but the 1.163 call from `TryLaunchAiAircraftGroup` reaches `0x14010f8e0` (still named `rep_140109de0_...free`), so that is it.
* Same shape in both: `New(0x340)`, `Mark` constructor, group speed and range taken as the **maximum `launched_speed` (stats `+0x158`) and `launched_range` (stats `+0x160`)** over the members, start point from
  the launching fleet or the given target, constants set on the new object (1.163: turn rate `4.0` at `+0x2ac`, `60.0` at `+0x250`, `1.56` at `+0x254`, `30.0` at `+0x2b0`, `9000.0` at `+0x168`,
  `100.0`/`1000.0`/`20.0` at `+0x174/+0x178/+0x17c`, `type = 4` at `+0x29c`), then the group is added to the MapCraft vector and `loadAircraftWeaponsFromBotMenu` (1.151 `ComputeMapAircraftWeaponStrength`) fills the
  group's weapon totals at `+0x2fc/+0x304`.
* **New in 1.163:** if the group has no linked target, it scans the profile's `designs` list for an entry within distance 1.0 with `+0x2e8 > 1` and `+0x248 != 0` and links it. Unexplained; probably a
  base/landing target.
* The group's `+0x29c` type is `4`; map missiles use `1` to `3` (`3` = ground), so `+0x29c` is the map-object kind.

<!-- MOVE: -> structures.md (MapCraft row details) and systems.md (air raid subsection). -->

## Group 2: the map aircraft group update (`UpdateMapAircraftGroup`)

### Where it is in 1.163 [code]
1.151 `UpdateMapAircraftGroup` is at `0x140111980`. Its 1.163 counterpart is at **`0x140117840`**: the prologue is identical in shape (`mov rax,rsp`, push rbp/rsi/rdi/r12-r15, `sub rsp,0x1b0`), the strings
`CraftsVsCrafts.seria` (`0x140360478`) and `CraftsVsMissile.seria` (`0x140360490`) are referenced from inside it, and our `systems.md` already calls it `FUN_140117840`. **The 1.163 program has no function
defined at `0x140117840`** (`get_function_by_address` finds none), which is why the fuzzy matcher found no counterpart. The same is probably the reason for the other "unmatched" air-group functions in
`review-1151.md`: the code exists but Ghidra never created functions there. (`find_code_gaps` on 1.163 lists 7,316 gaps, most of them small unwind fragments; real missing functions are a subset.)

<!-- MOVE: -> open-questions.md / roadmap.md (Ghidra side): "create function at 0x140117840 (and check the other three air-group entries) in the 1.163 program". FLAG for logdot. -->

### What the function does (read from the 1.151 annotated decompilation) [code]
* **Per frame, for each group:** run the children's logic; if the group's range-left value (`+0x24c`) is 0 the group disbands (children are removed); otherwise it flies. The group steers toward its target at a
  limited turn rate (`+0x2ac` = 4.0 from `CreateMapAircraftGroup`, scaled by dt), moves `speed * 0.001 * dt`, and **spends `+0x24c` by the distance moved**, so range left is "fuel". A timer at `+0x168` (cap `9000.0`)
  grows by `dt * 9000 / 300`.
* **Return state:** field `+0x338` (upper half) value `4` means "returning". When the group is farther than `rangeLeft - 100` from its home fleet it switches to returning. While returning (and when the
  support flags `petr_Support_` / a second flag are on) it calls `ReconcileMapAircraftGroupOwners`, and if it is within `20.0` of its home fleet it lands (`0x1400e65c0` in 1.151).
* **Engagements it starts (this is the missing link for `systems.md`):**
  * With the group's weapon total (`+0x2fc + +0x304`) above zero it scans the profile's MapCraft vector for an object on the **opposite side** (the product of the two `vtable+0x178` side values is `<= 0`),
    optionally restricted to its own target, and tests `CheckMapMotionEncounter` (the closest-approach test, `FUN_1400ec440` in 1.163). On a hit, and only if no engagement is pending (the global
    `loadAircraftMaps_`, our `DAT_143a11902`), it fills the side lists (A = the other object plus the group, plus every other MapCraft within `15.0` of either), and calls
    `SetLevelSeriaToLoad_("CraftsVsCrafts.seria")`.
  * Otherwise it scans the Missile vector the same way and, on a hit that is not a missile aimed at this group, builds the side lists (group plus other crafts that also meet the same missile) and calls
    `SetLevelSeriaToLoad_("CraftsVsMissile.seria")`. If that missile is the group's own target the group switches to returning.
* **So `CraftsVsCrafts`/`CraftsVsMissile` are loaded from here**, not from the fleet update; the fleet update starts `Missile.seria` and `Bombers.seria`. This answers the open question in `open-questions.md` about
  who sets up those two levels: it is the group update.

<!-- MOVE: -> systems.md "Engagements: map -> battle" (add the two flows, with the 15.0 radius and the side-product rule); -> roadmap.md under the "audio cue/auto-pause when aircraft intercept" item:
     the hook point is the two SetLevelSeriaToLoad_ calls; -> open-questions.md remove the "never observed" line for CraftsVsMissile/CraftsVsCrafts. -->

## Group 3: map-level intercepts (`runMissileandAircraftIntercept_`, `handleMissileIntercepts`)

`runMissileandAircraftIntercept_` is 1.151 `0x14010b4d0` and 1.163 `0x140111110` (our `systems.md` already uses the 1.163 address). The 1.163 copy is identical in structure. logdot's comment in both
copies: *"The probabilities are 75% of intercept for missiles, 66% for aircraft."* [code, both versions]

* **Missile kill:** among the Missile vector, for the entry that has the same target as the missile being processed (or the same stored position), `Random_Float(0,1) < 0.75` sets that missile's
  `launched_health` (`+0x2b0`) to 0, which kills it. If the roll fails, the loop breaks only when the missile still has health. **`systems.md` currently mentions only the 66% craft roll; add the 75% missile roll.**
* **Message and sound:** when the missile belongs to the opposing side (the two `vtable+0x178` side values have opposite signs) it prints `MISSILE_INTECEPTED` and plays `radio_kill_06`
  on the `MAPMODE_RADIO_HANDSET` gui element.
* **Craft down:** for the MapCraft that shares the missile's target it takes up to **3** of the group's children and rolls `< 0.66` for each; a hit calls the damage slot (`vtable+0x208` in 1.151,
  `+0x210` in 1.163) with `100.0`; then it prints `CRAFT_DOWN <n>`. Matches `systems.md` ("at most 3 crafts per pass, about 2/3 chance each"; `vtbl+0x210`).
* **Differences 1.151 -> 1.163:** only vtable slot numbers and the Profile vector offsets (see the Profile remap). The probabilities are unchanged, so the roadmap items on evasive manoeuvres and
  on defenders would change these two constants or add a per-fleet modifier here.

<!-- MOVE: -> systems.md "Engagements" last bullet ("Map-level shooting"): add the 75% roll, the side check and the radio sound; -> roadmap.md under the strategic-AI items: where the intercept
     probabilities live (two Random_Float constants, 0.75 and 0.66, inside this function). -->

## Group 4: the fleet update (`UpdateStrategicFleet`, 1.151 `0x14010c3a0`, 1.163 `0x140111ff0`)
Very large (2,072 decompiled lines in 1.151; the matcher scored 0.76 against `FUN_140111ff0`). Read by pattern (calls, strings, constants), not line by line. [code]

* **Four level loads exist, split between two places.** The fleet update calls `SetLevelSeriaToLoad_` with `"Missile.seria"`, `"Bombers.seria"` and **`"Combat.seria"`** (fleet against fleet). The two craft levels
  (`CraftsVsCrafts`, `CraftsVsMissile`) are started from `UpdateMapAircraftGroup` (group 2). `systems.md` lists `Missile` and `Bombers` only; add `Combat.seria` as the fleet-vs-fleet start.
  Before each load the function fills the side lists (the same global vectors as in `systems.md`; in 1.151 `DAT_143944488`/`DAT_1439443c0`) and stores the bearing in a global (`DAT_147eed998`, the camera/approach angle).
* **Missile launch hand-off confirms the cooldown field.** `if (field_0x508 == 0.0) initProfileMissiles_(fleet) else countdown`: in 1.151 the **missile** cooldown is `+0x508` and the consumer is
  `initProfileMissiles_` (the same name as the 1.163 map-launch consumer `FUN_1400eced0`). In 1.163 it is `+0x50c` (shift +4), and the aircraft cooldown is `+0x510` (group 1).
* **Refuel inside the same function:** the rate expression `fuelingProgress * 200.0` is visible in 1.151, matching `systems.md` (`RATE = 200` at a type-4 station) and the `MULSS` sites patched by
  highfleet-refuel. `handleRefuelingNoises_` is called when the refuel flag is on (1.163 `0x1400fe8b0`).
* **Sounds the update plays** (all by name): `mission_end` (radio, at most once per 3 seconds via `GetTicks___`), `turbine_01`, `pump`, `pump_on`, `pump_off`, `engine_rocket_03`, `engine_ignit_int`,
  `env_horn`, `env_ship_landing`. GUI element `MAPMODE_THRUST_SLIDER` is read twice. For the roadmap item "audio cue when aircraft intercept": the existing intercept cue is `radio_kill_06`
  on `MAPMODE_RADIO_HANDSET` (group 3), so reusing it for the aircraft-intercept level load in `UpdateMapAircraftGroup` is a one-line idea.
* Other named calls visible in it (1.151 names): `traverseEscadraMissiles_` (x3), `somethingEvacPods` (x3), `rescueMinigame_`, `shipKill_`, `handleLootHazards`, `miscMapSomething2_`,
  `CheckMapMotionEncounter` (x2), `CreateShell_`, `displayTextOnCreature_`, `validateFloatArray_`, `CreateTriggerVal` (x2, `"TUTORIAL"`).
* logdot's only comments in it: `/* TUTORIAL */` and *"ship curr detached at 460. Maybe somecount at 461??"* (a Body field `shipCurrDetatched?` at `+0x458`/`+0x461`, 1.151 numbering).

<!-- MOVE: Combat.seria + the cooldown-field fact -> systems.md ("Engagements" first bullet and "Map launch" consumer bullet); the sound names -> roadmap.md (audio cue item) and a new
     short "Sounds" list in content.md; the named calls -> nowhere (only for finding code later). -->

## Group 5: cluster munitions and the bomblet TTL (roadmap: "Make TTL adjustable for cluster munitions and mine bomblets")

* **1.151:** `Projectile_ExplodeAndCluster(projectile, ?, multiplier, maxCount, ttl)` at `0x14002c170`, called only from `creatureLogic` (`0x1400335b0`). It spawns
  `min(explosive * multiplier, maxCount)` bomblets; each is `New(0xa08)` + `Body::Body` (1.151 Body size, see the corrected size in `review-1151.md`), `CreateShell_`, `is_bullet`, owner = the projectile's owner,
  **`timeToLive = ttl`**, `desowningTime = ttl`, `ttlDesolveTime = 0.1`, `collisions = 2`, health/maxHealth `5.0`, each carrying `explosive / count`. Difficulty scaling: if the owner is a player-side creature
  the "dud" flag chance is `5% * (0.3 on difficulty 0, 0.6 on difficulty 1, 1.0 otherwise)`. Then it spawns the smoke/flash sprites ("strides" and "strides_fire" sounds, 1.151 `PlayRadioSound_`).
* **1.163:** the same job is done by **`FUN_140032fb0`** (`FireGun`'s next function): `(shooter, ?, count, damageA, damageB, ttl, angle)`. The bomblet fields now sit at the shifted offsets (TTL `+0x2c0`, desowning `+0xf0/+0xf4`,
  `ttlDesolveTime +0x2c4 = 0.1`, `collisions +0x2b8 = 2`, health `+0x2c8`/`+0x2cc` `= 5.0`), which confirms the Body remap. The **TTL is the sixth argument and is written to three fields**, so
  adding a config multiplier there (one place) makes cluster/mine bomblet lifetime adjustable. No caller was found by `get_function_callers` (the function is probably reached through a table or a jump from
  `FireShell`); finding the call sites is the remaining step, search for calls into `0x140032fb0` or the constants passed as the sixth argument.
* **Not this function:** `FUN_14002f480` (it also plays "strides") is the **active-protection burst** (KAZ): it tests nearby incoming bullets and missiles by stats category (`0x4000`, `0x8000000`, `0x200000`
  are excluded) within `60.0` / `120.0`, and damages them with the vtable damage slot. That is the code behind the "KAZ" part category in `structures.md` (bit 25) [guess]; its caller is `FUN_14007eb50`.

<!-- MOVE: -> roadmap.md under the TTL item (give both addresses and the sixth-argument remark); the KAZ remark -> systems.md (new short "Active protection" subsection) after a check of the category bit. -->

## Coverage so far, and what is left
Read in detail: `TryLaunchAiAircraftGroup`, `CreateMapAircraftGroup`, `UpdateMapAircraftGroup`, `runMissileandAircraftIntercept_`, `UpdateStrategicFleet` (by pattern), `FireGun`, `copyOverBody`,
`createNewBody`, `Projectile_ExplodeAndCluster`, `AADefense::FireMissile` (below), plus the Body and Profile struct layouts.
Not read yet (about 540 of the ~875 hand names): `creatureLogic` and its named pieces, `handleEndgameContent` and the `spawn*` family, `calcDMGPercentage` (trivial: `damage / maxHealth`), `FireShell`, `shipKill`,
`handleRamming`, `checkJammed`/`handleIRST`, the stats getters (`GetLaunched*`, `GetMissile*`, `GetThrust`, `returnMass`, `StatLegForce`), `CalculateStats`/`CalculateSectors`, the level-script labels
(`SomethingWithLevelSerias_*`), save/load (`serializeProfile`, `Save`, `Load`), shop/editor/UI functions, the HGE interface names, and the 1,449 data types.
Reading by brute force (batch decompile of all names) costs about 20-30k tokens per 40-100 functions and returned mostly library plumbing in the first two batches; the rest should be read by theme.

### Side finding: ground defense (`AADefense`) [code]
1.151 `createGroundDefenseCreatures__` (`0x140004950`) builds an `AADefense` object (class code `0x80007`, a comment by logdot: "This 0x80007 only shows up for ground defense creatures") with a linked
`Runner` creature and `MDL_WHEEL_01` wheels; `AADefense::FireMissile__` (`0x140005370`) is its state machine: it needs one part each of categories `0x10` (ammo), `0x20` (gun) and `0x800` (generator/quarters) plus
at least two wheels, then flies a `MDL_MISSILE_01` (TTL 60.0, layer 7) at the nearest hostile within `500.0` when its reload timer (`+0x12c`, base `30.0` at `+0x128`) is zero. Relevant to the
roadmap's tactical-AI items on what the AI can and cannot use; the 1.163 `Ground defense creatures?` comment on `FUN_1400e4530` is thus about a different class (see the MapCraft finding).
<!-- MOVE: -> systems.md (ground defense paragraph) and structures.md class table (0x80007 = AADefense). -->

## Group 6: the stats record (`ShipPart`, `GetStats` getters) [code + Ghidra struct]
In 1.151 the stats record is the Ghidra struct `ShipPart` (384 = `0x180` bytes; 1.163 allocates `0x188`, `New(0x188)` in `CopyObject`, and has no `ShipPart` struct at all). The 1.151 getters
(`GetLaunchedRange`, `GetThrust`, `GetMissileAp`, ... each is `GetShipPart(part_index)->field`) confirm which field name belongs to each offset. Comparing with the stats row in `structures.md`:
**the record grew by 8 bytes = two fields inserted in 1.163**, and everything in the notes agrees with that.

| 1.151 field (offset) | 1.163 offset | Note |
|---|---|---|
| `m_oid` `0x48`, `icon_name` `0x68` | same | |
| `price` `0x88`, `important` `0x8c`, `timecost` `0x90`, `repair_cost` `0x94` | same | notes [V] |
| `resources` `0x98` (and `edPropResources` `0xa0`) | same | repair/resource list; `repairPartsStats` returns its element count |
| `category` `0xb0`, `sort_index` `0xb4` | same | notes [V] |
| `burn_hp_max` `0xb8`, `burn_ignite` `0xbc`, `burn_heat` `0xc0` | same | **new names**: burning parameters (not in the notes) |
| `mdl_armor` `0xc4` | same | notes [V] |
| **`mdl_fuel_capacity` `0xc8` (double)** | same [?] | see the flag below |
| `mdl_fuel_need` `0xd0` | same | notes [V] |
| **`mdl_crew_capacity` `0xd4` (int)**, `mdl_crew_need` `0xd8` | same | see the flag below |
| `mdl_power` `0xdc`, `mdl_power_need` `0xe0`, `mdl_power_priority` `0xe4` | same | notes list `power_need` only |
| `mdl_ammobox` `0xe8`, `ammobox_need` `0xec`, `ammobox_priority` `0xf0`, `mdl_fss_capacity` `0xf4` | same | new names |
| `mdl_thrust` `0xf8`, `mdl_thrust_map` `0xfc` | same | notes [V] |
| `mdl_at` `0x100`, `mdl_leg_force` `0x104`, `mdl_rotation` `0x108` | same | new names (`GetMdlAt`, `StatLegForce`) |
| `mdl_radar` `0x10c`, `tracking` `0x110`, `guiding` `0x114`, `elint` `0x118`, `irst` `0x11c`, `jammer` `0x120`, `lifesupport` `0x124` | same | notes [V] except `lifesupport` (new) |
| `mdl_sectors_type` `0x128` | same | notes [V] (non-zero = takes part in arc scanning) |
| *(new in 1.163)* | `0x12c` `sectors_shift` | the first inserted field |
| `mdl_sectors_threshold` `0x12c` | `0x130` | +4 |
| `signature_ir` `0x130`, `fxpos.x/.y` `0x134/0x138` | `0x134`, `0x138/0x13c` | +4; `signature_ir` and `fxpos` are new names |
| `weapon_priority` `0x13c` .. `weapon_rate` `0x14c` (`priority`, `caliber`, `load_amount`, `load_time`, `rate`) | `0x140` .. `0x150` | +4; `rate` `+0x150` is the value `FireGun` divides into 60 |
| `acceleration_time` `0x150`, `launched_speed` `0x154`, `launched_speed2` `0x158`, `launched_range` `0x15c` | `0x154`, `0x158`, `0x15c`, `0x160` | +4 |
| `missile_type` `0x160`, `missile_explosive` `0x164` | `0x164`, `0x168` | +4 (`+0x168 > 100000` = nuclear, verified in the queue filler) |
| *(new in 1.163)* | `0x16c` `cluster` | the second inserted field |
| `missile_ap` `0x168`, `agility` `0x16c`, `radar_range` `0x170`, `radar_cone` `0x174`, `fuze_type` `0x178`, `launched_health` `0x17c` | `0x170`, `0x174`, `0x178`, `0x17c`, `0x180`, `0x184` | +8 |

* **Flag for `structures.md`:** the notes call `+0xd4` "tank capacity (int; the part's current fuel is Body +0x804)". In 1.151 `+0xd4` is **`mdl_crew_capacity`** (int) and the **fuel tank capacity is the double at `+0xc8`**
  (`mdl_fuel_capacity`), which also fits ship-level fuel being doubles (`+0x1638/+0x1640`). Likely correction: `+0xc8` tank capacity (double), `+0xd4` crew capacity. Verify with a fuel tank and a crew module in `OL.seria` before editing.
* **`GetMissileFuzeType`** is the only getter returning an int; all others return floats, which the notes' units already assume.
* **`GetPartPrice`** returns 0 when `endWar` is set (Profile field `endWar`, Ghidra offset 657 = `0x291` in 1.151) or when the part's category has bit 6 (`0x40`, "block, bridge") set; otherwise `price`. This is why bridge/block
  parts are free to swap in the editor and why prices vanish after the war ends. Not in the notes.
* The notes' sentence "Stats record ... `GetStats(index)` `FUN_140281e00`" is right: 1.163 `GetStats` is a bounds-checked pointer-array lookup (checked); the 1.151 name is `GetShipPart`.

<!-- MOVE: this table -> structures.md "Stats record" (replace the offset list with the full named list and add a 'version differences' line: 1.163 inserts sectors_shift and cluster); the GetPartPrice rule -> systems.md or formats.md (OL.seria row). FLAG +0xd4 vs +0xc8 for review. -->

## Group 7: the end game (`spawnEndgameShips_`, 1.151 `0x14023fa80`) [code]
Present in 1.151 as a named function; **not matched** by the fuzzy tool, **located by hand in 1.163 as `FUN_140261a20` (group 18)**. It is the scripted collapse that begins the "nuclear war" and closes the campaign. Read from the
1.151 decompilation (very long: three-way list sorting plus spawns).

* **Cities used by name:** `KHIVA` (the capital) and `BASRA`. Everything is positioned relative to `KHIVA`'s position.
* **Phase 1, sort the garrisons:** it walks the profile's city list (the vector at Ghidra offset 456/464) and drops those that already have a hostile fleet with `side > 0` within `700.0`. The remaining cities (with
  `moid+0xc != 0`, i.e. an active flag) are split into **four lists by quadrant relative to Khiva** (x below/above, y below/above) and each list is sorted by distance (`MergeSortObjectListByScratchKeyDescending`,
  key at `+0xf8`). The first city of each list gets state `2` at `+0x19c`.
* **Phase 2, strike groups:** from the cities with state `2` it picks one at random and spawns `spawnEndgameStrikeGroups_(strength 100.0, -1.0, position, name, 1)` for each; every fleet gets type `6`, its
  target set to Khiva's position, and enters the profile fleet vector; their `moid+0xc` is set to `3`.
* **Phase 3, reinforcement search:** up to **100 tries** to find a city (`+0x2e8 > 1`, active, 2000 to 4000 units from Khiva, not already occupied by a hostile fleet) and spawn another strike group
  there with strength `200.0` (normal) or `300.0` (hard mode, `Profile.hardMode`). Fleets from this phase get ships `Tarantul` (66%) or `Tarantul ARM` (34%).
* **Phase 4, garrison ships:** for every city with garrison strength it spawns ships through `somethingSpawnShips` (divides the strength by `20.0` or `50.0` depending on the city kind) and copies up to 3 of
  the generated names into the city record.
* **Finale:** `BASRA`'s record is cleared; then, **"Start the nuclear war"** (logdot's comment): if `Profile.escalation == 0` it shows `THE_BEGINNING` / `NUCLEAR_WAR`, plays `dram_hit_01`, and sets
  `escalation = max(escalation, 1)`; finally **`Profile.endWar = true`**. This is what `GetPartPrice` (group 6) checks, so after this function runs, part prices become 0.
* **Lead for the Khiva crash/loop bug in the roadmap: superseded by group 18.** An earlier version of this note said the finale was behind "list non-empty" guards and that the bug would be a state that never advances.
  That was wrong: the first write to each of the four quadrant lists is **unguarded** (group 18), in both versions, and the 1.163 counterpart is now located.

<!-- MOVE: -> roadmap.md under the "Capturing all cities around Khiva" bug (lead + names); -> systems.md (new short "End game" section: the three phases, endWar, escalation); -> open-questions.md (locate the 1.163 counterpart). -->

## Group 8: the HGE interface (`HGEVFTABLE`) [code + Ghidra struct]
1.151 has a named `HGEVFTABLE` struct (800 bytes = 100 slots, plus `HGE_Impl` 3,464 bytes and the `hge.h` / `hge.pdb` header types). 1.163 has none. Compared with `engine-hge.md`:

* **The 1.163 table is the 1.151 table plus one slot.** In 1.151 `Resource_Load` is slot 17 (`+0x88`) and `Resource_Free` slot 18; in 1.163 they are slots 18 and 19 with an extra "load file" method at 17
  (`engine-hge.md` already says this). So **the added file-loader slot is new in 1.163**; every slot at or after 17 is `+8` in 1.163, which is why `Random_Float` is `+0x108` in 1.151 and `+0x110` in 1.163,
  and the same `+8` applies to the Body vtable damage slot (`+0x208` -> `+0x210`) seen in group 3 (that one is a different vtable, but the same kind of change).
* **1.151 slot names** (stock HGE order, with the game's differences): 0 Release, 1 `System_Initiate`, 2 `System_Shutdown`, 3 `System_Start`, 4 *(unnamed: GetErrorMessage)*, 5 `System_Log`, 6 *(unnamed: one of
  Launch/Snapshot)*, 7-11 `System_SetStateBool/Func/(Hwnd)/Int/String`, 12-16 `GetState*`, 17 `Resource_Load`, 18 `Resource_Free`, 19 `AttachPack`, 20 `RemovePack`, 21 `RemoveAllPacks`, 22 `Resource_MakePath`,
  23 `EnumFiles`, 24 `EnumFolders`, 25-30 `SetInt/GetInt/SetFloat/GetFloat/SetString/GetString` (`Ini_*`), 31 `Random_Seed`, 32 `Random_Int`, 33 `Random_Float`, 34 `GetSeed`, 35 `GetTime`, 36 `GetDelta`,
  37 `GetFps`, 38 `EffectLoad`, 39 `EffectFree`, 40 `EffectPlay`, 41 `PlayEx`, 42 `StreamPlay`, 43 `MusicLoad`, 44 `MusicFree`, 55 `StreamLoad`, 56 `StreamFree`, 57-60 `ChannelUnknown`, 61-72 `Channel*` (`Pause`, `Resume`, `Stop`, `PauseAll`, `ResumeAll`, `StopAll`, `IsPlaying`, `GetLength`, `SetPos`, slot 70 unnamed, `SlideTo`, `IsSliding`), 77-87 input (`GetMousePos`,
  `SetMousePos`, `GetMoseWheel` [sic], `IsMouseOver`, `KeyDown`, `KeyUp`, `GetKeyState`, `GetKeyName`, `GetKey`, `GetChar`, `GetEvent`), 97 `showPoweredByHGE?`, 98/99 `GetSpriteWidth?`/`GetSpriteHeight?`
  (names with a question mark are logdot's guesses). The slots 45-54, 73-76 and 88-96 are unnamed in 1.151 (the stock header puts Gfx_/Target_/Texture_ there).
* **It answers the open question** in `open-questions.md` about which stock System_ method is missing: the table has **one** slot (6) between `System_Log` and `SetStateBool` where the stock header has two
  (`System_Launch`, `System_Snapshot`). Which one is still unnamed.
* All named slots match the HGE 1.8 header order, consistent with the notes' claim that the game uses a lightly modified stock HGE.
* Extra useful hook: `Resource_AttachPack` is slot 19 in 1.151 and **slot 20** in 1.163 (`engine-hge.md` says 20: consistent).

<!-- MOVE: -> engine-hge.md (interface table: add the 1.151 slot names column and the "added slot 17 is new in 1.163" fact); open-questions.md (update the missing System_ method line). -->

## Group 9: the save root, the `Profile` struct (names only) [code-struct, key pairing is a guess]
The save file `Saves/Profile_N/profile.seria` serialises the `Profile` object (1,380 bytes in both Ghidra programs; vectors moved by +0x48 in 1.163, see the Profile remap, and scalar offsets past
`0x1e0` are probably shifted too, so the offsets below are 1.151 values). `formats.md` lists the keys by observation; the field names below are logdot's and can help decide which key is which.

| Profile field (1.151 offset) | Likely save key (`formats.md`) |
|---|---|
| `countdown` `0x140`, `days` `0x144`, `daysFromEvent` `0x148` | `m_countdown` (days to the darkness event) |
| `enemyValue` `0x180`, `score` `0x184`, `scoreExpedition` `0x188`, `scoreMilitary` `0x18c`, `scoreSurvivors` `0x190` | the score counters (`m_scores` is the **starting cash** per the notes; here `cash` is a separate int at `0x260`; check which one the key is) |
| `escadras` `0x1b0`, `locations` `0x1c0`, `Missiles` `0x1e0`, `explosions` `0x1f0`, `designs` `0x210`, `mapCrafts` `0x228`, `mapMarks` `0x258`, `npcs` `0x268`, `items` `0x278` | `m_escadras`, `m_locations`, ... (the vectors) |
| `cash` `0x260`, `npcIndex` `0x264` | cash and the next-NPC counter |
| `reinforcementState` `0x28c`, `endRace` `0x290`, `endWar` `0x291`, `endStrike` `0x292`, `escalation` `0x294`, `flagshipLost` `0x298`, `burnFuel` `0x299`, `rams` `0x29c` | campaign state flags; **`endWar`/`escalation` are set by `spawnEndgameShips_`** (group 7) |
| `alert` `0x2a0`, `alertHr` `0x2a4`, `radioDuration` `0x2ac`, `radioDurationBase` `0x2b0` | alert level and radio timing |
| `enigmaSet1..4` `0x2b8..`, `enigmaKey1..12` `0x2c8..`, `enigmaGot1..12` `0x2f8..`, `enigmaTimer` `0x304` | the Enigma puzzle (12 keys, 12 "got" flags, a timer) |
| `tadsRecord` `0x308`, `intelData` `0x30c`, `ant` `0x310` | TADS record, intel counter, a flag named `ant` (`restOfEventsPrologueAntIsaiah` is the prologue event handler) |
| `charFear`, `charGerat`, `charRomani`, `charFaith`, `charRight`, `charForce`, `charWealth`, `charKindness` (ints `0x314..`) and the same eight `...Val` floats (`0x334..`) | `m_char_*`: the **eight player personality stats** (Fear, Gerat, Romani, Faith, Right, Force, Wealth, Kindness) as integer level and float value |
| `nextCreatureId` `0x358`, `nextHistoryDesign` `0x360` | id counters for new ships and saved designs |
| `trigger` `0x398`, `unlocks` `0x3d8`, `strigger` `0x418`, `events` `0x458`, `arguments` `0x498`, `demoState` `0x4b0`, `demoLoot` `0x4b8`, `inventory???` `0x4d8` | the string/number trigger tables (`CreateTriggerVal` reads these; `TUTORIAL_*`, `ESCALTION_WARNING` live here), unlocks, events |
| `mapSkyOffsetX/Y` `0x520/0x524`, `mapSkySteps`, `mapSkySeed`, `gameVersion` `0x548` | map sky, game version (written into the save) |

* **`Profile.gameVersion` (float at `0x548` in 1.151)** is what the version check `CORE_LAST_LOADED_VERSION` in `Config.ini` interacts with; the game version is also reachable through `GetGameVersionString` (`0x1401fa190`).
* The trigger tables are keyed by name: `CreateTriggerVal(&Profile+0x3f0, ...)` returns a reference to a named value (as seen in the tutorial code and in `ESCALTION_WARNING`). For save editing, these named
  values are the "flags" (tutorial progress, warnings) that a save editor may want to reset.

<!-- MOVE: -> formats.md "Save files" (field-name hints and the 8 personality names); keep the offsets out of the doc until verified for 1.163. -->

## Group 10: what 1.163 added or removed, from the string tables [code, `list_strings` diff of the two programs]
Method: all strings of both programs (6,800 in 1.151, 6,683 in 1.163), set difference. 229 strings only in 1.163 and 112 only in 1.151 (many are generated names or noise; the list below is filtered by hand).
A string being "only in" one version means that exact text is absent from the other program; code that builds a name at run time would not show up, so absence is a hint, not proof.

### New in 1.163
* **Skirmish and PVP modes:** level scripts `SCR_EDITOR_SKIRMISH`, `SCR_PRESELECT_SKIRMISH`, `SCR_PRESELECT_SKIRMISH_PVP`, `SCR_COMBAT_SKIRMISH`, `SCR_COMBAT_SKIRMISH_PVP`, `SCR_CITY_GENERATED_SKIRMISH`
  (plus `SCR_ED_RUN`, `SCR_DUNGEON`, `SCR_EMPTY`, `SCR_START`, `SCR_TITLE`), level files `EditorSkirmish.seria`, `PreselectSkirmish.seria`, `PreselectSkirmishPVP.seria`, `CombatSkirmish.seria`,
  `CombatSkirmishPVP.seria`, `City_generatedSkirmish.seria`, and a separate save directory **`SavesSkirmish/Profile_1..3`**. Title-menu keys `TITLE_SKIRMISH`, `TITLE_SKIRMISH_PVP`, `TITLE_HOTSEAT_DEVICE_*`,
  `TITLE_CONTROLS_HOTSEAT` (hot-seat two-player), `PRECOMBAT_PLAYER_1..4`, `PRESELECT_NPLAYERS`, `PRESELECT_MAX_WEIGHT`, `PROFILE_RESET_SKIRMISH_*`. The skirmish mode has its own profile, ship purchase
  (`SKIRMISH_BUY_SHIPS`, `ED_SHPWRK_BUY_SHIPS`) and **captain hiring** (`HIRE_CAPTAIN*`, `TRAIN_CAPTAIN*`, `SKIRMISH_HIRE_CAPTAIN*`, `totalCaptains`, `vecFreeCaptains`, `availableMassLevel`, `skirmishLevel`,
  `nextSkirmishEscadraLevel`, `skirmishAADs`). The `SCR_*` list in `formats.md` ("Levels") is therefore incomplete for 1.163: it lacks all of the above.
* **Controller support:** 1.163 links **SDL2** (`SDL2.dll`, `SDL_Init`, `SDL_JoystickOpen/Close/Name`, `SDL_NumJoysticks`, `SDL_PollEvent`, `SDL_Quit`; strings `Xbox Series X Controller`, `PS5 Controller`, `KEYBOARD`);
  1.151 used **DirectInput8** (`DINPUT8.dll`, `DirectInput8Create`, `GAMEPAD`, `MOUSE4`, `MOUSE5`). Relevant to the modloader (input hooks differ) and to the roadmap's mouse-sensitivity item.
* **Stats record fields (confirms group 6):** the strings **`m_mdl_sectors_shift`** and **`m_missile_explosive_cluster`** exist only in 1.163: these are exactly the two fields inserted in the stats record,
  so `OL.seria` in 1.163 can carry them. Also `MDL_MISSILE_CLUSTER_SFW_01` (a cluster missile part), `ITEM_HARPOON`, `ITEM_AMMO_57MM_TANK`, `ITEM_KAZ_AMMO`, `MDL_FIGHTER_01`, `ANTENNA_PART`.
* **KAZ (active protection) is a feature with ammo:** `ITEM_KAZ_AMMO` and the log line `HIDS %s activated.` (1.151 had `HIDS_ACTIVE %s activated.`: renamed). `m_tele_nukes_arm` / `m_tele_nukes_range` /
  `m_tele_dynamic_landing` / `m_tele_thrust_left_landing` / `m_tele_thrust_right_landing` are new telemetry keys (1.151 had `m_tele_nuke_range`): an in-game telemetry/landing readout.
* **New ships and names:** `Navarin Mk2`, `Navarin Mk3`, `Nomad Mk2`, `Lancer`, `Paladin`, `Titan`, `Gladiator LANCE`, `Egida`, `Novorossiysk`; `ALSAHIR_MESSAGE_COUNTER`, `CHECK_STARS`, `STATS_FEAR_EXTRA1/2`.
* **Graphics options:** `GFX_GLITCH_LEVEL`, `GLITCH_LEVEL_`, `RENDER_LAMP_ON/OFF` (1.151 had `GFX_GLITCH_LOW`, `GLITCHLOW_ON/OFF`: the on/off glitch option became a level). `D3DX11SaveTextureToFileA` (screenshot/texture dump) appears too.
* `GAME_TAKEOFF_TIME_AIR/BOMB/COMBAT/UNDEF`, `GAME_COUNTDOWN`, `LANDING_STAT_DAMAGE/EXPENDABLES/RADIATION/USVH`, `QUIT_TITLE_NO_ASK`, `Skirmish landing fixed` (a developer note left in the binary).

### Removed or renamed in 1.163
* **A debug HUD/overlay in 1.151:** `HGEFPS: %i`, `Batches: %i`, `Quads: %i`, `FILLRATE: %i%%`, `FXPSes: %i`, `Total particles: %i`, `BURN: %i`, `Render area: %f`, `cur time: %H:%M:%S`, and per-key
  lines `Key F1..F12: true` / `Render F1..F12: false`. None of these strings exists in 1.163, so the debug overlay was removed (or its text is built differently). For the modder-tools roadmap: the
  1.151 build is the reference for how the original overlay worked.
* `Media/fx.seria` (a 1.151 FX loader path and `ERR: FX load failed.`), `KHIVA`/`EHUDA`/`Big_Bouzouk`/`Mellifluous`/`Simple` strings (names that moved elsewhere), `ITEM_GUN37`.
* `m_tele_nuke_range` -> `m_tele_nukes_range`; `HIDS_ACTIVE %s activated.` -> `HIDS %s activated.`.

<!-- MOVE: Skirmish/levels -> formats.md ("Levels" list) and content.md; SDL2/DirectInput -> setup.md (modloader note) and roadmap.md (mouse sensitivity item); stats fields -> structures.md (stats row, 'version differences');
     debug HUD -> roadmap.md tooling section; ship names -> content.md. -->

## Group 11: the Ghidra type library, version by version [code, struct sizes vs allocation sizes]
`search_data_types` with a pattern containing a dot lists the `.conflict` duplicates, which exist for most project structs in 1.163 (a side effect of the earlier Version Tracking apply). Their sizes against the
real allocation sizes in `CopyObject` (`structures.md`) show which structs are already right in 1.163 and which are stale:

| Struct (`.conflict` in 1.163) | Ghidra size | Real 1.163 size | Status |
|---|---|---|---|
| `Node` | 296 (`0x128`) | `0x128` | OK |
| `Missile` | 776 (`0x308`) | `0x308` | OK |
| `Location` | 880 (`0x370`) | `0x370` | OK |
| `Sprite` | 424 (`0x1a8`) | `0x1a8` | OK |
| `AircraftLogic` | 432 (`0x1b0`) | `0x1b0` | OK |
| `Item` | 80 (`0x50`) | `0x50` | OK |
| `Body` | 2568 (`0xa08`) | `0xa40` | **stale** (+`0x38` missing) |
| `Escadra` | 1536 (`0x600`) | `0x618` | **stale** (+`0x18` missing) |
| `Creature` | 6358 | `0x1a50` = 6736 | **stale** (+378; the odd size shows the struct was patched by hand) |
| `GUI` | 3640 (`0xe38`) | `0xe70`..`0xf18` depending on the subclass | partly stale |
| `Profile` | 1380 (`0x564`) | not allocated through `CopyObject` | layout moved (group Profile remap) |
| `HGEVFTABLE` (800 bytes, 100 slots) | **absent in 1.163** | 101 slots | missing; 1.151 has it (group 8) |
| `ShipPart` (384 bytes) | **absent in 1.163** | `0x188` | missing; 1.151 has it (group 6) |

* **Order for the struct rebuild:** the OK structs need nothing; `Body`, `Escadra`, `Creature` get a remap (the Body remap is in `review-1151.md`; the Escadra shift so far: count `+4`, range `+4`, missile cooldown `+4`,
  aircraft cooldown `+4`, time stamp `+0x10`, i.e. +4 early and +0x10 by `+0x518`); `ShipPart` and `HGEVFTABLE` can be created from the tables in groups 6 and 8 (1.163 needs two extra stats fields and one extra vtable slot).
* **Cleanup:** every `*.conflict` type should end up replacing its non-conflict twin (the non-conflict `Body`, `BodyVFTABLE`, ... are the older 1.151 copies still referenced by names such as `createNewBody`'s
  signature). Do it only after a check of which functions use which twin.

<!-- MOVE: -> roadmap.md Ghidra side (the order), structures.md (the table of sizes becomes the "Ghidra struct status" note); open-questions.md (Creature size). -->

## Group 12: `FireShell`, the projectile factory (1.151 `0x1400307f0`, 1.163 `0x1400300d0`) [code]
Both versions carry logdot's header comment: *"Spawns a projectile based on ammo type index ... Dispatches on `ammo->index` ... Always spawns a muzzle flash body at the end regardless of ammo type."*
`FireGun` calls it (group `FireGun` in `review-1151.md`). 1.163 has one more argument (`param_8`) and `Body` allocations of `0xa40` (1.151: `0xa08`).

* **Dispatch is on `ammo->index`** (the `AmmoDefList` entry; stride `0x168` in 1.151 and `0x188` in 1.163, see group 15; ammo definitions are built in `DefineAmmos`). Cases in **both** versions:
  `5, 10 (0xa), 15 (0xf), 20 (0x14), 25 (0x19), 30 (0x1e), 40 (0x28)` = the plain cannon shells (logdot's comments tag `10` as "57mm; can kill in one volley", `0xf` "180mm high explosive" (by the ammo table in group 13, `0xf` is the **100mm** shell and `0x19` is the 180mm, so that comment is off by one calibre), `0x14` "130mm",
  `0x1e` "203mm normal shell"), `51 (0x33), 52 (0x34), 55 (0x37)` = rockets/missiles (sprite `missile_01`, particles `rocket_glow.psi`/`smoke_FIRE.psi`, sounds `missile_launch`/`missile_launch_far`),
  `60 (0x3c)` = a 3-pellet canister, `70 (0x46)` = a 6-pellet canister, `80 (0x50)` = EMP (`emp_01`). **1.163 adds `54 (0x36)` (another rocket variant) and `90 (0x5a)`** (a heavy shell that also
  changes the firing body's `logic` to `0x89` and sets projectile flags `0x10015`).
* **Where projectile hit points and lifetimes are set (roadmap: "HP modification for missiles, aircraft, rockets and cannon shells"):** rockets get `health = maxHealth = 10.0` and `timeToLive` `10.0` (cases 51/55) or
  `30.0` (cases 52/54) in this function; canister pellets get `health` 30.0 (case 60, explosive 200, TTL 12) or 10.0 (case 70, TTL 30, `explosive` 0); cluster bomblets are in group 5. These are literal constants
  here, so an HP/TTL config means patching these stores (or reading ammo-definition fields if the game exposes them). Cannon shells go through `Body::BulletImpact__` (below) instead.
* **Rocket logic:** the projectile's `logic` field is set to `ammo->caliber` and `isLogicActive = 1` (the missile guidance branch in `creatureLogic` keys on that id), `logicF2 = 1.5` is a guidance parameter, and
  `explosive = ammo->explosivePower`. So rocket speed and acceleration live partly in the ammo definition and partly in that logic branch (not in `FireShell`).
* **1.151 only: the "special behaviour" roll:** for enemy shooters, `behavior = 1.0` is scaled to `0.5` (difficulty 0) or `0.75` (difficulty 1), and each shell gets `field218_0x3b0 = (rand < behavior * p)` with
  `p = 0.5` for most shells, `0.8` for the 57mm and `0.2` for rockets. 1.163 no longer has the difficulty scaling; it computes a time value with `FUN_1401af7b0(n)` (n = 1, 3, 5, 6 or 8 depending on whether the owner is the
  player and on `Profile.field_0x164`) and stores it in the projectile (`+0x3c0`, the "launch timer" field of the Body table). That is the changed AI/difficulty rule; the 1.151 flag `+0x3b0` is gone.
* **Recoil and flash:** `apply_recoil_` applies an opposite impulse to the root body for the canister cases; the muzzle flash is a separate short-lived body (`timeToLive 5.0`, sprites `flash` / `flash_fire`).
* **1.163 extra:** `DAT_147fc6fd4` (the second flag besides `BOOL_147eed9ae` in 1.151) divides the flash size by 1.5, and the first branch (case 5) also calls `Random_Int(1,4)` when `param_8 == 0`.

<!-- MOVE: -> roadmap.md under the "HP modification" and "AI cannot use LG/INC shells / AP only at close range" items (the ammo-index dispatch and the new indices 54 and 90); -> systems.md (new subsection "Firing": FireGun -> FireShell). The ammo-index -> ammo-name map is still missing (look up DefineAmmos / AmmoDefList). -->

## Group 13: the ammo definition table (`DefineAmmos`, 1.151 `0x1402356d0`) [code]
Builds `AmmoDefList` (entry stride `0x168` in 1.151, `0x188` in 1.163 (corrected in group 15; it is not the stats-record size); two undefined entries first, then these). The field `index` is the key `FireShell` (group 12) dispatches on. Base entries; every derived
entry **copies its base (including `index`)** and changes strings and a few numbers, which is why all variants of one calibre share one `FireShell` case.

| `index` | Item | Calibre text | `explosivePower` | `speed` | Extras |
|---|---|---|---|---|---|
| 5 | `ITEM_AMMO_37MM` | 37mm | 0.3 | 1000 | `bulletHeight` 16, `caliber` field 100 |
| 10 | `ITEM_AMMO_57MM` | 57mm | 2.0 | 700 | `bulletHeight` 19 |
| 15 | `ITEM_AMMO_100MM` | 100mm | 14.0 | 700 | `bulletHeight` 24 |
| 20 | `ITEM_AMMO_130MM` | 130mm | 20.0 | 700 | `bulletHeight` 28 |
| 25 | `ITEM_AMMO_180MM` | 180mm | 82.0 | 700 | `bulletHeight` 38 |
| 30 | `ITEM_AMMO_203MM` | 203mm | 118.0 | 700 | `bulletHeight` 38 |
| 40 | `ITEM_AMMO_305MM` | 305mm | 400.0 | 700 | `bulletHeight` 38 |
| 51 | `ITEM_NAR122` | 122mm rocket pod | 45.0 | 150 | `caliber` 130, `gun_rate_time` 0.2, price 50, aircraft strength 3, shop rarity 0.7, amount 100 |
| 52 | `ITEM_AMMO_220MM` | 220mm rocket | 90.0 | 150 | price 0 (not sold) |
| 54 | `ITEM_AMMO_300MM` | 300mm rocket | 90.0 | 150 | price 0; **no `FireShell` case in 1.151** (see below) |
| 55 | `ITEM_NAR340` | 340mm rocket pod | 90.0 | 150 | `gun_rate_time` 0.5, price 100, aircraft strength 5, rarity 0.3, amount 20 |

Derived variants (they copy the base, so same `index`): `_INC` (`incendiaryPower` 1000; 37, 57, 100, 130, 180, 220, 300 mm), `_AP` (`explosivePower` 1.0, `speed` 1500, `apDrag` 0.0007,
`penetrativePower` **16** at 100mm, **20** at 130mm, **34** at 180mm; no 37/57 AP), `_PROXY` (`caliber` 160; 100, 130, 180 mm), `_LG` laser guided (`caliber` 140, `speed` 500, `explosivePower` x4; 130 and 180 mm only).
Bombs: `ITEM_FAB100` (explosive 50, aircraft strength 3), `ITEM_FAB250` (100, 5), `ITEM_FAB500` (200, 8). Aircraft guns: `ITEM_GUN37` (`gun_rate_time` 0.1, `gun_max_load` 10), `ITEM_GUN57`
(0.2, 7); air-to-air `ITEM_K13` (aircraft strength 4). Shop numbers are given per entry (`shopPrice`, `shopRarity`, `shopAmount`), for example 130mm AP price 100 / rarity 0.5 / amount 50, 180mm LG 500 / 0.3 / 10.

* **How this answers parts of the roadmap's tactical-AI item** ("AI cannot use LG/INC shells; AP only at extremely short range"): the *projectile* behaviour of LG, INC, AP and PROXY shells is not in `FireShell`
  (it shares the base calibre's case) but in the `Ammo` fields read by `Body::BulletImpact__`. The AI's *choice* of ammo is elsewhere (loading/selection code such as `loadPrecombatAmmo?` / the AI gun logic), not in
  these files.
* **A 1.151 bug visible here:** `index 54` (`ITEM_AMMO_300MM`) has no case in the 1.151 `FireShell` switch (cases are 51, 52, 55), so it falls into the default branch (only the muzzle flash). The 1.163 switch has a
  case `0x36` (54). That fits "300mm rockets did nothing in 1.151" [guess; the 1.163 index table was not read].
* **Roadmap items served:** "caliber above 30mm should not kill missiles in one shot" and "HP for cannon shells" start from the `Ammo` fields here (`explosivePower`, `penetrativePower`, `apDrag`) plus
  `BulletImpact__`; the `speed` column is the "capped top speed" item for projectiles.

<!-- MOVE: -> content.md or a new short "Ammo" section in systems.md (the table + variants), formats.md (OL.seria `m_launched_*` vs this table are different data: this table is in code, not in OL.seria); roadmap.md (the two notes above). -->

## Group 14: how a cannon shell is set up (`Body::BulletImpact__`, 1.151 `0x140050300`) [code]
Called by `FireShell` for every plain shell (cases 5 to 40) right after `CreateShell_`. Parameters (logdot's names where given): the shell body, the `Ammo` entry, the owner creature, the owner tag, the firing
body, the root body, the fire direction, a speed factor (1.0), `is_local_player`, `flash_power`, **`health`**, `shake_power`, a spread (`param_13`) and the fire power. What it sets:

* **Lifetime:** `timeToLive = desowningTime = 10.0`, but `1.0` if the ammo has `penetrativePower` (AP shells fly for one second), `3.0` for index 10 (57mm) and `2.0` for index 5 (37mm).
  (`FireShell` passes the constants `1.25`/`0.25`/... for size and the mass per calibre; see group 12.)
* **Damage fields copied from the ammo definition (group 13):** `explosive = explosivePower`, `isArmorPiercing` (a float) `= penetrativePower`, `explosiveTemperature = incendiaryPower`,
  `dragLinear = apDrag`, and **`logic = ammo->caliber`** with `isLogicActive = 1`. So `caliber` in the ammo table is not a size but a **projectile logic id** (100 plain shell, 130 rocket, 140 laser guided,
  160 proximity fuze); the per-frame projectile code in `creatureLogic` branches on it. This is why `LG`/`PROXY` variants behave differently although they share the base calibre's `FireShell` case.
* **Launch impulse:** speed `= Random_Float(0.98, 1.2) * ammo->speed * speedFactor`, deflected by a random angle within `+-spread`, applied as an impulse scaled by the shell's mass; if the shooter is the
  local player the opposite impulse is applied to the firing body (recoil).
* **Hit points:** `maxHealth = health = <health parameter>`. Every `FireShell` call passes `1.0`, so **all cannon shells have 1 HP**. That single constant (the 9th/10th argument in each `BulletImpact__` call)
  is the "HP of cannon shells" in the roadmap item; the 300 mm and heavier shells do not get more.
* Effects: screen shake `shake_power` (the last float in each call: 5.0 for 37mm, 10.0 for 57mm, 15.0 for 100mm, 20.0 for 130mm, 30.0 for 180mm, 40.0 for 203mm, 60.0 for 305mm), muzzle `scaleY = gfxFlash * flash_power`, sounds from the ammo
  (`shellOutSound` for the local player at close zoom, `shellFarSound` otherwise). Enemy shooters on some difficulties halve the volume (`0.5`).

<!-- MOVE: -> roadmap.md (HP and damage items: where each constant lives), systems.md "Firing"; the `caliber` = logic-id remark also goes to structures.md (Ammo table). -->

## Group 15: the 1.163 ammo table and what changed from 1.151 (`DefineAmmos`, 1.163 `0x140256f10`) [code]
The 1.163 counterpart exists and is named `DefineAmmos` (`0x140256f10`-`0x14025afc4`; it builds 35 entries into `AmmoDefList`/`AMMO_LIST_BEGIN` at `0x143a13be0`). It was found through the data: the global's xrefs
(168) include the writers inside this function, and `FireShell` indexes the same global. Source: the 1.163 decompile of `DefineAmmos`, `CreateUndefAmmo?` (`0x140289190`) / `UndefAmmo` (`0x140292e50`) and
`Body::BulletImpact__` (`0x140052a80`), against the 1.151 versions (group 13/14). Offsets are bytes into the `Ammo` record.

**Record layout.** 1.151 `Ammo` is `0x168` (360) bytes; 1.163 is `0x188` (392). The extra `0x20` comes from two inserts: a string `shell_enemy` (an "enemy fire" sound, `+0x110`, so the sound strings are `shell_in`,
`shell_out`, `shell_enemy`, `shell_far`) and a float **`ttl`** (`+0x16c`). Everything from `ttl` on moved by `+0x24` (1.151 `shopPrice` `0x14c` -> 1.163 `0x170`; `gun_rate_time` -> `fire_delay` at `0x17c`;
`gun_max_load` at `0x180`; `aircraftStrengthContribution` at `0x184`). Earlier in this file I wrote `0x188` for the 1.151 stride (group 12/13); that was wrong, it is the 1.163 size, and the 1.151 size is `0x168`.
Defaults (`UndefAmmo`): `incendiary_power` 100.0 (both versions), **`ttl` 10.0 (1.163 only)**, `fire_delay` (1.151 `gun_rate_time`) 0.5, `gun_max_load` 10.

**Careful: `+0x16c` means different things in two structs.** In the stats record it is `cluster` (group 6); in the `Ammo` record it is `ttl`. A Ghidra struct edit or an offset search will hit both.

**What 1.163 does with `ttl` (the main finding).** `BulletImpact__` now sets the shell's `timeToLive` / `desowningTime` from `ammo->ttl` (1.151 `BulletImpact__`, `0x140050300`, re-read: literal 10.0, `penetrativePower != 0` gives 1.0, `index == 10` gives 3.0, `index == 5` gives 2.0). Armor-piercing
shells (`penetrative_power != 0`) still fly 1.0. The values stored in `DefineAmmos`:

| Shell | 1.151 lifetime (s) | 1.163 `ttl` (s) |
|---|---|---|
| 37mm | 2.0 | 2.0 |
| 57mm (and the new `ITEM_AMMO_57MM_TANK`) | 3.0 | 3.0 |
| 100mm | 10.0 | **4.0** |
| 130mm | 10.0 | **7.0** |
| 180mm | 10.0 | **30.0** |
| 203mm, 305mm | 10.0 | 10.0 (default) |
| AP variants (100/130/180) | 1.0 | 1.0 |

Shell range is lifetime x muzzle speed (`speed` 700 for the base shells), so this changes effective range: a 100mm shell now lives 4 s, a 180mm shell 30 s. **This is a real gameplay difference between the versions
and the first hard evidence for the roadmap's "damage changes" scope**; both are data in `DefineAmmos`, so they are patchable constants. [code]; whether it is felt in play is untested [guess].

**Other value changes between the versions** (from the two `DefineAmmos` decompiles, `[code]`):
* `ITEM_AMMO_220MM` `explosive_power` **90 -> 180**; `ITEM_AMMO_300MM` **90 -> 500**, and its `caliber` (projectile logic id) 130 -> **132** (`0x84`). `ITEM_NAR122` (45) and `ITEM_NAR340` (90) are unchanged.
* Incendiary variants: `incendiary_power` **1000 -> 300** (every `_INC` entry).
* Laser-guided variants: `explosive_power` multiplier **x4 -> x1.5** (`ITEM_AMMO_130MM_LG`, `ITEM_AMMO_180MM_LG`).
* `ITEM_FAB250`: `aircraftStrengthContribution` 5 -> **6** and shop price 100 -> **200** (FAB100 and FAB500 unchanged). `ITEM_K13` (air-to-air missile): shop price 300 -> **400**.
* `ITEM_GUN37`: `fire_delay` 0.1 -> **0.05** and `gun_max_load` 10 -> **20** (GUN57 unchanged at 0.2 / 7).
* Unchanged (compared by hand, every numeric store in both decompiles, not by script): the base cannon `explosive_power` / `speed` / `bullet_height` (37mm .. 305mm), the AP penetrations 16 / 20 / 34 and `apDrag`, the rocket speeds and pod stats, and the shop price / rarity / amount of every other entry (including `ITEM_K13`'s rarity and amount, the FAB250 rarity and amount). Sound and sprite strings were **not** compared.
* **New entries:** `ITEM_HARPOON` (`index` 90 = `0x5a`, `caliber` 135 = `0x87`, `speed` 700, `explosive_power` 0), `ITEM_KAZ_AMMO` (`index` 100, no `FireShell` case; the KAZ burst is `FUN_14002f480`),
  and `ITEM_AMMO_57MM_TANK` (`index` 10, `caliber` 0 = no projectile logic, 57mm numbers).

**Resolves two earlier guesses.** (1) `FireShell` case `0x5a` (90), which I called "a heavy shell that changes the firing body's logic to 0x89", is the **harpoon** (`index` 90). (2) The 300mm rocket (`index` 54) had
no `FireShell` case in 1.151; 1.163 adds case `0x36` and raises the warhead from 90 to 500, which fits "the 300mm rocket was unfinished in 1.151". The 1.151 half is `[code]`; the "it did nothing in play" half is still a guess.
Case `0x37` (55, `ITEM_NAR340`) and `0x33`/`0x34` (51/52) are as before.

**Index map for 1.163** (the dispatch key of `FireShell`): 5 37mm, 10 57mm, 15 100mm, 20 130mm, 25 180mm, 30 203mm, 40 305mm, 51 NAR122, 52 220mm rocket, 54 300mm rocket, 55 NAR340, 90 harpoon, 100 KAZ.
Variants (`_INC`, `_AP`, `_PROXY`, `_LG`) copy their base and keep its `index`. The `FireShell` cases 60 (`0x3c`) and 70 (`0x46`) (canisters) and 80 (`0x50`, EMP) have no `DefineAmmos` entry in either version: they come from
code that fills other ammo (not read).

<!-- MOVE: -> systems.md "Firing" / a new "Ammo" section (the table, the ttl change); roadmap.md item "HP modification for ... cannon shells" and the damage-changes note; the roadmap item "Adjustable TTL for cluster munitions and mine bomblets" is a different mechanism (the bomblet spawner argument, group 5), not this field in "Version scope" (ttl is per ammo type in 1.163, a data constant); structures.md (Ammo record 0x168 vs 0x188). The 1.151 vs 1.163 value-change list is the evidence for "damage changes"; keep it in roadmap.md version scope. -->

## Group 16: where the tactical AI fires and picks ammo (1.163 `FUN_14007a8d0`, 1.151 `0x140076300`) [code unless noted]
Found by following the combat launch chain upward, not by name: `FireShell` <- `FireGun` <- `FireGuns` (`0x1400559e0`, a loop over one gun) <- **`FUN_14007a8d0`** (1.163, `0x14007a8d0`-`0x14007bfb1`). It is the
per-ship **AI weapon controller**: it aims every gun on an AI creature, picks the ammo, and decides whether to fire. The 1.151 twin is `rep_140076300_API-MS-WIN-CRT-MATH-L1-1-0.DLL::atan2f` at `0x140076300`
(a propagated name that has nothing to do with `atan2f`; flag for logdot). The 1.163 version is called from `FUN_140062f90` (the big ship update, not read) and from a function labelled `shipKill?`; I did not check the 1.151 callers.

**Premise check on `creatureLogic`.** `creatureLogic` (1.151 `0x1400335b0`, 1.163 `0x140033b90`) is not the ship AI. `FireShell`/`FireGun` call it, its callees are the missile/cluster/evac-pod functions, and
`BulletImpact__` stores `ammo->caliber` into the projectile's `logic` field (group 14). It is the **per-body behaviour dispatcher for projectiles, missiles and aircraft**, keyed by that logic id (100 plain shell, 130
rockets, 140 laser guided, 160 proximity, and in 1.163 132 for the 300mm rocket and 135 for the harpoon). The roadmap's tactical-AI items are therefore in the function above and its caller, not in `creatureLogic`.
I did not read `creatureLogic` itself (it timed out twice); this is inferred from callers/callees and the field it keys on [code, indirect].

**Answers to the roadmap's tactical items:**
* **"Closing to very short range disables all weapons" [Tactical, exploitable]: found, and new in 1.163.** After the target's position is read, 1.163 returns before any aiming or `FireGuns` when
  `distance < target.+0x1850 + self.+0x1850 + 30.0` (`+0x1850` is the ship's **bounding radius**, see group 17). 1.151's version of this function has no such test (I did not compare the callers). So the "all guns go silent when you
  are touching them" behaviour is, as far as this function goes, a 1.163 addition, and a patch is a change to that compare or to the constant `30.0` in this function (pinned in group 17: `0x14007b021` / `0x14007b02d`).
* **"AP only at extremely short range": confirmed, same rule in both versions.** For guns whose part caliber index is 15, 20, 25 or 30 (100, 130, 180, 203mm) the controller sets the gun's ammo slot
  (1.163 gun `+0x850`, 1.151 `+0x83c`) with `FindAmmoIndex(name)`. It picks `_AP` only if two creature flags are set **and the target is closer than 1000** units; else the proximity variant when other flags are set; else the plain shell.
  It **never selects `_INC` or `_LG`**, which matches the roadmap ("the AI cannot use LG/INC shells"). The 37mm, 57mm and rocket guns keep whatever they were loaded with.
* **A latent bug in both versions:** for caliber index 30 it looks up `ITEM_AMMO_230MM` (and `_PROXY`, `_AP`), but the table (group 13/15) has `ITEM_AMMO_203MM`. `FindAmmoIndex` returns 0 on a miss, which is the undefined
  entry whose `index` is 0, a `FireShell` default (muzzle flash only, no shell). **It does not bite in vanilla**: in the game's `OL.seria` no part has `m_weapon_caliber=30` [game]. It would bite a mod that adds a 203mm gun.
* **"Gives way to the player", "cannot deploy flares", "high convergence angles disable turrets": not in this function.** No movement code and no flare code here. The convergence item may relate to the new aim test below, but I have not shown that [guess].

**Other differences from 1.151 in this controller:**
* **Aim tolerance (1.163):** a gun fires only if its turret is within **0.025 rad** (about 1.4 degrees) of the aim angle; I see no such test in the 1.151 version of this function. [code; effect untested]
* **Range for firing at special targets (the missile/aircraft target branch):** strategic-launch targets (part flag `0x8000000`, the A-100 class): 1.151 unlimited range (`3.4e38`), 1.163 **3500**. Aircraft (`0x400`): 1.151 2x the
  gun range, 1.163 at least **3000** (the larger of 2x range and 3000). Tactical missiles (`0x4000`): 0.75x range in both. A creature flag (`damageCounter_` in 1.151, `linkDLL` in 1.163, the labels are wrong) caps the range at 700 in both.
* **Small guns (part caliber index <= 10) are limited to 1500** when a global flag is set (both versions).
* **Proximity-ammo rule** was restructured (1.151: both flags needed; 1.163: `c76+7` and (`c6e+7` or `c76`)); I could not tell what the flags mean.

**[game] cross-check from the game's `OL.seria` (vanilla 1.163):** `m_weapon_caliber` is the ammo `index`: `MDL_CANNON_30_6` = 5, `MDL_CANNON_57_2` = 10, `MDL_CANNON_100_2` = 15, `MDL_CANNON_130` / `_LOW` = 20,
`MDL_CANNON_180` / `_180_2` = 25, `MDL_RSZO_220` = 52, `MDL_TORPEDO_300` = 54, `MDL_CANNON_HARPOON` = 90, `MDL_KAZ` = 100. Notably **`MDL_CANNON_305_2` also uses 25 (180mm shells)**, so `ITEM_AMMO_305MM` (index 40) and
`ITEM_AMMO_203MM` (30) have no vanilla gun. This ties the stats record's `+0x144` (`caliber`) to the ammo table.

**Not found / still open:** the ship update that calls this controller (movement, "gives way"), flare logic, the meaning of the creature flags at `+0xc06..+0xc77` that choose AP/proximity, and the exact patch address for the 30.0 test.

<!-- MOVE: -> systems.md new "Tactical AI weapons" subsection (the controller, ammo choice rule, close-range cutoff, aim tolerance); roadmap.md AI items "Tactical, exploitable: closing to very short range" (found), "AI cannot use LG/INC; AP at very short range" (found), and a note for the Version scope (the range and cutoff changes are 1.163 gameplay differences); structures.md (Creature fields +0x1850, +0x850 gun ammo slot); open-questions.md (flares, give-way, flag meaning). -->

## Group 17: the per-ship AI tick (1.163 `FUN_140062f90`) and the close-range cutoff patch site [code unless noted]
Read in full (all 1587 decompiled lines). `FUN_140062f90` (`0x140062f90`-`0x140065f99`) has one caller, `0x1400739c0`, which Ghidra labels `shipKill?` (a wrong label: it calls this once per ship, so it is the
per-ship AI tick). The function does the movement steering, launches aircraft and missiles from the ship, and calls the weapon controller of group 16 (`FUN_14007a8d0`) when the ship has a target. 1.151 was not compared here.

**Pinned: the close-range cutoff (group 16) is in `FUN_14007a8d0`, bytes at `0x14007b011`-`0x14007b033`:**

| Address | Bytes | Instruction |
|---|---|---|
| `0x14007b011` | `f3 0f 10 83 50 18 00 00` | `MOVSS XMM0,[RBX+0x1850]` (target radius) |
| `0x14007b019` | `f3 0f 58 87 50 18 00 00` | `ADDSS XMM0,[RDI+0x1850]` (own radius) |
| `0x14007b021` | `f3 0f 58 05 b3 74 2d 00` | `ADDSS XMM0,[rip+0x2d74b3]` -> the float `30.0` at `0x1403524dc` |
| `0x14007b029` | `41 0f 2f c6` | `COMISS XMM0,XMM14` (XMM14 = distance between the two ships) |
| `0x14007b02d` | `0f 87 0c 0f 00 00` | `JA 0x14007bf3f` (the function's return: no aiming, no `FireGuns`) |

The guard is `radius(target) + radius(self) + 30.0 > distance -> return`. **Do not patch the constant at `0x1403524dc`**: it is a pooled `30.0f` with about 60 other references (`hooks.md` rule). The two clean options:
* **Make the margin adjustable (operand repoint, the `hooks.md` technique):** change the disp32 at `0x14007b025` (bytes `b3 74 2d 00`) so the `ADDSS` reads a private float in the mod's memory (allocate within +-2 GB of the image). The mod's setting is that float; `30.0` is vanilla.
* **Disable the cutoff:** set that private float to a large negative value (`-1e9`); the sum then never exceeds the distance. (Alternative: overwrite the six `JA` bytes with a 6-byte nop; the operand route keeps the knob adjustable.)
Version guard: compare the 40 bytes from `0x14007b011` to `0x14007b039` before patching. The function is not owned by any mod in `hooks.md`. **The effect is untested in game**; the margin only matters when two ships are nearly touching.

**`Creature +0x1850` is the ship's bounding radius [code]:** written in `CalculateStats` (`0x14007ffaa`, the only writer) from `0x140071120`, which takes the maximum over the ship's root parts of
(distance from the centre at `+0x1840` + that part's own radius at Body `+0x20c`). `+0x1840/+0x1844` is the centre of mass computed just above it.

**How the AI steers (movement), as read:**
* **Stand-off distance:** `0.35 x` the larger of two weapon-reach floats (`+0x1838`, `+0x183c`), capped at **1000** (660 if the flag at `+0xc74` is set). The ship tries to hover at that range from its target; the heading is
  a sum of weighted unit vectors: toward/away from the target by `clamp((distance - standoff)/600, -1, 1)`, a perpendicular **orbit** term with weight `1 - |that|` (so it circles at the stand-off range), **separation from other ships**, cohesion toward the
  average position of the ship's group (weight `clamp(distance/250 - 1, 0, 3)`), pull toward a waypoint (`clamp(distance/300 - 1, 0, 3)`), and push away from the map edges.
* **Separation is between allies.** `FUN_140220170(a, b)` is just `a == b`; the tick calls it on the two side floats at `+0xad4` truncated to int, so "ally" means "same integer side". For allies the push is
  `min(1, 200/(d+1))` (500 with a mode flag), scaled by 1 (or 100 when `BOOL_147fc6fdb` is set). **Non-allies, which includes the player, are pushed away only when two conditions hold** (the ship has reach >= 6000 or a related
  flag, and `DAT_147fc6fe0` is set); otherwise the loop ignores them. I could not resolve what `DAT_147fc6fe0` and `BOOL_147fc6fdb` mean (mode flags). *(Correction: an earlier version of this note said the AI avoids the player
  with the same push it uses between its own ships. That was wrong for the default case.)*
* **What this says about "the AI consistently gives way to the player":** the more likely mechanism is the **stand-off term**, not separation. The radial weight is `clamp((distance - standoff)/600, -1, 1)` toward the
  target, so when the player closes to inside the stand-off range the weight goes negative and the AI **backs away**, reaching full retreat 600 units inside it (the stand-off is `0.35 x reach`, at most 1000, so
  a 2000-reach ship starts backing off at 700). Nothing steers the player, so the AI always yields. [code for the term; that it explains the play behaviour is a guess, untested]. The knob is the `0.35` factor and the `600` clamp width; their addresses are not pinned yet.
* **Launching from the ship** (end of the function): if the ship has a target creature it can launch aircraft (`FUN_14002ff60`) when the target is between `radius(target) + radius(self) + 100` and `2000` away, on a random roll
  (about 1% per tick plus a term in the launch counts), with a 2.0 s ship-level cooldown (`+0xd60`) and a 6.0 s timer (`+0xcb8`). Missiles are launched through `FUN_14002e3a0` (the combat launch of the multicharge mod, `hooks.md`)
  from the ship's second launch list (`+0x13f0`). If the target is a strategic launch (`0x8000000`) or an aircraft (`0x400`), the ship fires at it with a per-ship cap of **3 launches (strategic missile) or 1 (aircraft)** (counter at `+0xc98`), 0.5 s apart
  (`+0xd64`). [code; I did not find where the counter resets.]
* **Flares: not found.** Nothing in this function or in the weapon controller references category bit 23 or a flare part. Whether `FUN_14002e3a0` can fire flares from the launch lists is not shown.

**`FUN_14002e3a0(launcher, target)`, the launch function [code]:** refuses if the launcher's cooldown float (`+0x848`) is non-zero, it has no owner (`+0xb8`) or no target. It writes the target link into the launcher
(`+0x490`), the owner link (`+0x4a8`) and sets the logic-active flag `+0x3c8` (the same fields as the combat-launch notes). For launchers whose **owner side is negative and non-zero (the AI side, since the difficulty flag below only applies there)** it adds limits:
* at most **1 launch per second at the same target** (the target's `+0x8b0` holds the time of the last launch at it);
* at most **10** missiles in flight at one target, **2 if the target is a tactical missile (`0x4000`), 1 if it is an aircraft (`0x400`)**, minus those already tracking it (a list of in-flight launches, compared at `+0x498`);
  strategic-launch targets (`0x8000000`) fall under the default 10 (the result of that test is discarded);
* the launcher's next-launch timer (`+0x3c0`) is set from `FUN_1401af7b0(8)`, or `(6)` when the Profile byte `+0x164` is set (the same difficulty byte as group 12).
Launchers on the positive side (the player's) skip all three limits. These limits are what the roadmap's "AI has no evasive manoeuvring / cruise missile barrage" items run into on the tactical map; they are constants in this function.
The function needs a target, and nothing in the AI tick calls anything without one, so **by construction the AI tick has no trigger for flares** (flares are not aimed at anything). That is an inference, not a search for flare parts. [code, inference]
`FUN_14020fce0(a, b)` is the plain distance between two creature centres (`+0x1840/+0x1844`), 999999 if either is null. Side convention (from the difficulty check): negative = AI, positive = player, 0 = neutral [guess from the difficulty byte].

**Still not read:** where the per-ship launch counter at `+0xc98` resets, what is in the ship's launch list at `+0x13f0`, and the meaning of the two mode flags.

**Pinned: the stand-off knobs in `FUN_140062f90` [code; untested].** All three constants are pooled and shared, so patch the instruction's operand (repoint) and never the constant (`hooks.md` rule):

| Knob | Instruction (address, bytes) | Constant | Other users of the constant |
|---|---|---|---|
| stand-off = `0.35` x reach | `0x1400631a6` `f3 0f 59 1d 0e 15 2f 00` and `0x1400631ec` `f3 0f 59 1d c8 14 2f 00` (`MULSS XMM3,[rip+d]`; two paths, with and without a ship target) | `0.35f` at `0x1403546bc` | 6 (`SomethingWithLevelSerias` x4, `FUN_14012f120`, one more) |
| stand-off cap 1000 | `0x14006320d` `f3 0f 10 35 2f f6 2e 00` (`MOVSS XMM6,[rip+d]`, then `MINSS XMM3,XMM6` at `0x14006321e`) | `1000.0f` at `0x140352844` | many (also the AP range threshold of group 16) |
| stand-off cap 660 when the `+0xc74` flag is set | `0x1400631fe` `f3 0f 5d 1d ce 33 2f 00` (`MINSS XMM3,[rip+d]`) | `660.0f` at `0x1403565d4` | not checked |
| radial weight width 600 | `0x140064723` `f3 0f 5e 05 11 e1 2e 00` (`DIVSS XMM0,[rip+d]`; `XMM0` = distance - stand-off, then clamped to +-1 against the pooled `1.0f` loaded at `0x14006471b`) | `600.0f` at `0x14035283c` | about 24 |

Recipes (all by operand repoint to a private float, with a 40-byte-or-so version guard around each site): a **smaller `0.35`** makes the AI hold a shorter range (it closes in); a **larger `600`** flattens the radial term so the AI retreats more
gently when the player gets inside its stand-off; a very large `600` means it almost never backs away. Not owned in `hooks.md`. The orbit and separation terms are unchanged by these.

<!-- MOVE: -> hooks.md (new rows in the Ownership table for 0x14007b021 / 0x14007b025 "close-range margin" and for the stand-off knobs 0x1400631a6, 0x1400631ec, 0x14006320d, 0x1400631fe, 0x140064723, all unowned, operand repoints) and roadmap.md AI items "closing to very short range" (found, with the patch recipe) and "AI gives way to the player" (candidate cause: no special case, symmetric separation); systems.md "Tactical AI" subsection (stand-off 0.35 x reach, orbit, separation, launch caps); structures.md Creature fields: +0x1840 centre, +0x1850 bounding radius, +0xad4 side float, +0x13d8/+0x13f0 launch lists, +0xd60/+0xd64 launch cooldowns, +0xc98 launch counter; systems.md "Launching" (the per-target launch limits of FUN_14002e3a0, which also belongs next to the multicharge owner row in hooks.md); open-questions.md (flares, mode flags). -->

## Group 18: the 1.163 endgame function and a probable cause of the Khiva crash [code; not reproduced in game]
**Located:** the 1.163 counterpart of `spawnEndgameShips_` is `FUN_140261a20` (`0x140261a20`-`0x140263534`, unnamed). Found via the strings `NUCLEAR_WAR` and `dram_hit_01` (its only code reference besides one other
function), then confirmed by an almost identical callee set and the same body (`KHIVA`, `BASRA`, the 100-try search, `Tarantul`/`Tarantul ARM`, `THE_BEGINNING`). Its one caller is at `0x1402b8af2`, in a region of the
level-script (`SCR_MAP`) handler where **no function is defined** (the same Ghidra gap as `0x140117840`). The call is preceded by a gate on three profile/global flags (bytes at `0x1402b8a27`-`0x1402b8a47`):
profile `+0x2ec` non-zero, profile `+0x2e9` zero, and the global byte `0x147fc6fca` zero. These are the 1.163 positions of `escalation` and `endWar` (the Ghidra `Profile` struct is the stale 1.151 layout, shifted `+0x58`: `endRace` `0x2e8`, `endWar` `0x2e9`,
`escalation` `0x2ec`); that reading of the gate is unverified, and it sits oddly with the function's own "if `escalation == 0`" branch (below), so do not rely on it.

**The probable cause of "capture all cities around Khiva and the game crashes / loops on load":** the function builds four circular lists (quadrants around Khiva) of eligible cities, sorts them, then writes `city.+0x19c = 2` to
**the first element of each list with no emptiness check**:

| 1.163 `0x140262226`-`0x140262279` (84 bytes, four blocks of 21) | meaning |
|---|---|
| `mov rax,[rbp-8]` / `mov rax,[rax]` / `mov rax,[rax+0x10]` / `mov dword [rax+0x19c],2` | list 1 head -> first node -> payload (the city) -> state = 2 |
| same with `[rbp-0x18]`, `[rbp-0x28]`, `[rbp-0x38]` | lists 2, 3, 4 |

(1.151: the same four writes at `0x140240266`; the decompile shows them straight after the four sorts, unguarded.) An empty list is a lone sentinel node from `New(0x18)` (a plain `operator new`, no zeroing; only its two link
fields are set), so `first = sentinel` and `[sentinel+0x10]` is whatever the heap held: typically a stale pointer or zero, then `+0x19c` is written through it. That is a wild write: a crash if the pointer is bad, silent heap
corruption if it is not. **A list is empty when no city in that quadrant passes the filter** (city state `+0x19c != 0`, and no friendly-side fleet within 700 of it); capturing every city in one quadrant around Khiva fits. If the
function runs on load of such a save, the game would crash each time, which would look like a loop. [code for the unguarded writes and the empty-list case; "captured cities have state 0" and the load-time repeat are guesses, untested]
The roadmap names 1.163, but the same code is in 1.151, so 1.151 should have it too [guess, not run].

**Patch recipe (not applied, untested):** a function-entry-style detour at `0x140262226` over those 84 bytes (the `hooks.md` technique; a 14-byte jump into a stub that returns to `0x14026227a`): for each of the four lists
(pointers at `[rbp-0x8]`, `[rbp-0x18]`, `[rbp-0x28]`, `[rbp-0x38]`), do `first = *list; if (first != list && first[2] != 0) first[2]->+0x19c = 2`. Version guard: compare those 84 bytes before patching. The rest of the function already
handles empty lists (the later loops are guarded), so nothing else should need to change. What the game should do when a quadrant is empty is a design question; the guard just stops the wild write.

**Other differences from 1.151 in this function:** the phase structure, the `100.0/200.0/300.0` strike strengths (`hardMode`), the `2000`-`4000` search ring, the `700` exclusion and the `Tarantul` split (66%) are unchanged. 1.163 adds
`CopyEscadraName` calls with a state flag set through bit marks (`local_234 |= 1/2/4`, unused locals as far as I can tell) and uses the escalation/`enigmaKey10` pair as the stale Ghidra struct shows them (offset 660 is `escalation`, 744
`enigmaKey10` is a mislabel: at the shifted layout it lines up with 1.151 `escalation`/`endWar`); I did not resolve these two names.

<!-- MOVE: -> roadmap.md under the "Capturing all cities around Khiva" bug (the cause and patch recipe, with the [guess] tags kept); -> systems.md "End game" section (three phases, the four-list write, endWar/escalation, Profile offsets +0x58 in 1.163); -> hooks.md Ownership table (candidate site 0x140262226, unowned); -> open-questions.md (the 3-flag gate in the SCR_MAP handler, the two profile names). Do NOT move before logdot confirms the stale-struct reading of the Profile offsets. -->

## Group 19: how a ship combines its parts' sensors, and the `+0xd4` question [code; not run]
Read in the 1.163 ship stats recompute (inside `rep_14006db30_GetValue`, Ghidra name wrong; the stats loop around `0x140072200`-`0x140072614`) and its helper `FUN_140061260`.

**The helper `FUN_140061260(ship, ship_array, part_array, scale, angle_a, angle_b, ...)`** merges one part's 360-entry sector array (`Body +0x508`, `m_sectors`) into one of the ship's 360-entry arrays, over an angle range (and an optional second range).
The last argument (a stack byte) selects the combine rule: **0 = per-sector maximum, non-zero = per-sector sum**.

**Which sensors use which rule (read from the call sites):**

| Stats field | Sensor | Ship arrays (two per type, `+0x78` apart) | Rule |
|---|---|---|---|
| `+0x10c` | radar | `+0x16b0`, `+0x1728` | **max** |
| `+0x110` | tracking | `+0x16c8`, `+0x1740` | **max** |
| `+0x114` | guiding | an integer count added at `+0x17b0` (no array) | n/a |
| `+0x118` | ELINT | `+0x16e0`, `+0x1758` | **max** |
| `+0x11c` | IRST | `+0x16f8`, (`+0x1770` inferred, not read) | **max** |
| `+0x120` | jammer | `+0x1710`, `+0x1788` | **sum** (the only one) |

Each sensor type has its **own** arrays, so different types are never mixed here. The second array of each pair uses a different scale when the part's `+0x888` is non-zero (meaning unknown). The values returned by the helper are stored at `+0x17a0`-`+0x17c8`;
the helper decompiles as `void`, so those stores may hold leftovers; I did not use them.

**Does the roadmap's "sensor range is accumulative with two or more sensor types" hold up?** Not in this stage. Radar, tracking, ELINT and IRST each combine their parts by **maximum, per sector, per type**, so two radars do not add up and different types do not add. The only summing rule is for **jammers**
(two jammers add), which looks deliberate. The fleet level also takes a **maximum** (the detection range at fleet `+0x4f0` is a `MAXSS` over ships, `0x14011b73d`). So if the in-game accumulation is real, it is either (a) in a later stage that turns these arrays into an effective range (not read), (b) the jammer
rule being what the reporter saw, or (c) a UI/readout effect. **Status: the claim is not confirmed by this code, and not refuted.** A test would be two radars on one ship, then one, in the ship's range readout.

**Resolves part of the `+0xd4` flag (flag 11 / group 6).** In the same loop: stats `+0xd4` is added into ship `+0x17f0`, the part's `Body +0x804` into ship `+0x17ec`, and stats `+0xd8` (crew need) into `+0x17f4`; all three are 32-bit integer sums.
Ship fuel is stored as doubles (`+0x1638`/`+0x1640`), so integer sums next to crew need are far more consistent with **`+0xd4` = crew capacity and `Body +0x804` = crew currently in the part** than with fuel. That matches logdot's 1.151 names (`mdl_crew_capacity` `0xd4`, `mdl_crew_need` `0xd8`, `mdl_fuel_capacity` a double at `+0xc8`).
Cross-check in the game's `OL.seria` [game]: `m_mdl_crew_capacity` exists on `MDL_COMBRIDGE_01` (60), `MDL_QUARTERS_01` (50), `MDL_QUARTERS_02` (25), and `m_mdl_fuel_capacity` on `MDL_FUEL_01/02/03` (40000, 450000, 80000), as separate keys, so the stats record has both. Which key sits at which offset still comes only from the 1.151 names plus the aggregation above, not from a direct read of
the loader. **Suggested correction to `structures.md` (do not apply yet): `+0xd4` crew capacity (int), `+0xc8` fuel capacity (double), `Body +0x804` crew present.**
It also bears on the roadmap's "functional crew-requirement system": the totals (`+0x17ec` present, `+0x17f0` capacity, `+0x17f4` needed) already exist per ship; what consumes them was not looked for.

<!-- MOVE: -> structures.md Stats record (the +0xd4 / +0xc8 correction, with the evidence above) and Body table (+0x804); -> roadmap.md "combined sensors" item (status: not confirmed; where to look next) and "crew requirement" item (the three per-ship totals); -> systems.md (sensor combine rules, max vs sum). -->

