# 1.151 vs 1.163: what moved, what was added (reference)

Source: a read-only comparison of logdot's annotated 1.151 Ghidra program with the 1.163 program, plus targeted decompilation. Neither program was edited. Tags as in `../README.md`: **[V]** 1.163 offset also verified in `structures.md` (game or code) · **[C]** 1.163 offset read from the copy routine and paired by role · **[?]** uncertain · **[tool]** fuzzy-match result · **[code]**, **[guess]**, **[game]** as in the README.
Porting a mod? Start with the guide: [porting-1151-1163.md](porting-1151-1163.md). Use this reference when a 1.151 name, offset or comment has to be carried to 1.163, or to see which differences are gameplay changes.

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

## 1.151 names that confirm what the 1.163 notes say
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

## Body remap, 1.151 to 1.163
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
| `0x828`, `0x82c` | **+0x10** | pump pair [C] |
| about `0x834` .. `0x868` (weapon/ammo area) | **+0xc for the saved weapon keys (`0x840`..`0x84c`), +0x14 for the `FireGun` runtime fields** | resolved with `FireGun` and the save keys (below): the zone is not one shift |
| `0x86a` .. `0x87c` (rescue flags, `isCrtScreen`, `repairType`) | about 0 [?] | bool cluster is repacked; see "unresolved" |
| about `0x980` .. `0xa30` (floor, edRotate, aircraft logic) | **+0x30** | `floorType`, `floor`, `edRotate`, aircraft logic pointer |
| tail flags (`isFocusable` ...) | **+0x30 or +0x38** [?] | the copy routine writes bytes at 0xa38..0xa3d; the 1.151 flags are at 0x9fc..0xa0d, so this end zone is unresolved |

**Total size (corrected):** the *real* 1.151 Body is **0xa08** bytes (`New(0xa08)` in 1.151 `Projectile_ExplodeAndCluster`; the Ghidra 1.151 struct says 0xa10, 8 bytes too big), and the real 1.163 Body
is **0xa40** (`New(0xa40)`), so the object grew by **0x38**. That also explains the stale 1.163 Ghidra struct: it is 2,568 = **0xa08 bytes, i.e. the 1.151 layout**, copied over and never resized.
The shift therefore climbs through the zones (0, +4, +0x10, +0x14, then +0x30 at the floor fields, and +0x38 at the end: aircraft logic pointer `0x9e8 -> 0xa20`).

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
| `m_mdl_pump`, `field_0x82c` | 0x828, 0x82c | 0x838, 0x83c | +0x10 | [C] copy-order pairing |
| `mdl_turbine` | 0x834 | **0x848** | **+0x14** | [C]; **0x848 is the field `UpdateEngineCovered` writes and the missile launch tests** (see below) |
| `field_0x838` | 0x838 | 0x84c | +0x14 | [C] |
| value `FireGun` passes to `FireShell` (1.151 name `mdl_covered`, a mislabel) | 0x83c | **0x850** | +0x14 by role | [C] FireGun in both versions; **0x850 is the saved key `m_weapon_ammo`**, the ammo index `FireShell` dispatches on [V, save-key string in `bodySecondaryInit`] |
| `weaponType`, `ammoIndex`, `weaponAmmoExtra` | 0x840, 0x844, 0x848 | **0x84c, 0x850, 0x854** | **+0xc** | [V] save keys `m_weapon_type`, `m_weapon_ammo`, `m_weapon_ammo_extra` in `bodySecondaryInit` (an earlier copy-order pairing at +0x14 was wrong) |
| `weaponAmmoAmount` | 0x84c | **0x858** (saved reserve, key `m_weapon_ammo_amount`, +0xc); `FireGun` decrements a separate runtime counter at **0x860** | +0xc / +0x14 | [V] key; in 1.151 `FireGun` decrements `weaponAmmoAmount` itself, in 1.163 the saved amount is the reserve and `0x860` is the loaded count (see below). Also key `m_weapon_ammo_extra_amount` at **0x85c** |
| cooldown float set to `1/(rate/60)` (`field_0x858`) | 0x858 | **0x86c** | +0x14 | [C] FireGun in both versions |
| float that blocks firing when > 0 (`field_0x85c`) | 0x85c | **0x870** | +0x14 | [C] FireGun in both versions |
| byte written 1 on entry (named `fFireRateTimer` in 1.151) | 0x860 | **0x874** | +0x14 | [C] FireGun in both versions |
| `floorType`, `floor` | 0x980, 0x988 | 0x9b0, 0x9b8 | +0x30 | [V] (`m_floor_type`, `m_floor`) |
| `lightColorR..A`, `lightFade`, `ambient` | 0x9c8.. | 0x9fc..? | +0x30 | [?] by zone |
| `edRotate` | 0x9f8 | 0xa28 | +0x30 | [V] (`m_ed_rotate` 0xa28) |
| `aircraftLogic` pointer | 0x9f0 (and 0x9e8) | 0xa20 | +0x30 | [C] |
| `helpInex` / flags (`isFocusable`...) | 0x9fc.. | 0xa34..0xa3d | +0x38 / +0x30 | [C] copy routine bytes at 0xa38..0xa3d |


