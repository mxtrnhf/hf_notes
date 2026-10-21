# AI ship steering: obstacle avoidance, force law, attitude hold (v1.163), ghidra-miner, 2026-10-21

Tags: **[V]** = read in the 1.163 program (decompile plus disassembly, constants read from memory). Names: `AiShip_SteerController` `0x14006cb30` (driver states 0 and 4), `AiShip_ScanObstacles` `0x14024cc20`, `AiShip_AddObstacleNode` `0x14024ce50` (renamed 2026-10-21 from `rep_14022bc20_New`; adds one obstacle; the old name carried the 1.151 address, do not decompile that address in 1.163). `AiShipTick` `0x140062f90` carries an **inlined copy of the same law** (scan call at `0x140064e6f`, same parameters), so the numbers below hold for both paths [V].

## 1. What the avoidance sees (ScanObstacles) [V]
Called with `range = clamp(4 * |v|, 200, 800)` (v = own hull velocity, root body `+0x130/+0x134`), `minMass = 0.1 * own mass (+0x15b8)`, `maxExplosive = 500.0`.

Loop over the whole global body array (up to 15000 entries). A body is **considered** when: it is active (vtable `+0x78`), it is not the ship's own root and not owned by the same link as the ship (`body+0xb8`), its class nibble is `0xf` and it has a b2 body (`+0x178`).
A considered body is then **dropped** when all of these hold: `minMass != 0`, vtable `+0x1a8` returns 0 (meaning not read), and `returnMass(body) < minMass`. The drop is **cancelled** (body kept) when `body+0x2dc >= 500` (explosive power, so a light but strongly explosive object is still avoided). Another override keeps a body when `creature+0xd70 == 2` and bit 21 of `FUN_1400457d0(body)` is set (not read). So the avoided set is: all other ships' parts (friends and the player, one entry per part body), debris and wrecks heavier than 10 % of own mass, big explosive objects. Shells, missiles and light debris are ignored. [The earlier note had the explosive test reversed.]

Each kept body goes through `AiShip_AddObstacleNode(body, ownPos, ownRadius, list, range)` (own radius = `creature_root+0x20c`; obstacle radius = `body+0x20c`; compound bodies, class bits `0x1f`, recurse into their children):
* `d` = centre distance; `gap = d - ownRadius - obsRadius`. Kept only if `gap <= range` and `d >= 0.001`.
* Node (0x38 bytes): body, pos (+8,+0xc), velocity (+0x10,+0x14; the body's `+0x130/+0x134`, or the master's if the body has a compound master), radius (+0x18), unit vector **ship to obstacle** (+0x1c,+0x20), gap (+0x24), bearing (+0x28), shadow interval `[bearing - atan2(r, d), bearing + atan2(r, d)]` (+0x2c,+0x30), weight (+0x34, filled later).
* List is sorted by gap ascending. A new node whose bearing lies inside the shadow interval of a nearer node is **discarded** (hidden behind it); after insertion, farther nodes whose bearing falls inside the new node's interval are **deleted**. So only the obstacles visible from the ship's position survive.

## 2. Avoidance force [V]
Per surviving node: `closing = (v_self - v_obs) . dir` (positive = approaching), `t = gap / closing` (`gap <= 0` is replaced by 0.1; `closing == 0` or `t > 10` gives weight 0; `t <= 0`, i.e. receding, gives weight 0), then

`w = ((10 - t) / 10)^2` (stored at node `+0x34`).

