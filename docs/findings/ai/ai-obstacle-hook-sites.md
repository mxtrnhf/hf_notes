# AI obstacle scan and steering: hook sites (1.163), 2026-10-23, for probe-dev (hf_ai)

Tags: **[V]** disassembly read, constants read from memory. Stolen-byte counts are instruction-aligned, with no rip-relative operand and no relative branch inside the cut (except where noted). `AiShipTick 0x140062f90` runs for AI ships; `AiShip_SteerController 0x14006cb30` is a second implementation with different constants (see ai-steering-and-avoidance.md s3, s5). Both are called by `aiShipDriver 0x1400739c0` (driver state = int at creature `+0xbd8`; state 2 = idle; `SteerController` call sites `0x140073d25`, `0x140073d89`, `0x140073ef0`; `AiShipTick` call `0x140074017`). Which state runs which was not mapped through the jump table: hook both scan sites (`0x140064e6f` in AiShipTick, `0x14006cf83` in SteerController) and log which fires.

## Scan call (AiShipTick, call at `0x140064e6f`)
`AiShip_ScanObstacles(RCX = creature (R14), RDX = &list = creature+0xd78, XMM2 = range, XMM3 = minMass (= 0.1 * mass, mass at [RBP-0x60]), [RSP+0x20] at the call = maxExplosive 500.0)`. Inside the callee the stack arg is at `[RSP+0x28]` at entry.
* List container: MSVC `std::list` with the sentinel node pointer at `creature+0xd78` and the element count at `creature+0xd80`; the list is emptied just before the scan (`0x140064dbc` loop) and **stays intact until the next tick's scan**. Walk: `node = [sentinel]`, `next = [node]`, element pointer = `[node+0x10]` (obstacle struct, 0x38 bytes: `+0x00` body, `+0x08/+0x0c` pos, `+0x10/+0x14` velocity, `+0x18` radius, `+0x1c/+0x20` unit vector ship->obstacle, `+0x24` gap, `+0x28` bearing, `+0x2c/+0x30` shadow interval, `+0x34` weight).
* Weight loop `0x140064ea0..0x140064f40` stores the weight at `0x140064f2c` (`MOVSS [RCX+0x34],XMM0`), accumulates `A = sum(-w * dir)` in XMM5 (x) / XMM6 (y). Own velocity is at `[RSP+0x74]` (x) / `[RSP+0x78]` (y); own position and own radius are not held here (ScanObstacles recomputes them: root = `[creature+0x88]` if its class nibble is 0xf, else the creature; ownPos = vtable `+0xe8` applied to `root+0x210`; ownRadius = `root+0x20c`; they are passed on as `AddObstacleNode(RDX = &ownPos, XMM2 = ownRadius)`).

## Hook sites
| # | Address | Stolen bytes | What is live there |
|---|---|---|---|
| 1 | `0x140064f58` (jump target of the empty-list path too) | `f30f1055a0 f3450f58c8` (10 bytes: `MOVSS XMM2,[RBP-0x60]`; `ADDSS XMM9,XMM8`) | A final: XMM5 = A.x, XMM6 = A.y (zero when no obstacles). XMM9/XMM10 = dir_t (unit vector to waypoint), XMM12 = `s * cmd_max` (s and cmd_max are multiplied before; not separate), `[RBP-0x60]` = mass, `[RBP-0x64]` = time scale ts = 10/min(accel,4), `[RSP+0x74/0x78]` = own velocity. dist and s are not kept separately in registers here. |
| 2 | `0x140065002` | `f3440f1154243c 450f28d0` (11 bytes) | F final before the attitude term: F.x = `[RSP+0x38]`, F.y = `[RSP+0x3c]` (stored at `0x140064fd7` and `0x140065002`). Preserve EFLAGS: the `COMISS` at `0x140064ffb` feeds the `JBE` at `0x14006500d`. |
| 3 | `0x140065233` (reached from both branches of the bank-1 clamp) | `410f28c3 410f28c9` (8 bytes) | bank 1 clamped: XMM12 (x), XMM10 (y); bank 2 after the attitude pair, NOT yet clamped: XMM11 (x), XMM9 (y). |
| 4 | `0x1400652d7` | `f3450f58a61c0c0000` (9 bytes, `ADDSS XMM12,[R14+0xc1c]`) | both banks clamped (limit 2T): bank 1 = XMM12/XMM10, bank 2 = XMM11/XMM9; next the 5-slot sum. |
| 5 | `0x1400653ea` | `41ff866c0c0000` (7 bytes, `INC [R14+0xc6c]`) | after the filter output (sum/6) and the slot stores: bank 1 out = XMM12/XMM10, bank 2 out = XMM11/XMM9; RAX = the ring index used this tick. These are the vectors converted to engine commands. |
| 6 | `0x140065456` / `0x14006546d` (stores) | | unit direction of F stored to creature `+0x1328/+0x132c` from XMM14 / XMM15 (read the creature fields instead of hooking). |

## ScanObstacles `0x14024cc20` and AddObstacleNode `0x14024ce50`
Body array: qword pointers, stride 8, base `0x143a33c90`; element count (loop bound) = dword at `0x143a51150`.
* `ScanObstacles` entry hook `0x14024cc29` (after the `TEST RCX,RCX / JZ`): stolen `4c8bdc 4154` (5 bytes: `MOV R11,RSP; PUSH R12`). RCX = creature, RDX = list pointer, XMM2 = range, XMM3 = minMass, maxExplosive at `[RSP+0x28]`.
* Considered counter: `0x14024cd46` (reached for every body that passed the active/own/class/b2-body filters, RBX = body): stolen `4032ff 440f2ec6` (7 bytes).
* Mass test: `0x14024cd69`: stolen `440f2fc0 400fb6ff` (8 bytes; `COMISS XMM8,XMM0` and `MOVZX EDI,DIL`), XMM0 = `returnMass(body)` (`0x1400486e0`), XMM8 = minMass, RBX = body; the drop flag becomes 1 when minMass > mass (and the vtable `+0x1a8` call at `0x14024cd57` returned 0). Overrides: explosive `[RBX+0x2dc] >= maxExplosive` clears the drop flag (`0x14024cd8f`); `creature +0xd70 == 2` with part-flag bit 21 keeps the body (`0x14024cdaa`).
* "Kept" point (call to AddObstacleNode will follow): `0x14024cdb5`, stolen `4d8bcc f3440f114c2420` (10 bytes), RBX = body. dropped = considered - kept.
* `AddObstacleNode` entry hook `0x14024ce59` (after `TEST RCX,RCX / JZ`): stolen `488bc4 48895810` (7 bytes). RCX = body, RDX = &ownPos (two floats), XMM2 = ownRadius, R9 = list pointer, range at `[RSP+0x28]`. The node is created at the end of the function (`New(0x38)`); range / shadow discards happen inside.

Ghidra: disassembly comments were added at hook sites 1 to 5.
