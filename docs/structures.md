# Game structures (1.163)

Tags: legend in `../README.md`. Offsets are hex byte offsets.

## Class codes (`m_code`, at object +0x28) and sizes (from the copy routine `FUN_1401bfd00`)
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
| 0x800000001047 | **MapCraft** (map aircraft group) | 0x270 |

## Body (ship part): ctor `FUN_140015690`, vtable `0x140352a30`
| Offset | Field |
|---|---|
| +0x28 / +0x48 | class code / state (0 = dead or dropped) [code] |
| +0x78 | `m_id` int64 [game] |
| +0x88 | master (hull/frame it is mounted on) [game] |
| +0xb0 / +0xb8 | owner smart-ref / owner pointer [game] |
| +0x128 / +0x12c, +0x130, +0x138 | position x,y (local to master), velocity, angle [game] |
| +0x188 | stats index [game] |
| +0x190 / +0x1a0 / +0x1a8 | `m_oid` std::string: data or SSO, length, capacity [game] |
| +0x1d0 `m_density`, +0x1f0 `m_layer`, +0x2c8/+0x2cc `m_health`/max [code] |
| +0x350 / +0x358 | slot vector begin / end [game] |
| +0x3c0 / +0x3c8 | launch timer / `m_logic_active` (set by the launch) [game] |
| +0x3d0.. / +0x3e4.. | `m_logic_f1..f4` / `m_logic_i1..i4`. `i4` (+0x3f0) held the first prototype's charge count; `i1` is used heavily by `FUN_140033b90` [game] |
| +0x490 / +0x4a8 | target ref / owner ref written by the launch [code] |
| +0x508 / +0x510 | `m_sectors` vector<float>, 360 entries after a scan [game] |
| +0x7a8 / +0x7ad | `m_count` / blueprint flag [game] |
| +0x848 | `m_mdl_covered` (1.0 when the engine cone is blocked); also a cooldown test in the launch [code] |
| +0x858 | `m_weapon_ammo_amount` [code] |
| +0x8d8 `m_stage` (not elevation), +0x90c `m_z` [code] |
| +0x9b0 / +0x9b8 | `m_floor_type` bitmask / `m_floor` = **elevation** [game] |
| +0xa28 | `m_ed_rotate` [code] |

Vtable slots: +0x40 kill(this,1), +0x48 kill, +0x50 add child, +0x68 remove from master, +0x80/+0x88 editor "place" steps, +0xe0/+0xe8 master angle/position
transform, +0x178 side (float; sign = friend/foe), +0x210 damage. Smart-ref = 0x18 bytes (vtable, pointer, ?): ctor `FUN_140194bd0(ref,node)`, copy
`FUN_140194b80`, dtor `FUN_140194d20`, assign `FUN_140194de0`; reallocating vector insert `FUN_140004b00(vec,pos,ref)`; `FUN_1402c7c90` = `vector<Node*>::insert(range of refs)`.

## Stats record (`GetStats(index)` `FUN_140281e00`; id -> index `FUN_140281cc0`) [code]
+0x88 price, +0x8c important, +0x90 timecost, +0x94 repair_cost, +0xb0 **category**, +0xb4 sort_index, +0xc4 armor, +0xd0 fuel_need, +0xd4 tank capacity (int; the part's current fuel is Body +0x804), +0xd8 crew_need,
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
+0x270 the tracked incoming missile · +0x420 `m_refuel_timer` (float), +0x424 `m_refuel_amount` · +0x461/+0x468 flags (+0x468 refuel animation) ·
+0x498 / +0x4a0 fuel and capacity (doubles) · **+0x50c launch cooldown (float)** [game] · **+0x538/+0x540/+0x548 map launch queue** [game] ·
callsign/name strings. Ship (Creature) fields used: +0x1638/+0x1640 fuel current/capacity (doubles), +0x1330 part list, +0x13d8/+0x13f0 launch lists, +0x17b0 in-flight limit,
+0xad4 owner cooldown. Station (location): +0x258 flag, +0x25c type (4 = fuel city), +0x274 fuel stock (float).

## Map missile (Missile, 0x400000001047), ctor `FUN_1400e48a0`, vtable `0x14035e998` [game]
+0x150/+0x154 position · +0x158 speed · +0x15c heading · +0x240 reverse flag · **+0x248 count** (launch writes 1) · +0x270 target fleet · +0x29c type (3 = ground, range <= 60) ·
**+0x2b8 / +0x2c8 / +0x2d0 part id** (std::string). The world singleton `FUN_140292a90()` holds the lists: missiles +0x228/+0x230, fleets +0x270/+0x278, friendly-fleet list +0x1f8/+0x200.
`FUN_1400ec440(a,b,dt)`: do two map objects come within 1.0 of each other during the next dt step (closest approach along headings); used for every encounter.
