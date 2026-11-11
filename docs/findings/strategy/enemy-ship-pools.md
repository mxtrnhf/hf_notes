# Enemy ship pools: where SG / TG / general enemies draw their hulls from (1.163)

Program: `Highfleet.exe.unpacked.exe` v1.163, image base `0x140000000`.
Researched 2026-11-11 from the live Ghidra program (decompiles + call-site
disassembly). Not validated in game. Tags: [code].

## Short answer

There is no data-file pool. All three enemy ship pools are **hard-coded name
lists inside code**, each entry paired with the design's strength scalar
(design record `+0x15f8`, resolved by name through the global design/property
library `newNode_`, virtual `+0xb8`; helper `retCreature154c?`
`0x140219980`). Three independent pool systems feed different enemy paths:

| Pool | Function | Drawn by | Feeds |
|---|---|---|---|
| 5 strength-tables (ids 0-4) | `somethingSpawnShips` `0x140203b80` | strength-budget roll loop inside it | city garrisons, event escadras, group-6 fleets, endgame garrisons |
| Weighted hull catalogue | `Endgame_BuildEscadra` `0x1402077c0` | budget roll loop inside it | roaming Strike Groups (campaign start + endgame) |
| 46-name price-bucket catalogue | `Fleet_GenerateShipNames` `0x140205ae0` | `Fleet_AddNamedShipToPool` `0x1401a7a40` + `Fleet_SelectShipsForBudget` `0x140206060` | general enemies in scenario slots |

## 1. `somethingSpawnShips(out, strength, poolId, chanceA, chanceB, flag)`

Builds a `CVec` of 0x28-byte `(EscadraName name, float strength)` pairs, then
rolls random entries (up to 10 retries keeping the best-fitting composition)
until the accumulated strength reaches `strength`, and copies the winning
name list into `out`. Post-roll extras: `chanceA` adds `Longbow`; `chanceB`
adds `Tarantul`, `Hound`, 50% `Eagle` and 50% `Tarantul MRL`.

