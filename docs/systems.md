# How the game works (launching, engagements, refueling)

Addresses are for Steam 1.163. Tags: legend in `../README.md`.

## Combat missile launch
Two separate launch paths exist. Full evidence and the ruled-out sites: [findings/combat-missile-launch.md](findings/combat-missile-launch.md).

**Anti-ship missiles (Zenith, stats index 130) [game for the AI path, code for the player key]**
* `FUN_14002ff60(launcher)` launches them: needs `launcher+0x848 == 0`, an owner (+0xb8) with a target (`owner+0xb00`, not an evac pod), then sets target/owner refs at `+0x490/+0x4a8`, `+0x3c8 = 1`, and registers the part in the owner's active-missile list. The AI tick `FUN_140062f90` calls it at `0x140065edb` over the ship's launch list `+0x13d8`, about a 1% roll per tick, then sets the ship cooldown `+0xd60` = 2.0 s. Whether aircraft/hangars also use it is not established.
* Player input `FUN_14018a530`: code 0x1012 uses the list at ship+0x13d8 with `FUN_14002ff60` [code, player path not hooked; the detach probe saw the player's Zenith launches]. Lists are rebuilt by the stats routine `FUN_14007fcf0` -> `FUN_140071380`.
* The part then detaches in the logic update `FUN_140033b90`: the call at `0x140037809` (`call 0x140048fc0`, RCX = the part) is the probe point [game]; disassembled [code]: `0x140037806 MOV RCX,RSI`, `0x140037809 CALL 0x140048fc0`, `0x140037811..0x140037817 CALL [RDX+0x68]` (`vtbl+0x68`, remove from its master), then `level->vtbl+0x50` adds it to the world (the `0x147fc6f88` level node is loaded at `0x14003781a`).

**Anti-air launchers (interceptors, for example S-4 Triumph) [code, not observed for Zenith]**
* `FUN_14002e590(part)` (player) / `FUN_14002e3a0(part, target)` (AI) need a target (`FUN_14006c0e0`/`FUN_14006c440`), the owner (+0xb8), the owner's cooldown (+0xad4) and in-flight limit (owner+0x17b0). They store target/owner refs at part+0x490/+0x4a8, set `+0x3c8`, start a timer, register the part in the owner's active-missile list. They were hooked at their AI call sites and never ran in three battles that included Zenith launches by both sides; multicharge's Triumph results ([mods/multicharge.md](mods/multicharge.md)) fit the AA reading [guess].
* Player input `FUN_14018a530`: code 0x1013 walks the ship's second list (ship+0x13f0, stride 0x18, entry+8 = part) and launches until one succeeds (one missile per press) [code].
* The multicharge page reports that the AI retries every frame (hundreds of failures per fight). That can only hold for ships with AA launchers and a missile or aircraft target: the AI call sites of this pair never ran in the three Zenith battles. It does not describe Zenith, which is rate-limited by the 1% roll and the 2.0 s cooldown [guess].

* Only the **low byte** of the return value is the success flag (both paths).
* A copy of a part is made like the editor does it: `FUN_1401bfd00` copy, `vtbl+0x80`, `FUN_140280840(c,1)`, set position/angle (`FUN_1400521f0`/`FUN_140051850`, world
  coordinates through the master `vtbl+0xe8/+0xe0`), `FUN_140027f90`, `vtbl+0x88`, count=1, blueprint=0, owner ref, then **add to the level node `*(0x147fc6f88)`** (only objects in the tree are updated).

## Map launch of strategic missiles [game]
The Triumph (AA; needs a fire-control radar like the R-9 Sprint `MDL_MISSILE_03`) is **combat only**; the A-100 is a **map-only** strategic missile.
* Panel `FUN_140273640`: **4 switches** (`MAPMODE_MISSILE_SW`), each bound to a distinct, not-yet-queued missile part of the selected type. `MAPMODE_MISSILE_FIRE` is the fire button. A strategic missile (A-100 =
  `MDL_NUKE_03_CONV`) is a single body with two mount slots.
* Queue filler `FUN_140214c40`: one **0x38-byte entry** per switched-on missile in the fleet's vector (fleet +0x538/+0x540/+0x548): `{SmartRef part, SmartRef target, float x,y at +0x30}`.
  A missile with stats +0x168 > 100000 triggers `NUCLEAR_ESCALATION_1` [code]: only while the `ESCALTION_WARNING` trigger is set (the game's own spelling) and no other block applies; that press then shows the dialogue, clears the trigger and queues **nothing**, and the next press queues normally. The target of an entry (global `DAT_143a13c68`) may be a fleet (`0x147`), a Missile or a MapCraft (mask tests) [code].
* Consumer `FUN_1400eced0(fleet)`, called from the fleet update `FUN_140111ff0` whenever **fleet +0x50c == 0**: takes the LAST entry (a dead or null part is popped and skipped first [code]), creates the map missile (`FUN_140334094(0x308)` +
  `FUN_1400e48a0`), copies the part id into it, kills the part (`vtbl+0x48`), pops the entry, recomputes ship totals, and sets **`fleet+0x50c = 300.0`** (immediate at `0x1400ed598`+6).
  The timer is counted down per frame (~`0x140115cc8`) and also blocks the AI decision `FUN_1400f00c0`: this is why a queued volley goes out one by one.
* AI side: `FUN_1400f00c0(fleet, targetInfo)` decides to fire (cooldown, range 100..9000, per-target salvo caps 1/2/8 at targetInfo+0x84), fills the queue via `FUN_1400fc760`.

## Engagements: map -> battle [game unless marked]
* Loader `FUN_14025afd0(level, bool, bool)` stores the name (global `DAT_1403c1390`), sets **`DAT_143a11902 = 1`** (an engagement is pending; blocks a second one in the same pass), then `FUN_1402db350`.
* Four global vectors of smart-refs describe the sides: **A `0x143a158e0`** (ours), **B `0x143a159c0`** (the other side), C `0x143a158b0`, D `0x143a13de8`.
* Observed: `Missile.seria` (a missile threatens our fleet): A=[Escadra], B=[Missile]. `Bombers.seria` (air raid): A=[**MapCraft**, one object carrying the planes], B=[Escadra].
  `CraftsVsMissile.seria` / `CraftsVsCrafts.seria` are started from the map aircraft group update `FUN_140117840` (two `SetLevelSeriaToLoad_` calls, side lists built from objects within 15.0); `Combat.seria` (fleet against fleet) is started from the fleet update beside `Missile` and `Bombers` [code, [findings/map-air-groups.md](findings/map-air-groups.md)]. None of the craft flows observed in game yet.
* Trigger for `Missile.seria` (inside `FUN_140111ff0`): the first missile for which `FUN_1400ec440` is true and sides are opposed wins; the lists are cleared, **that one missile** goes into B,
  nearby friendly fleets into A, the loader is called. A volley of three therefore produced three fights in a row.
* Scenarios are state machines inside the giant `FUN_1402ac970` (branch by `LVL_SCRIPT` name). `SCR_MISSILE` at `0x1402c4baf`; state byte-table `0x1402c7a00`, offsets `0x1402c79e4`.
  State 1 (`0x1402c4dfc`) calls **`FUN_1402d45c0`**: sorts the defender fleet's ships, spawns up to 4 (`FUN_1402672c0`), then reads **only B[0]**: `for i < B[0]+0x248` it creates a
  missile with `EditorParts_DefinePart(0x143a139f0, string at B[0]+0x2b8, level, 1)` at a random offset, then zeroes the count.
* So a salvo fights as one only if the first missile's count is the sum; pushing extra list entries is ignored [game].
* Map-level shooting: `FUN_140111110` (from `FUN_1400f11b0`) first rolls **75%** to kill a missile aimed at the same target (`MISSILE_INTECEPTED`, sound `radio_kill_06` on `MAPMODE_RADIO_HANDSET`), then downs at most 3 crafts per pass with a **66%** roll each (`CRAFT_DOWN`, `vtbl+0x210`) [code]. Both probabilities are literal `Random_Float` compares, unchanged since 1.151.

## Refueling [game]
Per frame, inside the fleet update, for a docked fleet (`RSI`), station (`R15`), frame time (`XMM15`):
`amount = min(fleet.capacity(+0x4a0) - fleet.fuel(+0x498), dt * RATE, station.stock(+0x274))`, `added = FUN_1400ea980(fleet, amount)`, `station.stock -= added`.
`RATE` = **200** at a type-4 station (`station+0x258 != 0 && station+0x25c == 4`), **100** otherwise, read by `MULSS` at `0x14011521f` / `0x140115240`; AI fleets use 100 at `0x14011529c`
(no stock accounting). Observed `dt` ~ 11.43 per frame step, so ~1143 fuel per call, 7 calls per ~19.5 ms.
* `FUN_1400ea980(Escadra*, double)` = add fuel to a fleet: spreads the amount over ships in proportion to free tank space (ship +0x1638 current, +0x1640 capacity, doubles; per-ship fill
  `FUN_140060d80`), adds the total to `fleet+0x498` (snaps to an integer within 0.1), returns it. Other callers: fuel from absorbed ships (`FUN_1400f9460`), scenario setup (5,000,000 once),
  shipworks exit (`FUN_1400d2260`), `FUN_1400a6230`, `FUN_1402017a0`, `FUN_140261a20`, `FUN_140290210`.
* `fleet+0x420 m_refuel_timer` / `+0x424 m_refuel_amount` are a delayed delivery (counted down in the fleet update, then delivered); they stayed 0 while refueling at a station.
  `+0x468` = refuel animation flag (`FUN_1400fe8b0`, sounds `refueling_start/loop/stop`); save/load `FUN_1400feb90`. The buy-fuel slider (`FUEL_BUY_SLIDER`) and the `MAPMODE_MISSION_FULLTANK` / `HALFTANK` branches are traced in [findings/click-func.md](rendering/click-func.md#decompiled-branches-v1163); `REFUEL_TIME` is untraced.

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
The ship stats routine `FUN_14007fcf0` computes `powf(TWR - 1, 0.5)` at `0x140080699`: speed = `50 * sqrt(TWR - 1)` m/s in 1.163 (internal unit; the UI and `speed.log` show km/h = m/s x 3.6) (1.151 used `25 * TWR`). The game caches each ship's speed.

## Strategic AI: aircraft launch, intercepts, end game [code]
* **Aircraft launch:** `TryLaunchAiAircraftGroup` (`0x1400ef910`) sends all (or, above 10 aircraft, a coin-flip half) of an AI fleet's aircraft in one group when the player is within `0.45 x range`; cooldown 1800. Conditions, patch sites: [findings/ai-aircraft-launch.md](findings/ai/ai-aircraft-launch.md).
* **Map aircraft groups** (`MapCraft`, 0x340): creation, per-frame update (range left is spent as fuel, return state, engagement triggers), intercept rolls and the fleet update's level loads: [findings/map-air-groups.md](findings/map-air-groups.md).
* **End game:** `FUN_140261a20` (1.151 `spawnEndgameShips_`) is the scripted collapse (strike groups against Khiva, escalation, `Profile.endWar`); after it runs `GetPartPrice` returns 0. Phases: [findings/end-game.md](findings/end-game.md); the crash cause: [findings/end-game.md#the-khiva-end-game-crash-unguarded-list-writes-1163-probable-cause](findings/khiva-crash.md).
* **Part prices:** `GetPartPrice` returns 0 when `Profile.endWar` is set or the part's category has bit 6 (`0x40`, block/bridge); otherwise the stats `price`. This is why bridges and blocks are free in the editor [code, 1.151 read].
* **Sensors:** radar, tracking, ELINT and IRST combine parts by per-sector maximum; only jammers sum. [findings/sensors-and-crew.md](findings/sensors-and-crew.md).

## Firing, tactical AI, point defence, flares [code]
* **Firing chain:** AI weapon controller `FUN_14007a8d0` (and the player's input path) -> `FireGuns` `0x1400559e0` -> `FireGun` `0x140032e60` -> `FireShell` `0x1400300d0` (dispatch on the `Ammo` entry's `index`) -> `Body::BulletImpact__` (cannon shells, all with 1 HP). [findings/firing-and-shells.md](findings/firing-and-shells.md); ammo table: [findings/ammo-1151-vs-1163.md](findings/ammo-1151-vs-1163.md). Weapon fields of the Body: `+0x858` reserve rounds (int), `+0x860` loaded rounds (float) [structures.md](structures.md).
* **Tactical AI:** per-ship tick `FUN_140062f90` (stand-off `0.35 x reach`, orbit, ally separation, launch caps; the Zenith launch is in [findings/combat-missile-launch.md](findings/combat-missile-launch.md)), weapon controller `FUN_14007a8d0` (ammo choice, close-range cutoff `radius + radius + 30`): [findings/ai-tick-patch-sites.md](findings/ai/ai-tick-patch-sites.md).
* **Active protection (KAZ):** `FUN_14002f480` is the close-in burst of the "strides" sprites: it picks an incoming projectile within 60/120 units and 45 degrees, spends one count and damages it with the target's own explosive power; stats categories `0x4000`, `0x8000000`, `0x200000` are excluded. Called from `FUN_14007eb50`. Matches the KAZ category (bit 25) [guess] and `ITEM_KAZ_AMMO` (1.163).
* **Flares:** the player's input path sets Creature `+0xbc0`, `FUN_14007eb50` then calls the release `FUN_14002eed0` on the `+0x1408` launcher list; nothing sets the flag for AI ships: [findings/ai-flares.md](findings/ai/ai-flares.md). The proximity-fuse crash is not located: [findings/flare-crash-hunt.md](findings/flare-crash-hunt.md).
* **Bomblets:** cluster and mine bomblets are spawned by `FUN_140032fb0` (TTL is its sixth argument): [findings/cluster-bomblet-ttl.md](findings/cluster-bomblet-ttl.md).

## Ground defense (`AADefense`, class `0x80007`) [code, 1.151 read]
1.151 `createGroundDefenseCreatures__` (`0x140004950`) builds an `AADefense` object (logdot: "This 0x80007 only shows up for ground defense creatures") with a linked `Runner` creature and `MDL_WHEEL_01` wheels. `AADefense::FireMissile__` (`0x140005370`) is its state machine: it needs one part each of categories `0x10` (ammo), `0x20` (gun) and `0x800` (generator/quarters) plus at least two wheels, then flies a `MDL_MISSILE_01` (TTL 60.0, layer 7) at the nearest hostile within `500.0` when its reload timer (`+0x12c`, base `30.0` at `+0x128`) is zero. The 1.163 comment "Ground defense creatures?" on `FUN_1400e4530` is wrong: that constructor builds the MapCraft (0x340).

## Sounds seen in the map code [code, 1.151 names]
Fleet update: `mission_end` (radio, at most once per 3 s), `turbine_01`, `pump`, `pump_on`, `pump_off`, `engine_rocket_03`, `engine_ignit_int`, `env_horn`, `env_ship_landing`. Intercept: `radio_kill_06`. Refuel: `refueling_start/loop/stop`. To play any of these from a mod: [sound.md](sound.md).
