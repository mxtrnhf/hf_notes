# Cluster and mine bomblet lifetime: the spawn function and its call site (1.163, partial)

Status: **spawn function and the single call site found; the source of the TTL argument at the call site is not traced. Nothing run in game.** Tags as in `../README.md`: **[game]** · **[code]** read from the decompilation · **[guess]** · **[not read]**.
Addresses are 1.163 (image base `0x140000000`, the unpacked exe). Origin: roadmap Mod Scope item "adjustable TTL for cluster munitions and mine bomblets". Earlier working notes: `review-1151-groups.md` group 5 (which said no caller was found).

## The spawn function [code]
`FUN_140032fb0` (`0x140032fb0`-`0x1400337f7`, the function after `FireGun`). Arguments as the decompiler shows them: `(shooter, ?, count, a4, a5, ttl, angle)`. `count` is `param_3`, `ttl` is the **sixth** argument (`param_6`).
* For each of `count` bomblets it allocates `New(0xa40)` + `Body::Body`, `CreateShell_`, and writes `ttl` to three fields: `+0x2c0` (time to live), `+0xf0` and `+0xf4` (desowning time). Other fixed fields: `+0x2c4 = 0.1`, `+0x2b8 = 2` (collisions), `+0x2cc`/`+0x2c8 = 5.0` (health), `+0x2dc = a4`, `+0xe0 = a5`.
* After the loop it creates one smoke/flash body and plays `strides` and `strides_fire` once per bomblet.
* So **one place** sets bomblet lifetime: scaling `param_6` on entry (or the three stores) changes all cluster and mine bomblets. This is the patch site for the roadmap item. [code]; the patch itself is not written or tested.

## The call site [code]
* Only one direct call exists: `0x140036c68`, inside the `creatureLogic` code region (Ghidra shows no function at that exact address; it is a chunk of `creatureLogic` `0x140033b90`). The other xref (`0x1480797d0`) is data, a table slot, probably a vtable or dispatch entry. [guess] that there may be a second, indirect, caller through that slot; not checked.
* Argument setup just before the call (`0x140036bf4`-`0x140036c65`): `R8D = (int)(XMM6 / [0x1403524e0])` is the **count**, where `XMM6` came from `FUN_140048870(creature)` and is also stored to `creature +0x2dc`; stack arg 5 (`[rsp+0x20]`) is the constant at `0x140354820`; **stack arg 6 (`[rsp+0x28]`) is `XMM10`**, i.e. the TTL, loaded by an earlier instruction in `creatureLogic`; stack arg 7 is a negated float; `XMM1` is the constant at `0x14035470c`.

## Open [not read]
* What `XMM10` holds here. No instruction writes `XMM10` between `creatureLogic`'s entry and `0x140036c68` in the ranges searched (`XMM10` is callee-saved, so it was set early in the function or the search missed an encoding). A decompile of the `creatureLogic` branch that contains `0x140036c68` would show it; the function is too large to decompile in one piece.
* Whether mine bomblets use the same call site or the indirect table slot.
* Which projectile logic id reaches this branch (cluster missile vs mine); the TTL may differ per ammo.
