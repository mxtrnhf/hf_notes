# The hull stabiliser: `creatureLogic` case logic id 200, one `Body_AddTorque` per engine part (v1.163), ghidra-miner, 2026-10-21
Found by the logger (sim.28): `Body_AddTorque` is called on the player Frame from return address `0x1400357d1`, one call per engine part per physics step. This note is the decompile of that code. Tags: [code] read in Ghidra, [inference], [open].

## Where it is [code]
* `creatureLogic` 0x140033b90 is the Body vtable slot `+0x1e8` (per-body logic tick); it switches on the part's logic id `+0x3c4`: `ecx = id - 1`, byte table at 0x140045170, jump table at 0x14004512c. **Logic id 200 (index 14) goes to 0x140035652**; id 210 (0xd2) goes to 0x1400357d6. (Id 200 is also the command code Part_HandleCommand sends to 0x140051060.) The engine parts' logic id is not in `OL.seria` stats; I derived "engine parts run this case" from the logger (one call per engine) and did not read it in parts data. [inference]
* Registers in the case: `RSI` = the engine part, `RBX` = its creature (`[RSI+0xb8]`), `RDI` = the root Frame (`traverseLinkedListCreature_(creature)`, or the part itself if the root is not a Body-class node).
* Entry guard (0x140035652): return if byte `0x143a11909` != 0; return if `[RSI+0xb8]` is null; return unless `0x140049e00(creature, 0x2f)` is true (class-code test). No timer, no key test, no `+0xbd4` test in the case.

## Formula [code, constants read]
```
gate  = creature+0x180c                         (= 2 * min(+0x1684, +0x1688), sums of Stats+0x100 per bank)
m_at  = GetMdlAt(part) = Stats+0x100  (0x140048720)
frac  = (gate == 0) ? 0 : m_at / gate
I     = Body_GetInertiaAboutOrigin(Frame)       (game units, b2 I / 0.05^5)
w     = Frame+0x13c        a = wrap(Frame+0x138, period 2*pi)   (0x14004ad40, dividePositive-based: result in [-pi, pi])
dt    = float global 0x1403c126c = 0.02          (the call is skipped if it is 0)

kd = kp = 0.05                                    (0x14035467c)
if creature+0xad4 > 0 and byte 0x147fc6fd4 (arcade flag) != 0 :  kd = 0.02 (0x140354674), kp = 0

Tw = -w * I * kd * frac
Ta = -a * I * kp * frac
if creature+0x17fc == 0 or creature+0x1800 == 0 :    # one thrust bank produced no force this tick
        Ta = 0 ;  Tw *= 0.5                           # 0x1403527a4
if creature+0x15b4 == 0 :  Tw = 0
T = Tw + Ta
if |T| > m_at :  T = sign(T) * m_at                   # cap at +-m_at, so u = T/m_at is in [-1, 1]
Body_AddTorque(Frame, T)                              # vtable +0x1a0: w += T * 0.05^5 * invI immediately
```
* This is a **PD-style hull stabiliser**: damping on `w` plus a restoring term on the wrapped hull angle toward 0 (hull "level"), shared among the engine parts in proportion to each part's `m_at` share of the gate, and capped per part. It is the same shape as the AI attitude hold in `AiShip_SteerController` (error `e = wrap(0 - angle)`, `k = e * I / 20`), but it acts through `Body_AddTorque` and **does run for the player ship** (logic tick of every engine part, no AI-flag test).
* Fit to the logged numbers: per call `u = T/m_at = -kd * (I/gate) * w` (+ `-kp * (I/gate) * a` when both banks fire). With `I = 2.27e8` (Lightning, 70.85 b2) and `gate = 3e7` (two statics, one per bank): `kd*I/gate = 0.378`, halved by the idle-bank rule `= 0.189` (logged 0.232, same order; the gate depends on the exact bank sums). In the stock ship both banks fire so the angle term is live with `kp = kd`: the ratio of the logged coefficients (0.20 / 0.22) matches `kp ~ kd`. [inference]
* **The angle term flips sign where `wrap(angle)` crosses +-pi**: `a` is the wrapped Frame angle `+0x138`, so near the inverted hull the torque jumps sign: this is the user's "180 degree" jerk. It exists only while both banks have thrust (`+0x17fc != 0 and +0x1800 != 0`); with the E/Q rotation keys held, swivel engines make both banks fire, a ship with only static engines does not (bank-2 statics get `cos < 0`, no force).
* Editor/arcade/side switch: `creature+0xad4 > 0` (player side) together with the arcade flag `0x147fc6fd4` replaces the gains by `kd = 0.02, kp = 0`. In Shipworks test flights and campaign battles the arcade flag is normally 0, so the default 0.05 / 0.05 applies. [inference, flag meaning not established]