### What this tells us
* **Mostly mechanical for the fields I could anchor.** Most named fields I checked fall in the +0 / +0x10 / +0x30 zones and can be mapped by adding a constant per zone . Only the weapon/ammo area
  (`0x828..0x880` in 1.151) and the `aircraftLogic`/lighting tail need individual attention.
* **The notes' offsets are self-consistent with this table** at every anchor I could cross-check (health, count/blueprint, logic, sectors, floor, edRotate, covered, weapon ammo): good
  evidence that `structures.md` is right for 1.163 and that the stale part is the Ghidra struct, not the notes.
* **Resolved 2026-10-14 (blind re-derivation, two agents): Body `+0x7f8` is the part's current fuel (double, key `m_mdl_fuel`), `+0x800` is `m_mdl_fss` (float), `+0x804` is `m_mdl_crew` (int).** The ship-level sums agree: `0x140071380` adds part `+0x7f8` (double) into ship `+0x1638` and part `+0x804` (int) into ship `+0x17ec`. The two table rows below that put the `mdl_fuel` double at `0x800` and `mdl_fss` at `0x808` are wrong (the 1.151-name pairing was off by one slot). Live check (probe v1.3, run 2): `+0x7f8` as a double read 4e5 on an installed `MDL_FUEL_02` (stats capacity 4.5e5, 0 on freshly held ones), so **the fuel slot is [game]**; `+0x800` / `+0x804` read 0 on all parts including both quarters parts (stats crew capacity 25), so the **crew slot (`+0x804`) is still [code] only**. The stats record's `+0xc8` (double capacity: 4e4 `MDL_FUEL_01`, 4.5e5 `MDL_FUEL_02`) and `+0xd4` (int crew capacity: 25 `MDL_QUARTERS_02`) are [game]. Old text kept for the record: **Open: Body `+0x800`/`+0x804`.** The 1.151 name `mdl_fuel` is a **double** copied as two words (0x800/0x804) in 1.163, yet the ship stats loop adds `Body +0x804` as a 32-bit integer into the crew total (see [findings/sensors-and-crew.md](findings/sensors-and-crew.md)). The two readings conflict; `structures.md` lists `+0x804` with both readings and flags the conflict. Settle it by reading a fuel part and a crewed module in game.

### Weapon and ammo fields, resolved with `FireGun` (1.151 `0x140032fa0`, 1.163 `0x140032e60`) [code]
The two versions of `FireGun` use the same fields in the same roles, so each field pairs exactly:

| Role in `FireGun` | 1.151 | 1.163 |
|---|---|---|
| ammo counter: test `< 1.0` exits, decremented by 1.0 per shot | `weaponAmmoAmount` `0x84c` | `+0x860` |
| float `> 0` blocks firing | `0x85c` | `+0x870` |
| byte set to 1 on entry | `fFireRateTimer` `0x860` | `+0x874` |
| float set to `1 / (rate / 60)` after a shot, non-zero blocks firing (`rate` is stats `+0x150` in 1.163) | `0x858` | `+0x86c` |
| value passed as the third argument of `FireShell` | `mdl_covered` `0x83c` | `+0x850` |
| stats lookup | `part_index` `0x188` | `0x188` |