Pool ids (`poolId`, verified at every call site's `R8D`):

* **Pool 0** — `{Courageous, Slogger, Navarin, Sarma, ...}` + a second
  tier `{Archangel, Fearsome, Flower, Gladiator, Gladiator MRL, Intrepid,
  Nimrod, Paladin Mk2, Sarma}` (two different push sequences; entries priced
  via direct design-library lookups, not `retCreature154c?`).
* **Pool 1** — `{Kormoran, Negev, Nomad, Nomad Mk2}` (no live caller found;
  only reachable if `Prologue_SpawnEventEscadra` param_3 is non-zero, and every
  call site passes 0 — dead in 1.163 as far as seen).
* **Pool 2** (27 names) — `{Yars, Yars Mk2, Mockingbird, Skylark, Tanker,
  Rook, ... Navarin, Negev, Paladin Mk2, Scarab, Triumphant, Voskhod, Wasp,
  Longbow, Jaguar, Gepard, Gladiator, Intrepid, Kormoran, Lightning, Meteor
  Mk3, Archangel, Egida Mk2, Fatman, Fearsome, Fenek, Flower}`.
* **Pool 3** (22 names) — `{Fatman, Fearsome, Fenek, Fenek Mk2, Flower,
  Gepard, Gladiator, Intrepid, Lightning, Lightning Mk3, Locust, Meteor Mk3,
  Mockingbird, Navarin, Paladin Mk2, Rook, Scarab, Skylark, Voskhod,
  Voskhod X2, Wasp, Wanderer, Yars}` (no live caller found — likely dead).
* **Pool 4** (14 names) — `{Archangel, Fatman, Fearsome, Fenek, Gepard,
  Gladiator, Intrepid, Kormoran, Negev, Paladin Mk2, Scarab, Tanker, Voskhod,
  Wasp}`.

Callers (all three, `R8D` verified):

| Caller | Site | pool | strength |
|---|---|---|---|
| `Prologue_SpawnEventEscadra` `0x1402038e0` (forwards its param_3) | 4 sites in `restOfEventsPrologueAntIsaiah` `0x14028de70` | 0 | campaign values (city/event strength, e.g. `5000.0 / (30|20)` near Khiva) |
| `Prologue_SpawnEventGroups` `0x1402a7f60` (group-6 creatures) | `0x1402a8342` | 2 | `creature+0x248 / 20` |
| endgame `spawnEndgameShips?` `0x140261a20` (city garrisons) | `0x140262bda` | 4 | `city strength / (20 or 50)` (city type `+0x258 == 6` selects the divisor) |

## 2. `Endgame_BuildEscadra` (the Strike Group composer) `0x1402077c0`

Builds the big roaming invasion fleets (the campaign-start ring of six near
`restOfEventsPrologueAntIsaiah`'s city loop, and the endgame waves). Catalogue:
`Borey` (seeded twice), plus `Kormoran`, `Negev`, `Borey`; if profile `+0x165`
is set also `Nomad Mk2`, `Nomad`, `Gryphon`, `Gryphon` (second copy). First
ship = cheapest catalogue hull at most half the budget; then random draws
against the budget (same 10-retry shape). Extras: probability-scaled
`Tarantul ARM`, a 1..2 draw of `Wasp` vs `Longbow`, and `Typhon` when
param_5 is set. Names go straight into `Fleet_CreateEscadraFromShips`.

## 3. `Fleet_GenerateShipNames(out, strength, bucket1..5 flags)` `0x140205ae0`

The general-enemy pool: 46 hard-coded vanilla hull names pushed through
`Fleet_AddNamedShipToPool` (registry price `+0x15f8`), Fisher-Yates shuffled
with `rand()`, then `Fleet_SelectShipsForBudget` picks names until the budget
(+20% slack, same best-of-10 shape). Buckets by price: `<=15`, `<=25`, `<=40`,
`<=75`, `>75`.

Drawn by `Fleet_CreateRandomEscadra` `0x1401a7120` (five times, once per
bucket, then `Fleet_CreateEscadraFromShips`, fill-up to a minimum, MT19937
shuffle seeded `0x1571`). Its only caller is
`Fleet_CreateRandomEscadraForSlot(slot)` `0x1401c2ba0`, slot presets 1-16
(e.g. slot 1: 15 cheap; slot 9: 0/50/120/150 counts; slot 16: 0/0/0/375/600)
and an id-derived budget for ids > 16 (`(id*120-920)` split 50/40/10).

`Fleet_CreateRandomEscadraForSlot` is called from the unnamed SCR_MAP-flow
block at `0x1402c3fa2` with **slot id = Profile+0x5dc counter** (incremented
at the call site, byte-verified) — the escalating enemy response fleets — and
from `Scene_ResetGlobalLinks` `0x14028db90` (`0x14028dd3f`).

## Fleet choke point

All of the above hand a `CVec<EscadraName>` (0x20-byte strings) to
`Fleet_CreateEscadraFromShips(names, type, arg, pos)` `0x1401c7060`, the
common constructor path for fleets built from name lists. It does not consult
any pool itself; names must exist in the design library (lookups return 0 for
unknown names and the strength contribution collapses to 0, but an unknown
name still flows into the fleet vector — unverified what happens downstream).
Entry bytes (16, for version guards):

| function | first 16 bytes |
|---|---|
| `0x1401c7060` | `48 89 5c 24 10 48 89 6c 24 18 48 89 74 24 20 57` |
| `0x1401a7a40` | `48 89 5c 24 18 57 48 83 ec 60 0f 29 74 24 50 48` |
| `0x140205ae0` | `48 8b c4 48 89 58 10 44 88 48 20 44 88 40 18 48` |
| `0x140203b80` | `48 8b c4 48 89 58 10 48 89 70 18 48 89 78 20 55` |
| `0x1402077c0` | `48 8b c4 48 89 58 08 55 56 57 41 54 41 55 41 56` |

## Where the designs come from (2026-11-12 update)

The name lookups all go through the `LIB_SHIPS` library node stored at global
`0x143a13a70` (Ghidra's `newNode_`; `retCreature154c?` `0x140219980` reads
exactly this global and calls the node's virtual `+0xb8` name lookup). The
node is created and named `"LIB_SHIPS"` inside `PreLoadLibraries_`
(`0x140233710`, site `0x1402347f7`: `MOV [0x143a13a70],RAX`, then
`CopyString(node+0xc8,"LIB_SHIPS")`), which then enumerates
**`Objects/Designs`** (`Profile_EnumerateSeriaFiles` `0x14021a2d0`, called
with `"Objects/Designs"` at `0x14023483c`) and `LoadSeriaFile`s every
`.seria` in it.

Consequences:

* A pool name is valid exactly when `Objects/Designs/<Name>.seria` exists;
  dropping a design there makes it usable in pools immediately.
* `Ships/` is NOT the source. Its references are the editor save/load paths
  (`Editor_LoadSelectedSeria` `0x1400d30e8`, `loadShipBackups?`
  `0x14023cd52`, shipworks `ClickFunc` dialogs) and the game rewrites it
  (backups to `Ships_backup/` on a `CORE_LAST_LOADED_VERSION` bump).
* `ShipDesign_EnumerateDesignFiles` (`0x140212850`) scans `Objects/Designs`
  AND `Ships` with `FindFirstFileA`, but only to build UI name lists; it is
  not the library loader.

## Mod angle (PoC proposal, not implemented)

* **Generic removal/addition everywhere**: wrapper detour on
  `Fleet_CreateEscadraFromShips` — param_1 is the name vector; filter out
  blacklisted names, append configured names, then call the trampoline.
  Covers pools 1-3 in one hook.
* **Pool membership (general enemies)**: wrapper detour on
  `Fleet_AddNamedShipToPool(ctx, name)` — blacklist entries by returning
  early; add entries by re-invoking the trampoline with extra names when the
  last vanilla name (`Sevastopol`) passes through. The ctx pointer is a
  parameter, so the trampoline can be called repeatedly from the detour.
* **Pool 1 + SG catalogue**: entry wrappers around `somethingSpawnShips`
  (`R8D` = pool id) and `Endgame_BuildEscadra` post-processing their output
  vectors.
* Names are resolved through the design library, so custom/mod designs work
  as pool entries if registered there; strengths are read at `+0x15f8` at
  pool-build time, so a changed stats record changes draw weights without
  touching the pool code.

## Open

* Pools 1 and 3 of `somethingSpawnShips`: no caller passes those ids in
  1.163 (all four `Prologue_SpawnEventEscadra` sites pass 0; only the
  `param_3` register forward could select them). Possibly leftover from
  1.151 difficulty variants.
* The exact in-game trigger behind the `0x1402c3e70`-`0x1402c3fa2` block
  (Profile+0x5dc counter semantics, called "escalation response" here from
  the counter-slot link) was not traced beyond the call site.
* Whether unknown names flowing into `Fleet_CreateEscadraFromShips` crash or
  are skipped downstream is unverified.