## The 0.6 s tail after release: not found [open]
Nothing in this case has a 0.6 s timer: with no thrust, both bank sums read 0, so `Ta = 0` and `Tw` stays (x0.5) while `w` and `gate` are nonzero, and the torque would continue until `w` is 0. Candidates for what ends it (logger can check): (1) the bank sums `+0x17fc/+0x1800` are not cleared the way the case assumes (their writers: `Engine_ApplyThrustForce` adds; `CalculateStats(false)` zeroes `+0x17f8..+0x1808`; `CreatureUpdate` 0x14007eb50 reads them every tick and ramps `+0xbc4` with them, so a stale nonzero sum would keep both terms live until something resets them); (2) `creature+0x15b4` (zero turns the w term off; it is a stats-pass accumulator, written at 0x140081211); (3) the guard byte `0x143a11909`; (4) the logic tick of the part not being called after the engine's activity decays (flame smoothing, part `+0x840`). Log `+0x17fc`, `+0x1800`, `+0x15b4`, `+0x180c` and `byte 0x143a11909` each step through the release window to pick the cause.

## `+0xbc4` ramp (side finding) [code]
`CreatureUpdate` 0x14007eb50 (0x14007ef16..0x14007f089): `+0xbc4` is a 0..1 engine "spool" value. If the bank sums `+0x17fc + +0x1800` are nonzero it rises each tick by `dt / tau` with `tau` = 120 (battle-kind flags `0x147fc6fda/db/dc/dd`), 50, 30 or 10 seconds depending on flags (constants at 0x1403c0e30..3c), clamped to 1.0; with no thrust it falls by `dt / tau_down` (floored at 0). `IsInEditor` (0x1403ef368) resets it to 0 every tick (0x14007ec10). `Engine_ApplyThrustForce` multiplies thrust by 0.01 while `+0xbc4 < 0.5` (and sets 0.001 if it is exactly 0). So thrust is strongly reduced until the ramp passes 0.5; check this against the thrust the logger sees. The relation to my earlier f(X) note: both can scale thrust.

