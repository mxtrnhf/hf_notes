# Cluster and mine bomblet lifetime: the spawn function and its call sites (1.163, partial)

Status: **all FOUR call sites and their TTL arguments are read (2026-10-26, see the last section); the older text below says "two" and is superseded there. Nothing run in game.** Tags: legend in `../../README.md`.
Addresses are 1.163 (image base `0x140000000`, the unpacked exe). Origin: roadmap Mod Scope item "adjustable TTL for cluster munitions and mine bomblets".

## The spawn function [code]
`FUN_140032fb0` (`0x140032fb0`-`0x1400337f7`, the function after `FireGun`). Arguments as the decompiler shows them: `(shooter, ?, count, a4, a5, ttl, angle)`. `count` is `param_3`, `ttl` is the **sixth** argument (`param_6`).
* For each of `count` bomblets it allocates `New(0xa40)` + `Body::Body`, `CreateShell_`, and writes `ttl` to three fields: `+0x2c0` (time to live), `+0xf0` and `+0xf4` (desowning time). Other fixed fields: `+0x2c4 = 0.1`, `+0x2b8 = 2` (collisions), `+0x2cc`/`+0x2c8 = 5.0` (health), `+0x2dc = a4`, `+0xe0 = a5`.
* After the loop it creates one smoke/flash body and plays `strides` and `strides_fire` once per bomblet.
* So **one place** sets bomblet lifetime: scaling `param_6` on entry (or the three stores) changes all cluster and mine bomblets. This is the patch site for the roadmap item. [code]; the patch itself is not written or tested.

## The 1.151 original [code]
`Projectile_ExplodeAndCluster(projectile, ?, multiplier, maxCount, ttl)` at 1.151 `0x14002c170`, called only from `creatureLogic` (1.151 `0x1400335b0`). It spawns `min(explosive * multiplier, maxCount)` bomblets, each `New(0xa08)` + `Body::Body`, `CreateShell_`, `is_bullet`, owner = the projectile's owner, `timeToLive = desowningTime = ttl`, `ttlDesolveTime = 0.1`, `collisions = 2`, health 5.0, carrying `explosive / count`. Difficulty scaling: for a player-side owner the "dud" flag chance is `5% * (0.3 on difficulty 0, 0.6 on difficulty 1, 1.0 otherwise)`. 1.163 no longer has the difficulty scaling here (it stores `FUN_1401af7b0(n)` in `+0x3c0`).

## The call sites [code]
Ghidra lists one call (`0x140036c68`), but a second one sits in undefined code just before it: **`0x140036886`**. Both are in the `creatureLogic` region (`0x140033b90`). The `.pdata` xref (`0x1480797d0`) is an exception-table entry, not a call. So at least **two** direct callers exist. Stack slots at the call: `[rsp+0x20]` = 5th arg, **`[rsp+0x28]` = 6th arg (TTL)**, `[rsp+0x30]` = 7th (angle), `[rsp+0x38]` = an 8th argument the decompiler does not show.
| | call `0x140036886` | call `0x140036c68` |
|---|---|---|
| count (`R8D`) | `(int)` of a value from `FUN_14001c7b0(...)` | `(int)(XMM6 / [0x1403524e0])`, `XMM6 = FUN_140048870(creature)` = also stored to `creature +0x2dc` |
| 4th arg (`XMM3`) | `XMM6 = creature[+0x2dc] / count` | constant (`XMM6 / [0x1403524e0]` path) |
| 5th arg `[rsp+0x20]` | `XMM9` | constant at `0x140354820` = `16.0` |
| **6th arg `[rsp+0x28]` = TTL** | **constant at `0x1403546b0` = `0.3`** | **`XMM10`** (value not traced) |
| 7th arg `[rsp+0x30]` (angle) | `XMM9` (0 selects the velocity direction) | a negated float |
| 8th `[rsp+0x38]` | constant `0x140352844` = `1000.0` | constant `0x1403548bc` = `2000.0` |
Reading: the first call (condition `EBX` is a missile-type switch; the code before it tests a distance/health ratio) passes the literal `0.3` as TTL, which is the cluster/mine-like case with short-lived bomblets; the second passes a register. Which ammo or part reaches which call is **not** established. [code for the values, guess for the meaning]
So scaling the sixth argument **inside `FUN_140032fb0`** (one place) still covers both calls.

