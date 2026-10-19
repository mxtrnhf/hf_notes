# Strategic missile -> tactical target assignment (`ConfigureStrategicMissileForTacticalBattle`)

Status: **read in both programs (2026-10-19); no in-game test.** Tags: legend in `../../README.md`. Plus **[KB]** = a statement of an external, AI-written HighFleet knowledge base (not part of this repo), checked here and marked as confirmed or not.
**Every address below names its version.** The two programs reuse the same numbers for different functions (table in section 5), so an address without a version is a bug in these notes.

## 1. What it is
When a strategic (map) missile meets a fleet, the game builds a tactical battle (`Missile.seria`) and spawns the missile bodies. This function is called once per spawned missile body and decides **which ship that missile attacks**.

| | 1.151 | 1.163 |
|---|---|---|
| Function | `0x140241680`, Ghidra name `ConfigureStrategicMissileForTacticalBattle` (1998 bytes) | `0x140263700`, Ghidra name `FUN_140263700` (not in the port table; matched by shape, see below) |
| Caller | `SetupStrategicMissileBattle` (`0x1402aa830`), call at `0x1402ab0f0` | `FUN_1402d45c0`, call at `0x1402d4e80` (SCR_MISSILE state 1, see [map-air-groups.md](map-air-groups.md)); plus one data reference at `0x148084ee8` |

Why these two are the same function **[code]**: the same overall call pattern (`CopyEscadraName`, `New`, `SetLink`, a descending merge sort), the same two hook-site instruction sequences (section 3), and every field offset moved by the amount the port table predicts (section 4). The callers are the same function too **[code, 2026-10-19]**: 1.151 `SetupStrategicMissileBattle` `0x1402aa830` and 1.163 `FUN_1402d45c0` are both **2390 bytes** with the same call list (4x `Link_ConstructFromBody`, 4x `Link_CopyConstructor`, 10x link destructor, `DefinePart`, `safeSetBodyPosition`, `cosf`, `Get_Profile` twice, one call to this function, ...). It is not in the port table yet.

## 2. What it does (1.163, decompiled)
Arguments: `param_1` = the tactical missile body (a Creature) just created, `param_2` = the **strategic Missile object it came from** (the map missile whose count `+0x248` drives the spawn loop in `FUN_1402d45c0`, lines `lVar28 = [[0x143a159c0]+8]` ... `FUN_140263700(newBody, lVar28)`) **[code, 2026-10-19]**. The names "tactical missile" / "aimed creature" are the KB's **[KB]**.

1. Copy the name at `param_1+0x190` and test whether its last 5 characters are `_CONV` (string at 1.163 `0x14035fc64`).
2. Write the creature's **logic id** `param_1+0x3c4` (see [combat-missile-launch.md](combat-missile-launch.md): `+0x3c4` is the logic id) = **1 for `_CONV`, 10 for anything else**, set `+0x3c8 = 1`, and set the link `param_1+0x4a8` = `param_2` (non-`_CONV`) or null (`_CONV`) **[code]**. What logic 1 and logic 10 do is not read here.
3. A small test on `param_2` (1.163 `0x1400f8e00`, Ghidra name `rep_1400f36b0_..._sqrtf`, a **wrong label**): true when the squared distance between the points `(+0x25c,+0x260)` and `(+0x150,+0x154)` is below `100.0^2`, i.e. distance < 100 **[code]**. What the two points are is unknown.
   * **False (distance >= 100):** simple case. Logic id 10, link `+0x4a8 = param_2`, `param_1+0x1c0 |= 0x15`, **done: no ship is picked here**.
   * **True:** continue below, if the global creature list (1.163 `DAT_143faa5d8` begin / `DAT_143faa5e0` end, entries of 0x18 bytes, the creature pointer at entry+8) is not empty.
4. Virtual call on `param_2` (vtable `+0x178`) returns a float `v`. **`v > 0`: Path A. Otherwise: Path B.** The KB calls this call `creatureAimed__` **[KB]**.
5. **Path A (sorted):** walk the global list; keep a ship if `FUN_140073450(ship)` is true: the ship is named `Titan`, **or** the float at `ship+0x1604` is not 0. It is the 1.163 twin of 1.151 `hasTWRStat?` (`0x14006f960`, 24 bytes: "return `ship+0x1558 != 0.0`", the TWR stat), shifted +0xac like the combat value, **plus a `Titan` exception that 1.151 does not have** **[code]**. For each kept ship set a sort key at `ship+0xF8` = **0 if `ship+0xc19` is set, else `ship+0x15f8` (combat value)**. Sort the kept ships by key, **descending** (1.163 `FUN_1400a1000`; 1.151 name `MergeSortObjectListByScratchKeyDescending` at `0x14009d310`). The first one becomes the target. So: **highest combat value first, and flagged ships last** (the flag is what our notes call the prize flag, [battle-ally.md](battle-ally.md)) **[code]**.
6. **Path B (random):** pick a random index in `[0, count-1]` (HGE interface call `+0x108` in 1.163, `+0x100` in 1.151) over the **whole** global list, no filter at all (own side, prize ships and all) **[code]**.
7. Both paths end at one instruction pair: `LEA RCX,[R13+0x490]` then `CALL SetLink` (1.163 `0x140263bc1`/`0x140263bc8`), i.e. **the chosen target is the link at `param_1+0x490`** (1.151: `+0x480`).

