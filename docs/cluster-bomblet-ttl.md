# Cluster and mine bomblet lifetime: the spawn function and its call site (1.163, partial)

Status: **spawn function and the single call site found; the source of the TTL argument at the call site is not traced. Nothing run in game.** Tags as in `../README.md`: **[game]** · **[code]** read from the decompilation · **[guess]** · **[not read]**.
Addresses are 1.163 (image base `0x140000000`, the unpacked exe). Origin: roadmap Mod Scope item "adjustable TTL for cluster munitions and mine bomblets". Earlier working notes: `review-1151-groups.md` group 5 (which said no caller was found).

## The spawn function [code]
`FUN_140032fb0` (`0x140032fb0`-`0x1400337f7`, the function after `FireGun`). Arguments as the decompiler shows them: `(shooter, ?, count, a4, a5, ttl, angle)`. `count` is `param_3`, `ttl` is the **sixth** argument (`param_6`).
* For each of `count` bomblets it allocates `New(0xa40)` + `Body::Body`, `CreateShell_`, and writes `ttl` to three fields: `+0x2c0` (time to live), `+0xf0` and `+0xf4` (desowning time). Other fixed fields: `+0x2c4 = 0.1`, `+0x2b8 = 2` (collisions), `+0x2cc`/`+0x2c8 = 5.0` (health), `+0x2dc = a4`, `+0xe0 = a5`.
* After the loop it creates one smoke/flash body and plays `strides` and `strides_fire` once per bomblet.
* So **one place** sets bomblet lifetime: scaling `param_6` on entry (or the three stores) changes all cluster and mine bomblets. This is the patch site for the roadmap item. [code]; the patch itself is not written or tested.

## The call site [code]
* Only one direct call exists: `0x140036c68`, inside the `creatureLogic` code region (Ghidra shows no function at that exact address; it is a chunk of `creatureLogic` `0x140033b90`). The other xref (`0x1480797d0`) lies in `.pdata` (`148078000`-`14808c1ff`): it is an exception-table entry for the function, not a call. So there is **one** caller. [code]
* Argument setup just before the call (`0x140036bf4`-`0x140036c65`): `R8D = (int)(XMM6 / [0x1403524e0])` is the **count**, where `XMM6` came from `FUN_140048870(creature)` and is also stored to `creature +0x2dc`; stack arg 5 (`[rsp+0x20]`) is the constant at `0x140354820`; **stack arg 6 (`[rsp+0x28]`) is `XMM10`**, i.e. the TTL, loaded by an earlier instruction in `creatureLogic`; stack arg 7 is a negated float; `XMM1` is the constant at `0x14035470c`.

## Open [not read]
* What `XMM10` holds here. It is callee-saved and `creatureLogic` blocks do not run in address order, so the absence of a writer in the low addresses proves nothing. Candidates: `0x14003b658` (`MOVSS XMM10,[RBX+0x68]` then `MULSS` by `[0x140354810]`), and constant loads at `0x14003fd76`, `0x140040f27`, `0x140042053`, `0x14004232e`, `0x140043753`. Not decided.
* Whether mine bomblets use this same call site (there is no other caller, so they should).
* Which projectile logic id reaches this branch (cluster missile vs mine); the TTL may differ per ammo.

## Live-test recipe
Breakpoint `0x140036c68` (the call). Read the sixth argument at `[rsp+0x28]` (float; also in `XMM10`) and `R8D` (bomblet count). Fire a cluster missile and trigger a mine; if both reach this address the TTL values show directly. To test the patch idea, scale the float at `[rsp+0x28]` before the call and watch the bomblets live longer or shorter.