## Open [not read]
* What `XMM10` holds here. It is callee-saved and `creatureLogic` blocks do not run in address order, so the absence of a writer in the low addresses proves nothing. Candidates: `0x14003b658` (`MOVSS XMM10,[RBX+0x68]` then `MULSS` by `[0x140354810]`), and constant loads at `0x14003fd76`, `0x140040f27`, `0x140042053`, `0x14004232e`, `0x140043753`. Not decided. Only matters for the second call; the first uses the literal `0.3`.
* Whether mine bomblets use this same call site (there is no other caller, so they should).
* Which projectile logic id reaches this branch (cluster missile vs mine); the TTL may differ per ammo.

## Live-test recipe
Breakpoints `0x140036886` and `0x140036c68` (the two calls). Read the sixth argument at `[rsp+0x28]` (float) and `R8D` (bomblet count) at each. Fire a cluster missile and trigger a mine; if both reach this address the TTL values show directly. To test the patch idea, scale the float at `[rsp+0x28]` before the call and watch the bomblets live longer or shorter.

## Update 2026-10-26: four call sites, all TTLs known (ds3-bomblet report, curator re-checked the xrefs and the 1.0f constant) [code]
`get_xrefs_to(0x140032fb0)` gives **four** calls (plus the `.pdata` entry). The "two" above was incomplete; the missing two sit in the logic-160 and logic-150 blocks.

| call | block | TTL (6th arg) | count | note |
|---|---|---|---|---|
| `0x140034269` | logic 160 proximity shell | **0.3** (`0x1403546b0`) | `clamp(explosive*0.25, 5, 15)` | then `explosive = max(explosive/5, 10)`, die |
| `0x140034448` | logic 150 airburst | **1.0** (`0x1403524d8`) | 1 | no vanilla ammo uses 150 |
| `0x140036886` | missile body ids 1/3/4, `EBX != 1` | **0.3** | `clamp(explosive/30, 5, 15)` | the proximity burst (`0 < dist/closing < 0.1`, see [flares-and-missiles.md](flares-and-missiles.md)) |
| `0x140036c68` | missile body ids 1/3/4, fuze type 1 | **1.0** = `XMM10`, the only write is `MOVSS XMM10,[0x1403524d8]` at `0x140036276` (bytes `00 00 80 3f`) | `explosive/100` | `GetMissileFuzeType` (`0x1400488d0`, `Stats+0x180`) |

* So the "untraced `XMM10`" is the constant **1.0 f**, loaded once at the top of the missile block; it is not an ammo field and not computed.
* The ammo table's `+0x16c` ttl (2/3/4/7/30/10/1 s) is the PROJECTILE's own lifetime read by `BulletImpact__`; it never feeds a bomblet TTL.
* Cluster **rockets** use a different spawner, `FUN_14001c890`: TTL = `param_6 * rand(0.5, 1.0)`; `param_6` = **30.0** for logic 130 (NAR122, 220MM, NAR340, 220MM_INC and also `300MM_INC`, which stores logic 130, possibly a data slip) giving 15-30 s, and **2.0** for logic 132 (300MM) giving 1-2 s.
* A mod that wants one knob still scales the sixth argument inside `FUN_140032fb0`; rocket bomblets need a second knob in `FUN_14001c890`'s callers (constants inside the logic-130/132 blocks at `0x140034afd` and `0x140034e01`).
* Which missile design has fuze type 1 (1.0 s) and which takes the 0.3 s branch is design data and was not read [guess: type 1 = mine-like warhead].

## Logic ids 150, 90, 180 (open-questions item 8a) [code, ds3-bomblet]
No compare of `body+0x3c4` or `ammo+0x150` with `0x96` / `0x5a` / `0xb4` exists. `creatureLogic` dispatches by a byte table at `0x140045160` into a jump table at `0x14004512c`: **150 has a block** (index 11, `0x140033e0b`: explodes and spawns one 1.0 s bomblet through call 2); **90 and 180 map to index 16 = the default no-op `0x14004501f`**, so a mod that gives an ammo record logic 90 or 180 gets an inert projectile. Ids with a block but no vanilla ammo: 110, 120, 137, 150, 190, 200, 210 (set by other code); 400 and 550 are special tables.
Per-id behaviour of the vanilla ids (0, 100, 130, 132, 135, 140, 160): see the table in [flares-and-missiles.md](flares-and-missiles.md#per-logic-id-ds3-missile-2026-10-26); the timeout path is one generic routine (`+0x2c0` then vtable `+0x48`) that never reads the id.
