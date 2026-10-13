# Game structures (1.163)

Tags: legend in `../README.md`. Offsets are hex byte offsets. What moved between 1.151 and 1.163 (Body, Profile, stats record, Ghidra struct status): [version-differences.md](version-differences.md).

## Class codes (`m_code`, at object +0x28) and sizes
| Code | Class | Size |
|---|---|---|
| 0x7 | Node | 0x128 |
| 0xf (15) | **Body**, a ship part | 0xa40 |
| 0x1f (31) | Frame (hull group) | 0xa58 |
| 0x2f (47) | Creature / ship | 0x1a50 |
| 0x47 | (unnamed) | 0x248 |
| 0xc7 (199) | location (city/station) | 0x370 |
| 0x147 (327) | **Escadra**, a fleet | 0x618 |
| 0x203 (515) | intel entry | 0x1b8 |
| 0x400000001047 | **Missile** (map object) | 0x308 |
| 0x800000001047 | **MapCraft** (map aircraft group) | 0x340 |
| 0x8000000003 | (unnamed; Ghidra calls its ctor `CreateFX`) | 0x270 |
| 0x80007 | **AADefense**, a ground-defense unit [code, 1.151 `createGroundDefenseCreatures__` `0x140004950`; 1.163 size not checked] | - |

**Codes nest as bit sets.** The code tests membership with a mask, for example `(code & 0x147) == 0x147` for a fleet and `(code & 0x800000001047) == 0x800000001047` for a MapCraft
[code], and `& 0x4000f`, `& 0x2f` for Body-like objects. The values themselves look like an inheritance chain: 0x7 (Node) -> 0xf (Body) -> 0x1f (Frame) / 0x2f (Creature), 0x7 -> 0x47 ->
0x147 (Escadra) / 0xc7 (location), and 0x1047 as the common base of Missile (0x400000001047) and MapCraft (0x800000001047) [guess]. Practical rule: to test "is this a X", mask and compare; do not compare equal to the code.

Source of the sizes [code]: the copy routine `FUN_1401bfd00` (`CopyObject`, one `New(size)` per code) for every row **except** `0x800000001047`. That code has no case in the copy routine;
its 0x340 comes from the default-construction factory (entry `0x1402024e0`, Ghidra name `Panel::Constructor`; a switch on the code, `New(0x340)` then `FUN_1400e4530`, which
builds on the `Mark` constructor). The same factory gives the same sizes for the other rows, and also covers codes the copy routine lacks (for example `0x800000000003` = 0x1b0, ctor named `AircraftLogic` by Ghidra; `0xc000f` = 0xe98; `0x44000f` = 0xf18).

## Body (ship part): copy ctor `FUN_140015690` (Ghidra `createNewBody`: takes a source object and calls `copyOverBody`; the default one is `Body::Body(this, 1)` in the factory), vtable `0x140352a30`
| Offset | Field |
|---|---|
| +0x28 / +0x48 | class code / state (0 = dead or dropped) [code] |
| +0x78 | `m_id` int64 [game] |
| +0x88 | master (hull/frame it is mounted on) [game] |
| +0xb0 / +0xb8 | owner smart-ref / owner pointer [game] |
| +0x128 / +0x12c, +0x130, +0x138 | position x,y (local to master), velocity, angle [game] |
| +0x188 | stats index [game] |
| +0x190 / +0x1a0 / +0x1a8 | `m_oid` std::string: data or SSO, length, capacity [game] |
| +0x1b0 `m_b2bstate` [code], +0x1d0 `m_density`, +0x1f0 `m_layer`, +0x2c8/+0x2cc `m_health`/max [code] |
| +0x350 / +0x358 | slot vector begin / end [game] |
| +0x3c0 / +0x3c8 | launch timer / `m_logic_active` (set by the launch) [game] |
| +0x3d0.. / +0x3e4.. | `m_logic_f1..f4` / `m_logic_i1..i4`. `i4` (+0x3f0) held the first prototype's charge count; `i1` is used heavily by `FUN_140033b90` [game] |
| +0x490 / +0x4a8 | target ref / owner ref written by the launch [code] |
| +0x508 / +0x510 | `m_sectors` vector<float>, 360 entries after a scan [game] |
| +0x7a8 / +0x7ad | `m_count` / blueprint flag [game] |
| +0x848 | `m_mdl_covered` (1.0 when the engine cone is blocked); also a cooldown test in the launch [code] |
| +0x84c / +0x850 / +0x854 / +0x858 / +0x85c | saved weapon keys (matched in `bodySecondaryInit`): `m_weapon_type`, `m_weapon_ammo` (the ammo index `FireShell` dispatches on), `m_weapon_ammo_extra`, **`m_weapon_ammo_amount` = reserve rounds (int)**, `m_weapon_ammo_extra_amount` [code, key strings] |
| +0x860 / +0x864 / +0x868 | runtime, no save key: **loaded** rounds (float; `FireGun` decrements it, needs >= 1) / reload step timer / rounds the current reload step adds (1 if the reserve was non-empty, else 0). `FUN_140054fb0` moves rounds reserve -> loaded one step at a time. Magazine size = Stats `+0x148`, reload time = Stats `+0x14c` [code] |
| +0x800 / +0x804 | 1.151 name `mdl_fuel` (double, two words); but the ship stats loop sums `Body +0x804` as an int next to crew (crew present?). Conflicting readings, open: [version-differences.md](version-differences.md) [code] |
| +0x8d8 `m_stage` (not elevation), +0x90c `m_z` [code] |
| +0x9b0 / +0x9b8 | `m_floor_type` bitmask / `m_floor` = **elevation** [game] |
| +0xa28 | `m_ed_rotate` [code] |

