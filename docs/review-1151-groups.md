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