* So in this zone the shift is **+0x14**, not +0xc. (An earlier first-pass guess of +0xc was wrong.)
* **Discrepancy with `structures.md` (resolved below):** the notes said `+0x848` = `m_mdl_covered` and `+0x858` = `m_weapon_ammo_amount`. The code supports the first half: `FUN_14001c4a0`
  (`UpdateEngineCovered`) clears and sets 1.0 at `+0x848`, and the AA launch `FUN_14002e590` (and the Zenith launch `FUN_14002ff60`) returns 0 unless `+0x848 == 0.0`, so `+0x848` really is the "engine cone blocked / launch
  blocked" flag. But `FireGun` decrements `+0x860`, not `+0x858`; the resolution below shows `+0x858` is the reserve count and `+0x860` the loaded rounds. The 1.151 field *names* `mdl_covered` / `mdl_turbine` are also swapped relative to what 1.163's `UpdateEngineCovered`
  writes (`+0x848` = 1.151 `0x834` `mdl_turbine`; the thing `FireGun` passes on is `+0x850`). Do not trust 1.151's name for that pair.
* The 1.151 names `fFireCharge` (`0x854`), `fFireRateTimer` (`0x860`), `fFireDelay` (`0x864`), `bFireStatus` (`0x868`) do not match how `FireGun` uses the fields (`0x860` is a byte flag, `0x858` and
  `0x85c` are floats). Those names in the 1.151 Ghidra struct look misplaced; do not carry them across.
* **`FireGun` itself changed:** 1.151 contains the 360-sector blocking check that `highfleet-qol` restores (`iSectorIndex`, "This is what stops you from firing if your gun is blocked by your own ship");
  1.163's `FireGun` has no sector check. Useful evidence for `systems.md` ("gun arc blocking restored by qol") and for the roadmap item about turret blocking.
* 1.151's `FireGun` also carries two logdot comments worth keeping: `FireShell` is the call that actually fires; and the rate cooldown store is required for guns to fire at all.

**Save keys of the whole block (static, 1.163, matched in `bodySecondaryInit`):** `+0x84c` `m_weapon_type`, `+0x850` `m_weapon_ammo` (the ammo index), `+0x854` `m_weapon_ammo_extra`, `+0x858` `m_weapon_ammo_amount`, `+0x85c` `m_weapon_ammo_extra_amount`, `+0x877` `m_rescue_explosive` (bool). The runtime fields `+0x860`..`+0x874` have no save key. So in this block the saved fields shift by **+0xc** and the `FireGun` runtime fields by +0x14; the single 1.151 counter was split into a saved reserve and a runtime loaded count.

**Resolution of the `+0x858` question (static, 1.163):** both are right. `+0x858` is the **reserve** (int), loaded from the save key `m_weapon_ammo_amount` (20 characters, matched in `bodySecondaryInit` at `0x140026d58`-`0x140026d73`); `+0x860` is the **loaded rounds** (float) that `FireGun` decrements. The per-frame update `FUN_140054fb0` moves rounds reserve to loaded one reload step at a time (timer `+0x864`, step size `+0x868`; magazine size and reload time are stats `+0x148` and `+0x14c`). `+0x854` is parsed from a 19-character key starting `m_weapon_ammo_ex`. The earlier pairing with 1.151 `ammoIndex` for `+0x858` was wrong. Not run in game.

### Unresolved parts of the Body remap
1. The bool cluster `0x86a..0x87c` (rescue flags, `isCrtScreen`, `repairType`): the 1.163 copy routine copies single bytes at `0x877..0x87b`, the 1.151 one at `0x878..0x87c`; the shift there is about 0
   (-1 for some bytes), not +0x14. Read the 1.163 constructor around `0x860..0x880` before laying these fields out. The region `0x880..0x980` then has to climb from about 0 to +0x30 (floor): unmapped.
2. Lighting fields (`lightColor*`, `lightFade`, `ambient`) and the `aircraft_logic` / `aircraftLogic` pair: assigned by zone only.
3. All fields in the `(unnamed)` rows of the 1.151 struct (about 60% of its size). They have no names to carry, so the remap matters only for resizing, not for naming.

## Profile remap (the world singleton): +0x48 for the vector block [code]
`Get_Profile` (1.163 `0x140292a90`, `Get_Profile_`) returns the `Profile`. The Ghidra `Profile` struct is the same size (1,380 bytes) and identical in both programs, which is a stale copy:
its vectors moved in 1.163.

