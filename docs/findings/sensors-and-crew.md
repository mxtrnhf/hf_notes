# How a ship combines its parts' sensors, and the `+0xd4` crew-capacity question (1.163)

Status: **read from the 1.163 ship stats recompute; not run in game.** Tags: legend in `../../README.md`.

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
(two jammers add), which looks deliberate. The fleet level also takes a **maximum** (fleet `+0x4d0..+0x4e0` are `MAXSS` over ships, `0x14011b7a9..0x14011b809`; the older reading that `+0x4f0` is the detection range is wrong, see below). So if the in-game accumulation is real, it is either (a) in a later stage that turns these arrays into an effective range (not read), (b) the jammer
rule being what the reporter saw, or (c) a UI/readout effect. **Status (updated 2026-10-20): false as stated.** The later stage was read (DeepSeek `hf_ml/out/ds2-sensors`, formula re-read by Claude in the decompile of `0x1402378a0`, Ghidra label `rep_140219810_Get_Profile_`, the only caller is `UpdateStrategicFleet` at `0x1401156ba`) [code]: detection strength between observer fleet O and target fleet T is `R*R/2500 * S / (d*d)` minus a jammer sum, clamped to 0..1, with `R` = O `+0x4d0` (the radar maximum over its ships), `S` = T `+0x178` (target size), `d` = distance in km. Only the radar maximum enters it; tracking (`+0x4d4`), ELINT (`+0x4d8`), IRST (`+0x4dc`) and jammer (`+0x4e0`) feed separate tests, and no two sensor types are ever added or multiplied. Jammer term: for each fleet with `+0x180 != 0` whose bearing lies within 0.2 rad of a 90-degree axis relative to the target bearing, `+0x4e0/(d+1)` (the divisor uses the observer-target distance, not the distance to the jammer) [code], plus the same for the second list at profile `+0x240` using `+0x250`. **Gates the DeepSeek report left out (found by Claude):** the function returns 0 unless `T+0x158 != 0`, and the range gate `d <= min(R, R*S/2500)` is replaced by 0 (detect only when the caller passes the force flag) when `O+0x42c == 0`; what those two fields are is unknown. The horizon test uses `distanceFormulaTriangle_(h1/1000, h2/1000, 1)` [code]. The per-type number at `+0x17a0..` is the mean of two fixed arcs (72.8..107.2 and 252.8..287.2 degrees) of the max-merged array, and each part overwrites it (last part wins) [agent]; that, plus the summing jammer, are the only things that can look like accumulation [guess]. **Fleet `+0x4f0` is not a detection range:** the `MAXSS` at `0x14011b73d` (bytes `F3 0F 5F 85 D8 17 00 00`) takes the max of ship `+0x17d8` = max of stats `+0x160` (launcher range) over parts with category bit `0x8000000`, and no instruction reads fleet `+0x4f0` [agent: 'no reader' comes from a literal-offset search]. A live test is still the two-radars readout.

**Resolves the `+0xd4` question .** In the same loop: stats `+0xd4` is added into ship `+0x17f0`, the part's `Body +0x804` into ship `+0x17ec`, and stats `+0xd8` (crew need) into `+0x17f4`; all three are 32-bit integer sums.
Ship fuel is stored as doubles (`+0x1638`/`+0x1640`), so integer sums next to crew need are far more consistent with **`+0xd4` = crew capacity and `Body +0x804` = crew currently in the part** than with fuel. That matches logdot's 1.151 names (`mdl_crew_capacity` `0xd4`, `mdl_crew_need` `0xd8`, `mdl_fuel_capacity` a double at `+0xc8`).
Cross-check in the game's `OL.seria` [game]: `m_mdl_crew_capacity` exists on `MDL_COMBRIDGE_01` (60), `MDL_QUARTERS_01` (50), `MDL_QUARTERS_02` (25), and `m_mdl_fuel_capacity` on `MDL_FUEL_01/02/03` (40000, 450000, 80000), as separate keys, so the stats record has both. Which key sits at which offset still comes only from the 1.151 names plus the aggregation above, not from a direct read of
the loader. **Applied to `structures.md` (marked indirect): `+0xd4` crew capacity (int), `+0xc8` fuel capacity (double), `Body +0x804` summed as an int next to crew.**
It also bears on the roadmap's "functional crew-requirement system": the totals (`+0x17ec` present, `+0x17f0` capacity, `+0x17f4` needed) already exist per ship; what consumes them was not looked for.

## Live-test recipe
* Sensors: two radars on one ship, then one, and read the radar sector range in the ship readout; a breakpoint on the helper `FUN_140061260` shows the last argument (0 = max, non-zero = sum) per call.
* Crew: a breakpoint in the stats loop at `0x140072200`-`0x140072614` and a read of ship `+0x17ec`/`+0x17f0`/`+0x17f4` with a crewed and an uncrewed module.
