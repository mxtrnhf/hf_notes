# How the game works (launching, engagements, refueling)

Addresses are for Steam 1.163. **[game]** = verified in play, **[code]** = read from the decompilation.

## Combat missile launch [game]
* `FUN_14002e590(part)` (player) / `FUN_14002e3a0(part, target)` (AI) need a target (`FUN_14006c0e0`/`FUN_14006c440`), the owner (+0xb8), the owner's cooldown (+0xad4) and in-flight
  limit (owner+0x17b0). They store target/owner refs at part+0x490/+0x4a8, set `+0x3c8`, start a timer, register the part in the owner's active-missile list.
* The part then detaches in the logic update `FUN_140033b90` (~`0x140037806`): `vtbl+0x68` removes it from its master, `level->vtbl+0x50` adds it to the world.
* Player input `FUN_14018a530`: code 0x1013 walks the ship's AA list (ship+0x13f0, stride 0x18, entry+8 = part) and launches until one succeeds (one missile per press);
  0x1012 uses the list at ship+0x13d8 with `FUN_14002ff60`. Lists are rebuilt by the stats routine `FUN_14007fcf0` -> `FUN_140071380`.
* Only the **low byte** of the return value is the success flag. The AI calls the launch **every frame** until it succeeds (hundreds of failures per fight).
* A copy of a part is made like the editor does it: `FUN_1401bfd00` copy, `vtbl+0x80`, `FUN_140280840(c,1)`, set position/angle (`FUN_1400521f0`/`FUN_140051850`, world
  coordinates through the master `vtbl+0xe8/+0xe0`), `FUN_140027f90`, `vtbl+0x88`, count=1, blueprint=0, owner ref, then **add to the level node `*(0x147fc6f88)`** (only objects in the tree are updated).

## Map launch of strategic missiles [game]
* Panel `FUN_140273640`: **4 switches** (`MAPMODE_MISSILE_SW`), each bound to a distinct, not-yet-queued missile part of the selected type. A strategic missile (A-100 =
  `MDL_NUKE_03_CONV`) is a single body with two mount slots.
* Queue filler `FUN_140214c40`: one **0x38-byte entry** per switched-on missile in the fleet's vector (fleet +0x538/+0x540/+0x548): `{SmartRef part, SmartRef target, float x,y at +0x30}`.
  A missile with stats +0x168 > 100000 triggers `NUCLEAR_ESCALATION_1`.
* Consumer `FUN_1400eced0(fleet)`, called from the fleet update `FUN_140111ff0` whenever **fleet +0x50c == 0**: takes the LAST entry, creates the map missile (`FUN_140334094(0x308)` +
  `FUN_1400e48a0`), copies the part id into it, kills the part (`vtbl+0x48`), pops the entry, recomputes ship totals, and sets **`fleet+0x50c = 300.0`** (immediate at `0x1400ed598`+6).
  The timer is counted down per frame (~`0x140115cc8`) and also blocks the AI decision `FUN_1400f00c0`: this is why a queued volley goes out one by one.
* AI side: `FUN_1400f00c0(fleet, targetInfo)` decides to fire (cooldown, range 100..9000, per-target salvo caps 1/2/8 at targetInfo+0x84), fills the queue via `FUN_1400fc760`.

## Engagements: map -> battle [game unless marked]
* Loader `FUN_14025afd0(level, bool, bool)` stores the name, sets **`DAT_143a11902 = 1`** (an engagement is pending; blocks a second one in the same pass), then `FUN_1402db350`.
* Four global vectors of smart-refs describe the sides: **A `0x143a158e0`** (ours), **B `0x143a159c0`** (the other side), C `0x143a158b0`, D `0x143a13de8`.
* Observed: `Missile.seria` (a missile threatens our fleet): A=[Escadra], B=[Missile]. `Bombers.seria` (air raid): A=[**MapCraft**, one object carrying the planes], B=[Escadra].
  `CraftsVsMissile.seria` / `CraftsVsCrafts.seria` (planes defending/engaging, set up by `FUN_140117840`) not seen yet.
* Trigger for `Missile.seria` (inside `FUN_140111ff0`): the first missile for which `FUN_1400ec440` is true and sides are opposed wins; the lists are cleared, **that one missile** goes into B,
  nearby friendly fleets into A, the loader is called. A volley of three therefore produced three fights in a row.