| Vector | 1.151 (Ghidra name, offset) | 1.163 offset | Evidence |
|---|---|---|---|
| Escadras (fleets): begin/end | `escadras` `+0x1b0`/`+0x1b8` | `+0x1f8`/`+0x200` | `structures.md` already lists the friendly-fleet list at `+0x1f8/+0x200` [notes] |
| Missiles (map missiles): begin/end | `Missiles`/`MissileEnd` `+0x1e0`/`+0x1e8` | `+0x228`/`+0x230` | the map-launch consumer `FUN_1400eced0` pushes the new Missile at `+0x228` (end `+0x230`, cap `+0x238`) [code]; `structures.md` already says "missiles +0x228/+0x230" |
| MapCrafts (map aircraft groups): begin/end | `mapCrafts` `+0x228`/`+0x230` | `+0x270`/`+0x278` | 1.163 `CreateMapAircraftGroup` (`0x14010f8e0`) pushes the new group at `+0x270` (end `+0x278`, cap `+0x280`) [code] |
| `explosions`, `designs`, `items`, ... | `+0x1f0`, `+0x210`, `+0x278` | +0x48 presumably | [guess] |

* **Consequence for `structures.md` (applied):** `+0x270/+0x278` is the **MapCraft** vector and the fleet vector is `+0x1f8`; the notes' earlier "fleets +0x270" was a mix-up with the MapCraft target field at `+0x270`. (A MapCraft stores its target at `+0x270` as well, which may have caused the mix-up; that is a field of the
  MapCraft object, not of the Profile.)
* Ghidra's stale label `mapCrafts` at `Profile+0x228` in the 1.163 program is really the Missile vector; the real MapCraft vector has no name there.
* Same method as the `Body` remap : pair a function present in both versions, compare the offsets it uses.
* **Decisive confirmation (the map-intercepts section of map-air-groups.md):** `runMissileandAircraftIntercept_` is present in both versions. In 1.151 it walks `Profile.Missiles` (the missile-kill loop with the 75% roll) and then
  `Profile.mapCrafts` (the craft-down loop with the 66% roll); in 1.163 the **first** loop walks `+0x228/+0x230` and the **second** `+0x270/+0x278`. Same code, same roles, so Missiles `+0x1e0 -> +0x228` and
  MapCrafts `+0x228 -> +0x270` [code].

## Fleet (Escadra) field shifts [code]
Count `+0x4e8` to `+0x4ec`, range `+0x4f0` to `+0x4f4`, missile-launch cooldown `+0x508` to `+0x50c`, aircraft cooldown `+0x50c` to `+0x510`, time stamp `+0x518` to `+0x528`, state `+0x188` unchanged (from `TryLaunchAiAircraftGroup` and the fleet update). So the `+0x50c` cooldown the salvo mod patches is a different field from the aircraft cooldown `+0x510`. The Escadra struct in Ghidra is `0x600` bytes against the real `0x618`.

## Stats record (`ShipPart` in 1.151, `GetStats` in 1.163) [code + Ghidra struct]
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

* **Fuel versus crew (now applied to `structures.md`, see [findings/sensors-and-crew.md](findings/sensors-and-crew.md)):** the old notes called `+0xd4` "tank capacity (int; the part's current fuel is Body +0x804)". In 1.151 `+0xd4` is **`mdl_crew_capacity`** (int) and the **fuel tank capacity is the double at `+0xc8`**
  (`mdl_fuel_capacity`), which also fits ship-level fuel being doubles (`+0x1638/+0x1640`). Correction: `+0xc8` tank capacity (double), `+0xd4` crew capacity.
* **`GetMissileFuzeType`** is the only getter returning an int; all others return floats, which the notes' units already assume.
* **`GetPartPrice`** returns 0 when `endWar` is set (Profile field `endWar`, Ghidra offset 657 = `0x291` in 1.151) or when the part's category has bit 6 (`0x40`, "block, bridge") set; otherwise `price`. This is why bridge/block
  parts are free to swap in the editor and why prices vanish after the war ends. Not in the notes.