Vtable slots: +0x40 kill(this,1), +0x48 kill, (+0x48 kill goes `FUN_140049ea0` -> `FUN_1402805d0` -> vtbl+0x40(this,1)), +0x50 add child, +0x68 remove from master, +0x80/+0x88 editor "place" steps, +0xe0/+0xe8 master angle/position
transform, +0x178 side (float; sign = friend/foe), +0x210 damage. Smart-ref = 0x18 bytes (vtable, pointer, ?): ctor `FUN_140194bd0(ref,node)`, copy
`FUN_140194b80`, dtor `FUN_140194d20`, assign `FUN_140194de0`; reallocating vector insert `FUN_140004b00(vec,pos,ref)`; `FUN_1402c7c90` = `vector<Node*>::insert(range of refs)`.

## Stats record (`GetStats(index)` `FUN_140281e00`; id -> index `FUN_140281cc0`) [code]
+0x88 price, +0x8c important, +0x90 timecost, +0x94 repair_cost, +0xb0 **category**, +0xb4 sort_index, +0xc4 armor, +0xd0 fuel_need, +0xc8 fuel capacity (double), +0xd4 crew capacity (int) [code, indirect: the 1.151 names plus the ship stats sum; `findings/sensors-and-crew.md`], +0xd8 crew_need,
+0xe0 power_need, +0xf8 thrust, +0xfc thrust_map, +0x10c radar, +0x110 tracking, +0x114 guiding, +0x118 elint, +0x11c irst, +0x120 jammer, +0x128 sectors_type
(non-zero = takes part in arc scanning), +0x12c sectors_shift, +0x130 sectors_threshold, +0x140 weapon_priority, +0x144 caliber, +0x148 load_amount, +0x14c load_time,
+0x150 rate, +0x154 acceleration_time, +0x158 launched_speed, +0x15c speed2, +0x160 range, +0x164 missile_type, +0x168 explosive (> 100000 = nuclear), +0x16c cluster,
+0x170 ap, +0x174 agility, +0x178 radar_range, +0x17c radar_cone, +0x180 fuze_type, +0x184 launched_health.
Units [guide]: `m_weapon_load_time` in 4/7 s; `m_launched_range` km for strategic; `m_launched_speed` m/s on the map, `speed2` arcade; guns with the lowest priority value are
auxiliary (ground units fire only priority <= 100). Caliber index ties to shell stats (ammo-extended `padding_cch`).

### `m_category` bits [game: read from every `m_stats` record of the 1.163 `OL.seria`]
0-based bit = value 2^n. (The community guide numbers the same bits from the high end: guide N = bit 32 - N; its descriptions match.)

| Bit | Value | Parts with it | Bit | Value | Parts with it |
|---|---|---|---|---|---|
| 0 | 1 | fuel | 14 | 16384 | tactical missiles (arcade launch) |
| 1 | 2 | armor | 15 | 32768 | protector (?) |
| 2 | 4 | FSS | 16 | 65536 | radar, FCR, SPO (ELINT/radar) |
| 3 | 8 | escape pods (EVAC) | 17 | 131072 | railing |
| 18 | 262144 | (unused in vanilla) |
| 4 | 16 | ammo | 19 | 524288 | ground units, missile drum |
| 5 | 32 | **gun** (cannons, harpoon, RSZO, torpedo) | 20 | 1048576 | IR detection (IRST) |
| 6 | 64 | block, bridge | 21 | 2097152 | bomb |
| 7 | 128 | hull (HARD, FERMA) | 22 | 4194304 | jammer |
| 8 | 256 | engine | 23 | 8388608 | flares |
| 9 | 512 | destiller | 24 | 16777216 | rescue items |
| 10 | 1024 | aircraft (CRAFT_*) | 25 | 33554432 | KAZ (active protection) |
| 11 | 2048 | generator, quarters | 26 | 67108864 | deck |
| 12 | 4096 | cargo | **27** | **134217728** | **strategic launch** (all `MDL_NUKE_*`, so the A-100) |
| 13 | 8192 | leg | 28-31 | - | unused |