## `SetAngularVelocity` caller 0x14011c5fd [code]
`CreateFrameFragments` 0x14011c1a0: in its per-fragment loop it calls `0x140051e20` (set linear velocity) and then `Body_SetAngularVelocity(fragment, w_parent)` (`XMM6`, the parent's spin) for each fragment body (`R14`) that already has its own b2 body. It copies the parent's spin onto the pieces created when the Frame is split into bodies (break-up or part detaching); the target is the fragment, not the hull. The small values the logger saw (-0.17 to +0.4) are those fragment spins.

## Addendum (dispatch, bank sums, logger offsets) 2026-10-21 [code unless marked]
### Dispatch of the engine logic case
* `CreatureUpdate` 0x14007eb50 -> for each child part `FUN_140054b20` (Body update wrapper): `if vtable[+0x78](part)` (state-active predicate) then `vtable[+0x1e0](part, dt)` (Body update), then **`if (part+0x3c8 != 0)` (`m_logic_active` byte) `vtable[+0x1e8](part)` = `creatureLogic`**. So the logic case 200 runs for a part only while that byte is nonzero; `creatureLogic` itself clears `+0x3c8` in many other cases (one-shot logics) but the engine case 200 does not write it. No 0.6 s / 30-tick countdown exists in `FUN_140054b20`, in the case, or in `Engine_ApplyThrustForce` (all three read). Which of `[part+0x3c8]`, the `+0x78` predicate or the engine's own state changes 0.6 s after release is **not established**; the logger should record both per engine part.
### `creature +0x17fc / +0x1800 / +0x1804 / +0x1808`
* Written only by `Engine_ApplyThrustForce`, inside the branch where the force is actually applied (`cos(c-a) > 0`, power gate, fuel gate): scan the part's command list `part+0x370..+0x378`; **`+0x17fc += F` if the list contains 0x66 (bank 1), else `+0x1800 += F` if it contains 0x67 (bank 2)**; `+0x1804 += Fx`, `+0x1808 += Fy` (force vector). `F` is the applied force after the `+0xbc4` and f(X) factors.
* **They are never zeroed per tick.** The only zeroing store is the tail of `CalculateStats(.., bSetCreatureValues = false)` (0x140080dec/df3/dfa: `+0x17f8`, `+0x1800`, `+0x1808` as qword/dword), which runs on ship build / spawn, not per step; `Creature_ResetStatAccumulators` 0x140061f60 does not touch them; `+0x17f8` is the fuel-burn accumulator (`Creature_BurnFuel`). So each is "total thrust applied by bank N since the last reset", and the idle-bank test in the stabiliser (`== 0`) means "this bank has **never** fired since the last reset". [code; a reset through code that I could not see is possible]
* Readers: stabiliser case (0x140035757/0x140035766), `CreatureUpdate` 0x14007ef90/98 (`sum == 0` selects the `+0xbc4` ramp direction), the thrust history sampler (0x14008102c/34: stores `+0x1800 + +0x17fc` as the 6th float of each history record), `CalculateStats` (0x140080529/31), UI.
* Consequence for the swivel-only ship [inference]: a bank is idle in the stabiliser only if no engine carrying code 0x66 (bank 1) or 0x67 (bank 2) has ever had `cos(c - a) > 0` since the reset. With Q/E, bank 2 gets command angle `hull + pi`; a swivel engine whose joint limits or servo speed never bring it to `cos > 0` leaves `+0x1800 == 0`, and the case halves the damping and drops the angle term, as simulator observed. The stock ship's statics (mounted so that bank-2 statics reach `cos > 0`) make `+0x1800 != 0`. Check per engine: command list contents (bank), swivel limits, and the first tick each sum becomes nonzero.
### `creature +0x15b4`
* Sum over the velocity-history ring (up to 500 records, `CalculateStats` phase 5) of the 6th float of each record = the thrust sample `+0x1800 + +0x17fc` at the time of the record (`0x140081160..0x140081211`: fields `+0xc..+0x1c` of a record are added into `+0x15a4,a8,ac,b0,b4`). Zero until the first thrust sample is stored. With cumulative bank sums it stays nonzero afterwards.
### Logger offsets (sim.29)
| item | where | type |
|---|---|---|
| bank 1 / bank 2 applied-thrust sums | creature `+0x17fc` / `+0x1800` | float |
| force vector sums | creature `+0x1804` / `+0x1808` | float, float |
| history thrust sum | creature `+0x15b4` | float |
| turn gate | creature `+0x180c` | float |
| bank m_at sums | creature `+0x1684` / `+0x1688` | float |
| side / spool / total mass | creature `+0xad4` / `+0xbc4` / `+0x15b8` | float |
| AI flag, AI state | creature `+0xbd4` (byte) / `+0xbdc` (int) | |
| effective-thrust sums | creature `+0x166c` / `+0x1670`, X = `+0x1608` | float |
| engine list | creature `+0x1390` (begin) .. `+0x1398` (end): vector of 0x18-byte Link records, part pointer at record `+8` | |
| per part | command list begin/end `+0x370` / `+0x378` (int32 codes); logic id `+0x3c4` (int); `m_logic_active` `+0x3c8` (byte); power `+0x818` (float); `+0x810` (float, 3.0 set when thrust exceeds a threshold); `+0x820` (float, gun active flag); engine activity `+0x840` (float); Stats id `+0x188` (int); local mount angle `+0x138` (float); owner `+0x...` via Link at `+0x88` master | |
| command struct | `+0` code, `+4` strength (or angle for 100/101), `+0xc` remaining count, `+0x10` angle, `+0x18` force sum out | |
| globals | byte `0x143a11909` (entry guard), byte `0x147fc6fd4` (arcade), byte `0x1403ef368` (IsInEditor), float `0x1403c126c` (dt = 0.02), world `0x143a119f0` | |
* Tying a torque row to a part: hook `Body_AddTorque` 0x140019be0 and filter on return address `0x1400357d1`; at that moment `RSI` = the engine part, `RBX` = the creature, `RDI` = the Frame (all callee-saved, untouched by the callee prologue), `XMM1` = T. For the intermediate terms, an inline detour at **0x1400357c5** (cut 6 bytes: `48 8b 07 48 8b cf` = `MOV RAX,[RDI]; MOV RCX,RDI`, no branch, no RIP-relative) sees `RSI, RBX, RDI`, `XMM1` = clamped T, `XMM9` = m_at, `XMM8` = frac, `XMM10` = I, `XMM7` = Tw after the rules.

## Addendum 2 (frame order, inertia, register map) 2026-10-21 [code]
* **Frame order** (`!FrameFunc` 0x1401a8970, calls at 0x1401a8eb8..): `SomethingPreTask` 0x140286e40 (BreakUpFrame, cleanup, history ring; does not touch the thrust sums) -> `SomethingPhysicTask` 0x140286380 -> `SomethingInputTask` 0x14018dbf0 (`Player_SendThrustCommands` -> `Engine_ApplyThrustForce`: forces and the `+0x17fc..+0x1808` adds) -> `SomethingAITask` 0x140011180 -> `SomethingGameTask` 0x140127590 -> 0x1402dd890 -> 0x140316e20 -> list walk at 0x143a15868. `CreatureUpdate` 0x14007eb50 is reached through a vtable (no direct caller), after the input task in the frame. The per-tick zeroing of `+0x17fc/+0x1800` that the logger sees (0 at Step entry) was **not found**: all stores to `+0x17f0..+0x1808` are `Engine_ApplyThrustForce` adds and `CalculateStats(.., false)`; `Creature_ResetStatAccumulators` and `SomethingPreTask` do not clear them. [open]
* **Inertia used**: `Body_GetInertiaAboutOrigin` 0x140048440 `= (m*(lc.x^2+lc.y^2) + I)/0.05^5`, from the Frame's own b2 body only (`+0x90` mass, `+0x98` inertia about COM, `+0x1c/+0x20` sweep.localCenter); parts with their own b2 body are not included; creature mass `+0x15b8` is not used by the stabiliser.
* **Register map at 0x1400357c5** (no call between 0x140035745 and the AddTorque call): `XMM1` = T (clamped), `XMM7` = Tw (after halving and the `+0x15b4` test), `XMM9` = m_at, `XMM8` = m_at/gate, `XMM10` = I, `XMM2` = kp, `XMM3` = sign mask, `XMM6` = 0, `XMM0` = dt; `RSI` part, `RBX` creature, `RDI` Frame. Not in registers: gate (`creature+0x180c`), w (`Frame+0x13c`), wrapped angle a (recompute from `Frame+0x138`), kd (0.05, or 0.02 under arcade flag with side > 0), and Ta/T0 when the clamp fired. `RSP` is 0 mod 16 in the whole body (prologue: 5 pushes + `SUB RSP,0xc50`, entry RSP is 8 mod 16); no push/pop in the case; flags are not live across 0x1400357c5.

## Correction 2026-10-21 (sim.30 readings; supersedes the "cumulative / never fired since reset" reading above)
* The logger (sim.30, detour at 0x1400357c5) shows `creature +0x17fc` / `+0x1800` **nonzero inside the stabiliser**, while they read 0 at `b2World_Step` entry. So they behave as **per-tick** sums: `Engine_ApplyThrustForce` adds them in the input task, `CreatureUpdate` (stabiliser, `+0xbc4` ramp) reads this frame's values, and something clears them afterwards, before the next step. I still did not find the clearing store (see the frame-order addendum); the "cumulative since reset" statement and the sentence "idle means the bank has never fired" are **wrong**. Correct rule: **the idle-bank test is made every tick on that tick's bank force sums**: if either `+0x17fc` or `+0x1800` is 0 in this tick (one bank applied no force: no engine of that bank passed `cos(c-a) > 0`, the power/fuel gates), the angle term is dropped and the damping term is halved for that tick.
* Measured with the player ship: `Tw` equals the formula to 1.00000 (sd 0) over about 20 000 active rows. The S rows also contain enemy ships' calls, which follow the same formula: **the stabiliser runs for AI ships too** (consistent with the case having no AI-flag test).
* Related note by the simulator session: [hull-rotation-behaviour.md](hull-rotation-behaviour.md) (player-visible behaviour per design with the measured numbers).