* The notes' sentence "Stats record ... `GetStats(index)` `FUN_140281e00`" is right: 1.163 `GetStats` is a bounds-checked pointer-array lookup (checked); the 1.151 name is `GetShipPart`.

## The `Ammo` record and ammo values
The `Ammo` record is `0x168` bytes in 1.151 and `0x188` in 1.163 (new `shell_enemy` string and a float `ttl` at `+0x16c`). Careful: `+0x16c` is `cluster` in the stats record and `ttl` in the `Ammo` record. Full table and every value change: [findings/ammo-1151-vs-1163.md](findings/ammo-1151-vs-1163.md).

## Ghidra struct status, 1.163 [code, sizes vs allocation sizes]
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
| `Profile` | 1380 (`0x564`) | not allocated through `CopyObject` | layout moved (Profile remap above) |
| `HGEVFTABLE` (800 bytes, 100 slots) | **absent in 1.163** | 101 slots | missing; 1.151 has it (engine-hge.md) |
| `ShipPart` (384 bytes) | **absent in 1.163** | `0x188` | missing; 1.151 has it (stats record above) |

* The 1.151 program also carries the type categories `hge.h` (and `hge.h/functions`), `hge.pdb`, `unzip.h`, `zlib.h`, `ioapi.h`, `bass.h`, `mfobjects.h`, `rpcndr.h`, `tapi.h`, `wtypes.h`, `New Category` and `HighFleet`; 1.163 lacks them. Both have the project categories `_Body`, `_Escadra`, `_Missile`, `_Profile`, `_Creature`, `_AircraftLogic`, `_Link`, `_Node`, `_GUI`.
* **Order for the struct rebuild:** the OK structs need nothing; `Body`, `Escadra`, `Creature` get a remap (the Body remap is above; the Escadra shift so far: count `+4`, range `+4`, missile cooldown `+4`,
  aircraft cooldown `+4`, time stamp `+0x10`, i.e. +4 early and +0x10 by `+0x518`); `ShipPart` and `HGEVFTABLE` can be created from the stats table above and the HGE slot list in engine-hge.md (1.163 needs two extra stats fields and one extra vtable slot).
* **Cleanup:** every `*.conflict` type should end up replacing its non-conflict twin (the non-conflict `Body`, `BodyVFTABLE`, ... are the older 1.151 copies still referenced by names such as `createNewBody`'s
  signature). Do it only after a check of which functions use which twin.

## Strings: what 1.163 added or removed [code, `list_strings` diff of the two programs]
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
* **Stats record fields (confirms the stats table):** the strings **`m_mdl_sectors_shift`** and **`m_missile_explosive_cluster`** exist only in 1.163: these are exactly the two fields inserted in the stats record,
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

## 1.151 annotation themes the 1.163 program lacks (354 names)
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


## Gameplay differences
* **Explosion damage** [game, both versions] (2026-10-14): Zenith-class warhead 200 -> 300, first armored part in the blast chain x2 -> x4, ordinary part cost flat 5 -> `maxHP/20` (trusses free, armor 10 in both); 180mm gun shells unchanged. Details and evidence: [findings/explosion-damage-1151-vs-1163.md](findings/explosion-damage-1151-vs-1163.md).
* **Ammo table** (2026-10-14): shell lifetime `ttl` per ammo (100 mm 10 s to 4 s, 130 mm 10 s to 7 s, 180 mm 10 s to 30 s), rocket warheads, incendiary power and more. 1.163 values confirmed live by the ammo-table dump (`hf_probe` v1.3; the shop price `+0x170` confirmed for one item) [game]; the 1.151 values come from the decompile [code]. Details: [findings/ammo-1151-vs-1163.md](findings/ammo-1151-vs-1163.md).
* **Part stats in `OL.seria`** (live data files, 2026-10-14): `MDL_CANNON_180` reload 6 -> 5 s, power need 1800 -> 1200, price 4000 -> 3000; `MDL_CANNON_305_2` rate 180 -> 240; `MDL_KAZ` power need 10 -> 100 and price 1500 -> 2000; crew need up on 11 parts (e.g. `MDL_FCR_01` 1 -> 8); sector thresholds changed on 14 parts. Full list: [findings/explosion-damage-1151-vs-1163.md](findings/explosion-damage-1151-vs-1163.md) (Data files).