The guide adds: gun enables elevation and shifts it +1; bit 19's group enables arc calculation and shifts elevation -1 (?). Cross-check [game]: the raycast "may block" test uses
`~(category >> 5) & 1`, i.e. a body blocks a ray unless it is a **gun** (bit 5), or the floor rule allows it (`systems.md`).

## Fleet (Escadra, 0x147) [code unless noted]
+0x100 std::list of ships (ship objects via `FUN_14021b070`) · +0x150/+0x154 position · +0x158 speed · +0x15c heading · +0x240 reverse flag ·
+0x270 the tracked incoming missile or MapCraft [code: also read as a MapCraft-masked pointer in `changeAircraftState_`] · +0x420 `m_refuel_timer` (float), +0x424 `m_refuel_amount` · +0x461/+0x468 flags (+0x468 refuel animation) ·
+0x498 / +0x4a0 fuel and capacity (doubles) · **+0x50c launch cooldown (float)** [game] · **+0x538/+0x540/+0x548 map launch queue** [game] ·
callsign/name strings. Ship (Creature) fields used: +0x1638/+0x1640 fuel current/capacity (doubles), +0x1330 part list, +0x13d8/+0x13f0 launch lists, +0x17b0 in-flight limit,
+0xad4 owner cooldown. Station (location): +0x258 flag, +0x25c type (4 = fuel city), +0x274 fuel stock (float).

## Map missile (Missile, 0x400000001047), default ctor `FUN_1400e48a0` (no source argument; sets the name "Missile" and the code; the copy ctor is `Missile`, which also references the vtable), vtable `0x14035e998` [game]
+0x150/+0x154 position · +0x158 speed · +0x15c heading · +0x240 reverse flag · **+0x248 count** (launch writes 1) · +0x270 target fleet · +0x29c type (3 = ground, range <= 60) ·
**+0x2b8 / +0x2c8 / +0x2d0 part id** (std::string). The world singleton `FUN_140292a90()` holds the lists: missiles +0x228/+0x230, **MapCrafts +0x270/+0x278**, fleets +0x1f8/+0x200 [code: `CreateMapAircraftGroup` pushes at +0x270 and the map intercept loops walk +0x228 then +0x270; the earlier "fleets +0x270" was a mix-up with the MapCraft target field]. In the Ghidra program the `Profile` struct is the stale 1.151 layout (vectors +0x48).
`FUN_1400ec440(a,b,dt)`: do two map objects come within 1.0 of each other during the next dt step (closest approach along headings); used for every encounter.

## Creature (ship) fields seen in the AI and launch code [code]
+0xad4 side float (negative non-zero = AI side, positive = player, 0 = neutral; inferred from where the difficulty byte applies [guess]) · +0xbbc..+0xbc0 control flags (+0xbbd drives `FireGuns`, +0xbbe `FUN_14002e7d0`, **+0xbc0 flares**) · +0xc98 per-ship strategic/aircraft launch counter · +0xcb8 / +0xd60 / +0xd64 launch timers and cooldowns ·
+0x13d8 / +0x13f0 launch lists (stride 0x18, entry +8 = part) · +0x1408..+0x1410 flare launcher list · +0x1840/+0x1844 centre of mass · **+0x1850 bounding radius** (written only in `CalculateStats` `0x14007ffaa`) · +0x1838/+0x183c weapon reach floats · +0x17ec/+0x17f0/+0x17f4 crew present / capacity / needed (int sums) · +0x1638/+0x1640 fuel (doubles).
Details and addresses: [findings/ai-tick-patch-sites.md](findings/ai-tick-patch-sites.md), [findings/ai-flares.md](findings/ai-flares.md), [findings/sensors-and-crew.md](findings/sensors-and-crew.md).

## Projectile logic ids (Body `+0x3c4`, set from the `Ammo` record's `caliber`) [code]
100 plain shell · 130 rocket · 132 300 mm rocket (1.163) · 135 harpoon (1.163) · 140 laser guided · 160 proximity fuze · 0x44c (1100) flare. `creatureLogic` (`0x140033b90`) branches on this id; it is the per-body behaviour dispatcher for projectiles, missiles and aircraft, not the ship AI. See [findings/firing-and-shells.md](findings/firing-and-shells.md).
