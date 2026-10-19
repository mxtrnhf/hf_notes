# Strategic AI launches all its aircraft at once: where, and the patch sites (1.163)

Status: **read from the decompilation and disassembly (re-checked in this pass); no patch applied, nothing run in game.** Tags: legend in `../../../README.md`.
Addresses are 1.163 (image base `0x140000000`, the unpacked exe). Origin: roadmap AI item "the AI launches all its aircraft when it detects the player within strike range, so none are left for defensive interception".

## The function [code]
`TryLaunchAiAircraftGroup` at `0x1400ef910` (Ghidra name was the machine-propagated `rep_1400ea210_...`, now `TryLaunchAiAircraftGroup` after the 2026-10-15 name port; the 1.151 twin is `0x1400ea210`). `RCX` = AI fleet, `RDX` = detected target. Returns 1 if it launched.

Launch conditions, all required [code]:
| Test | Instruction | Value |
|---|---|---|
| target non-null | `0x1400ef94c` | |
| aircraft count (fleet `+0x4ec`) non-zero | `0x1400ef95d` | |
| distance to target `< range(+0x4f4) * 0.45` | `0x1400ef972` | `0.45` at `0x14036054c` |
| aircraft cooldown (`+0x510`) is 0 | `0x1400ef983` | |
| fleet state float `+0x188` is 0 | `0x1400ef99d` | |
| target field `+0x78` `< 1200.0` | `0x1400ef9b4` | `1200.0` (`0x44960000`) at `0x1403605ec`; 480.0 in 1.151 |
| distance `> 200.0` | `0x1400ef9ca` | constant at `0x14035282c` |

## How many aircraft [code]
`0x1400ef9fb`: `MOV ECX,[RBX+0x4ec]` loads the fleet's whole aircraft count into the group-size variable `[RBP-0x69]`. `0x1400efa04`: if the count is `> 10` (`CMP ECX,0xa / JLE`), a coin flip (`HGE vtable +0x108`, `Random_Int(0,1)`) halves it (`0x1400efa2c`-`0x1400efa33`: `MOV EAX,ECX / CDQ / SUB EAX,EDX / SAR EAX,1`). Counts of 10 or fewer all launch. The loop at `0x1400efb03`-`0x1400efc76` then adds one aircraft entry per count from the `PLANE_TLL` weight table and passes the list to `FUN_14010f8e0` (`0x1400efcfd`). Afterwards `0x1400efd07` sets the aircraft cooldown `+0x510 = 1800.0` (`0x44e10000`), and `0x1400ef9f3` stores `hourCount + 24` at `+0x528`.
So one launch sends **all** aircraft (or half, when more than 10), which is the roadmap complaint. [code]

## Patch sites [guess: untested]
* **Always halve (above 10), not a coin flip:** the `JZ` at `0x1400efa2a` (`74 0a`, skips the halving when the random result is 0). Replace the two bytes with `90 90`. Smallest change; still launches everything for counts of 10 or fewer. [bytes derived from the disassembly, not read back]
* **Keep a reserve:** reduce the stored count right after it is loaded, at `0x1400ef9fb`-`0x1400efa01` (`MOV ECX,[RBX+0x4ec] / MOV [RBP-0x69],ECX`). A detour here can write `max(1, count*fraction)` into `[RBP-0x69]` instead. Needs a code cave; the instructions are 6 + 3 bytes.
* **Launch later or less often:** the `0.45` factor (`0x14036054c`) is a shared constant, so repoint the operand at `0x1400ef972` to another constant rather than editing the value. Same for `1200.0` at `0x1400ef9b4`. The cooldown immediate at `0x1400efd07` is private to this function and can be edited in place.
* Not read: what the launch removes from the fleet's count (`FUN_14010f8e0` / `CreateMapAircraftGroup`), so whether a reserve really stays home needs that function. [not read]

## Live-test recipe
Breakpoint `0x1400efa01` (after the count is stored): `ECX` = fleet aircraft count, then read `[RBP-0x69]` after `0x1400efa33` to see the size actually launched. Let an AI fleet detect the player in strike range and check that the launched group size equals `count` (or `count/2` when `count > 10` and the roll succeeded). Then apply the `90 90` patch and confirm the halving becomes unconditional.