* Scenarios are state machines inside the giant `FUN_1402ac970` (branch by `LVL_SCRIPT` name). `SCR_MISSILE` at `0x1402c4baf`; state byte-table `0x1402c7a00`, offsets `0x1402c79e4`.
  State 1 (`0x1402c4dfc`) calls **`FUN_1402d45c0`**: sorts the defender fleet's ships, spawns up to 4 (`FUN_1402672c0`), then reads **only B[0]**: `for i < B[0]+0x248` it creates a
  missile with `EditorParts_DefinePart(0x143a139f0, string at B[0]+0x2b8, level, 1)` at a random offset, then zeroes the count.
* So a salvo fights as one only if the first missile's count is the sum; pushing extra list entries is ignored [game].
* Map-level shooting: `FUN_140111110` (from `FUN_1400f11b0`) prints `MISSILE_INTECEPTED` and downs at most 3 crafts per pass, ~2/3 chance each (`CRAFT_DOWN`, `vtbl+0x210`) [code].

## Refueling [game]
Per frame, inside the fleet update, for a docked fleet (`RSI`), station (`R15`), frame time (`XMM15`):
`amount = min(fleet.capacity(+0x4a0) - fleet.fuel(+0x498), dt * RATE, station.stock(+0x274))`, `added = FUN_1400ea980(fleet, amount)`, `station.stock -= added`.
`RATE` = **200** at a type-4 station (`station+0x258 != 0 && station+0x25c == 4`), **100** otherwise, read by `MULSS` at `0x14011521f` / `0x140115240`; AI fleets use 100 at `0x14011529c`
(no stock accounting). Observed `dt` ~ 11.43 per frame step, so ~1143 fuel per call, 7 calls per ~19.5 ms.
* `FUN_1400ea980(Escadra*, double)` = add fuel to a fleet: spreads the amount over ships in proportion to free tank space (ship +0x1638 current, +0x1640 capacity, doubles; per-ship fill
  `FUN_140060d80`), adds the total to `fleet+0x498` (snaps to an integer within 0.1), returns it. Other callers: fuel from absorbed ships (`FUN_1400f9460`), scenario setup (5,000,000 once),
  shipworks exit (`FUN_1400d2260`), `FUN_1400a6230`, `FUN_1402017a0`, `FUN_140261a20`, `FUN_140290210`.
* `fleet+0x420 m_refuel_timer` / `+0x424 m_refuel_amount` are a delayed delivery (counted down in the fleet update, then delivered); they stayed 0 while refueling at a station.
  `+0x468` = refuel animation flag (`FUN_1400fe8b0`, sounds `refueling_start/loop/stop`); save/load `FUN_1400feb90`. The buy-fuel slider UI (`FUEL_BUY_SLIDER`, `REFUEL_TIME`) is untraced.

## Elevation and firing arcs [game unless marked]
* Solver `FUN_140256a90` sets `m_floor` from `m_floor_type` and neighbours. Bits: `0x01` auto-recompute, `0x02` neighbours must be strictly higher, `0x04`/`0x08` neighbour-count variants,
  `0x10` force floor 3. A part without `0x01`/`0x10` keeps its saved floor. An automatic part rises by 1 when every connection-slot neighbour is at or above it, repeating until stable
  (bumping attached non-socket children). Saved ships contain floors 1-3.
* Arc scan `Body::ScanSectors` `0x140052340`: 360 one-degree rays via `World_RaycastBodies` `0x140239f30`; a hit writes 0 to that degree's `m_sectors` entry. `UpdateEngineCovered`
  `0x14001c4a0` averages the engine cone into `m_mdl_covered`. A body blocks a ray only if it is **not a gun** (category bit 5) **or** `shooterFloor <= otherFloor`
  (+1 if the body's master type is 7): elevation decides who can block whom (guns only block by height).
* Gun arc blocking is restored in 1.163 by highfleet-qol: it detours `FireGun` (inject `0x140032f22`, exit `0x140032ef0`, return `0x140032f29`), reads the gun's 360 `m_sectors`
  (requires stats +0x128 != 0), maps the gun angle relative to the root to a sector and blocks on 0.0.

## Map cruise speed [game]
The ship stats routine `FUN_14007fcf0` computes `powf(TWR - 1, 0.5)` at `0x140080699`: speed = `50 * sqrt(TWR - 1)` m/s in 1.163 (1.151 used `25 * TWR`). The game caches each ship's speed.