`A = - sum(w_i * dir_i)` (pushes away). Weight factor `creature+0xc04` is set to 1.0 in the AI-ship setup (`0x140072d74`) and no other creature code writes it, so use 1.0. (`AiShipTick`'s copy omits the multiply, same result.)

## 3. Force law (translation) [V; constants read: 9.82, 10, 20, 100, 0.1, 3.0]
* `dir_t` = unit vector from hull to waypoint (`creature +0xbf0/+0xbf4`), `dist` = distance; `s = clamp(sqrt(dist + 0.1) / 20, 0, 1)` (s reaches 1 at dist 400).
* Desired velocity `v_des = 100 * s * (A + dir_t)` (not normalised, so |A + dir_t| can exceed 1 or fall toward 0 when the avoid term cancels the heading).
* `F = m * (v_des - v) / kk - (0, m * 9.82)` with `kk = 10 / TWR`, `TWR = (T1 + T2) / (m * 9.82)`, `T1/T2 = creature +0x1664/+0x1668`, `m = +0x15b8`. So `F = (T1 + T2) / 98.2 * (v_des - v) - (0, 9.82 m)`: a proportional velocity controller whose gain scales with thrust to weight ratio (acceleration `= TWR/10 * (v_des - v)` plus gravity compensation).
* If `T1 == 0` or `T2 == 0` the function returns without sending any command (ship adrift).

## 4. Attitude hold [V]
* Gate: `creature +0x180c / I > 0.02`, with `I = Body_GetInertiaAboutOrigin(root)` (`FUN_140048440`). `+0x180c = 2 * min(+0x1684, +0x1688)` (sums of Stats `+0x100` per bank). Gate off: no torque term at all (the engines' own stabiliser, see `hull-stabiliser-engine-logic.md`, is separate and always runs).
* Commanded angle is **0 rad** (hull level, world frame); `a` = hull angle (root `+0x138`). `e = wrap(0 - a)` into `[-pi, pi]`.
* P term only, no derivative, no cap: `k = e * I / 20`, `h = (sin a, -cos a)`; **bank 1 vector += k h, bank 2 vector -= k h** (the same pair construction as the player's Q/E keys but with magnitude k).

## 5. From force to engine commands [V]
1. Bank vector = `F` (+ attitude pair). Clamp per bank, with `T` = that bank's thrust sum (`+0x1664` / `+0x1668`): if `|vec| > 3T` scale to `3T`; **else if `|vec| > T` scale to `T`**. (This is what the disassembly does, `COMISS` polarity checked at `0x14006d2ea` / `0x14006d31c`: values between T and 3T are cut to T, values above 3T are cut to 3T. Odd, but it is the code.)
2. Smoothing: five stored slots per bank (x at `+0xc1c + 8 i`, y at `+0xc20 + 8 i`; bank 2 at `+0xc44` / `+0xc48`), shared ring index `+0xc6c` (0..4). `out = (sum of the 5 slots + new clamped vector) / 6`; then `slot[idx] = out` (the **output** is stored, not the raw input, so it is an IIR-like filter), `idx = (idx + 1) mod 5`. Slots start at 0.
3. Per bank: angle `= -atan2(-x, -y)` wrapped to `[0, 2pi)`; strength `= |out| / T_bank` (can reach 3.0, the player's keys give 1.0, boost 2.0).
4. Commands to every engine part in the list `+0x1330`: `100` (bank 1 angle), `0x65` (bank 2 angle), `0x66` (bank 1 angle and strength), `0x67` (bank 2 angle and strength); parts act on their own bank.
5. Side effect: `creature +0x1328/+0x132c` = unit direction of `F` before the attitude term and filter.

## 6. What this does not explain / open
* **Question "what zeroes `+0x17fc/+0x1800` each tick": nothing new.** `Creature_ResetStatAccumulators` `0x140061e70` (callers `CalculateStats`, `0x140072b90`) writes 8 bytes at `+0x17f0` (covers `+0x17f0..+0x17f7`), `+0x180c`, `+0x17e4/+0x17e8`, and does **not** touch `+0x17fc..+0x1803/+0x1804..+0x180b`. Still no per-tick clearing store known; treat the logged per-tick behaviour as fact.
* Not read: vtable `+0x1a8` meaning, `FUN_1400457d0` bit 21 and the `+0xd70 == 2` mode, how `AiShipTick` picks the waypoint (`+0xbf0/+0xbf4` writes at `0x140064a8d`, `aiShipDriver` `0x140073d3f`).
* Units: velocity and positions are in game units (not Box2D metres); thrust sums are compared with `m * 9.82`, so thrust is in mass-unit x 9.82. A fit against logged AI flights is the only check of the absolute scale.