Consequence **[guess from the code, not tested]**: in Path A every missile of a salvo gets the same sort, so they all pick the same top-CV ship unless that ship has gone. Path B spreads them at random. Edge case read from the decompile **[code reading, not traced]**: if Path A keeps no ship, the code still reads the first entry of its temporary list, which is then the list's own head node (allocated with `New(0x18)`, payload never written), and passes that value to `SetLink`.

## 3. Hook sites (instruction boundaries read in both programs)
The value that ends up in `RDX` is the target object passed to `SetLink`.

| | 1.163 | 1.151 |
|---|---|---|
| Path A site | `0x140263bba`: `MOV RAX,[R14]` (3 bytes), `MOV RDX,[RAX+0x10]` (4 bytes); 7 bytes, ends exactly at the convergence point | `0x140241d7a`, same two instructions |
| Path B site | `0x1402639e3`: `MOVSXD RCX,EAX` (3), `LEA RDX,[RCX+RCX*3]` (4), `MOV RAX,[0x143faa5d8]` (7) = 14 bytes, then `MOV RDX,[RAX+RDX*8+8]` (5) at `0x1402639f1` and `JMP 0x140263bc1` (5) | `0x140241b9f`, same, list `[0x143ed10d8]` |
| Convergence | `0x140263bc1` `LEA RCX,[R13+0x490]`; `0x140263bc8` `CALL SetLink` (`0x140194de0`) | `0x140241d81` `LEA RCX,[R14+0x480]`; `0x140241d88` `CALL SetLink` (`0x140187120`) |

Per-ship salvo distribution would replace the chosen `RDX` at one of the two Path sites **[idea, not built]**.

## 4. Version differences inside this function
| What | 1.151 | 1.163 | Shift |
|---|---|---|---|
| chosen-target link | `+0x480` | `+0x490` | +0x10 |
| second link (`non-_CONV` target) | `+0x498` | `+0x4a8` | +0x10 |
| prize / non-priority flag | `+0xbb1` | `+0xc19` | +0x68 |
| combat value (`m_tele_combatvalue`) | `+0x154c` | `+0x15f8` | +0xac |
| global creature list | `0x143ed10d8` | `0x143faa5d8` | n/a |
| "has a TWR stat" test used by Path A | `hasTWRStat?` `0x14006f960`: `ship+0x1558 != 0` | `FUN_140073450`: name is `Titan` **or** `ship+0x1604 != 0` | +0xac, plus a new `Titan` rule |
| extra work | calls `Get_Profile` twice, `memcmp` twice, `GetPartIndex` twice, `CopyString` twice, `displayYellowLable?` | **none of these** (call list read in 1.163) | block removed or moved |

The last row matters: the 1.151 function contains a block that reads the profile and a part index around the `_CONV` test (looks like an escalation-dependent part swap **[guess]**); the 1.163 function has no such block. A claim that "1.163 strips `_CONV` when escalation is non-zero inside this function" is **not supported**. Where that logic went in 1.163 is open. (The `_CONV` suffix test itself was read in 1.163 only; the 1.151 version was not compared line by line.)

## 5. Same address, different function (verified 2026-10-19 by opening both programs)
Do not carry an address across versions without the port table ([../data/port-1151-1163-functions.tsv](../data/port-1151-1163-functions.tsv), [../porting-1151-1163.md](../porting-1151-1163.md)).

| Address | In 1.151 | In 1.163 |
|---|---|---|
| `0x14010c3a0` | `UpdateStrategicFleet` | inside `displayLables` |
| `0x140111ff0` | inside `UpdateMapAircraftGroup` | `UpdateStrategicFleet` |
| `0x140113710` | strategic Missile per-tick function | inside `UpdateStrategicFleet` |
| `0x1401195d0` | another function (Ghidra `..._sqrtf`) | strategic Missile per-tick function (1.151 twin: `0x140113710`) |
| `0x140263700` | inside an `atan2f` helper | `FUN_140263700` (this page) |
| `0x140032fa0` | `FireGun` | inside `FireGun` (starts at `0x140032e60`) |
| `0x1402ab190` | entry of a function Ghidra labels `rep_..._sinf` | inside `rep_140287200_New` (starts at `0x1402ab180`) |
| `0x1402077c0` | `LoadDialogue` | `FUN_1402077c0` (strike-group composer) |
| `0x1401a94d0` | inside `selectPlayerStrikeGroups?` (starts `0x1401a9070`) | `initGame` (the 1.151 `initGame` is `0x140199bf0`, 15284 bytes) |
| `0x140032f60` | not code (no instruction, no function) | inside `FireGun` |

## 6. The external KB on this function
Checked against the two programs: **confirmed** the two hook sites and the convergence point (both versions), the `_CONV` suffix test, the two-path structure, and all four offset shifts; **wrong**: its "call site `0x1402D4BA3`" (the only direct call in 1.163 is `0x1402d4e80`), and its address `0x1400ECF80` for `initProfileMissiles?` (an interior address; the entry is 1.163 `0x1400eced0`). Not checked: its claim that the flag is set on trade-convoy **escorts**; our notes put it on the prize ship itself ([battle-ally.md](battle-ally.md)), which fits this code (flagged ships sorted last, so missiles go for the escorts).

## 7. Open
* What the two points in step 3 are (for a map Missile: probably its current and its target position **[guess]**), and what `v` (vtable `+0x178` of the map Missile) means.
* Which side takes Path A and which Path B in play (KB: player missiles A, AI missiles B **[KB, untested]**).
* What logic ids 1 and 10 do to the missile after step 2.
* Whether the 1.163 `Get_Profile`/part-swap logic exists elsewhere (section 4).
