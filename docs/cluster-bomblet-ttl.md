# Cluster and mine bomblet lifetime: the spawn function and its call site (1.163, partial)

Status: **spawn function and the single call site found; the source of the TTL argument at the call site is not traced. Nothing run in game.** Tags as in `../README.md`: **[game]** · **[code]** read from the decompilation · **[guess]** · **[not read]**.
Addresses are 1.163 (image base `0x140000000`, the unpacked exe). Origin: roadmap Mod Scope item "adjustable TTL for cluster munitions and mine bomblets". Earlier working notes: `review-1151-groups.md` group 5 (which said no caller was found).

## The spawn function [code]
`FUN_140032fb0` (`0x140032fb0`-`0x1400337f7`, the function after `FireGun`). Arguments as the decompiler shows them: `(shooter, ?, count, a4, a5, ttl, angle)`. `count` is `param_3`, `ttl` is the **sixth** argument (`param_6`).
* For each of `count` bomblets it allocates `New(0xa40)` + `Body::Body`, `CreateShell_`, and writes `ttl` to three fields: `+0x2c0` (time to live), `+0xf0` and `+0xf4` (desowning time). Other fixed fields: `+0x2c4 = 0.1`, `+0x2b8 = 2` (collisions), `+0x2cc`/`+0x2c8 = 5.0` (health), `+0x2dc = a4`, `+0xe0 = a5`.
* After the loop it creates one smoke/flash body and plays `strides` and `strides_fire` once per bomblet.
* So **one place** sets bomblet lifetime: scaling `param_6` on entry (or the three stores) changes all cluster and mine bomblets. This is the patch site for the roadmap item. [code]; the patch itself is not written or tested.

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
