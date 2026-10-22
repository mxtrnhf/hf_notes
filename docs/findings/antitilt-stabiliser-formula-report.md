# Hull "engine anti-tilt" stabiliser: formula, closed-form behaviour, parameter sensitivity (v1.163)

Compiled 2026-10-22 from the notes in `hf_notes/docs/findings/` and the simulator `hf_ml/sim/hfsim/flight.py`. Read-only research: no Ghidra access, no new measurements. Tags as in the notes: [code] read in Ghidra by ghidra-miner/curator, [log] measured on flight logs, [inference] derived here or in a note, [open] unresolved. Numbers not found in a source are marked "not in sources".

Sources: `hull-stabiliser-engine-logic.md` (main decompile, sections "Formula", Corrections 1-2), `hull-stabiliser-coupling.md` (verification, inertia table, clamp regimes), `player-attitude-stabiliser.md` (where `m_mdl_at` is read), `hull-rotation-behaviour.md` (player-visible summary), `static-engine-force-path.md` (how thrust reaches the hull), `flight.py` `Flight._stabiliser`, `hf_ml/data/Libraries/OL.seria`.

## 0. Is this "the headache parameter"? Not defined anywhere

A case-insensitive grep for `headache` over `hf_notes`, `hf_ml` (incl. `notes`, `handover`, `DESIGN_NOTES.md`, `ROADMAP.md`, `TASK.md`, `sim/`) and the rest of the project tree found **no occurrence** (also none for "migraine", "head-ache"). No source defines a "headache parameter". The notes call the mechanism "stabiliser", "anti-tilt" (`m_mdl_at`, "angular thrust" in `structures.md`), "PD-style hull stabiliser". So the identification with the user's nickname cannot be confirmed from the project; it is the user's own term. Candidate quantities that could be meant (none confirmed):

| candidate | what it is | why it could be a "headache" |
|---|---|---|
| `kd`, `kp` | 0.05 / 0.05 constants at 0x14035467c (arcade variant 0.02 / 0) | global gains, not in OL.seria |
| `m_mdl_at` (Stats +0x100) | per-engine data field in OL.seria; the only OL.seria input | sets share and clamp |
| `gate` (creature +0x180c) | `2*min(bank-1 sum, bank-2 sum)` of m_at | normalises every engine's share |
| `frac = m_at/gate` | per-engine share of the torque | |
| the 0.6 s tail / `+0x15b4` history | on/off switch of the damping term | mechanism still [open] |
| `stab_share` (sim only) | 0.6 / 0.9 fudge for children inertia coupling | the sim's biggest unexplained knob (Lightning 0.6) |

The anti-tilt formula is the best match for "a hidden parameter that makes ships behave oddly" (the notes show it explains the spin plateau, the 0.6 s drop and the once-per-turn "lurch"), but whether that is the user's "headache parameter" is [open] and should be confirmed with the user.

## 1. Plain-language summary

* What: every engine part of a ship, every physics step (dt = 0.02 s), pushes the hull's angular velocity directly (via `Body_AddTorque`) against its spin and against its tilt away from "level" (angle 0). It is a game mechanic, not Box2D physics, and never appears in any force/torque accumulator. [code][log]
* When: while the ship thrusts and for about 0.6 s after thrust ends (30-tick thrust history `creature+0x15b4`; the damping term is zeroed when the history is empty). The mechanism of the 0.6 s is measured, not decoded (section 5). [log][open]
* Who: the player ship and AI ships alike. The case (`creatureLogic` logic id 200, 0x140035652) has no AI-flag, key, or timer test. [code][log: enemy rows follow the same formula]
* Which engines: all live engine parts that carry bank command 0x66 or 0x67, swivel and static alike. Each engine contributes a share `m_at/gate` of the total, so the shares sum to ~1 for the hull.
* Effect: a damping of the hull spin with time constant ~0.3 s (both banks firing) or ~0.6 s (one bank idle, or after release), plus, only when both banks fired this tick, a restoring "spring" toward angle 0 that flips sign where the wrapped angle crosses +-pi (the "lurch", once per revolution). [inference from [code]]

## 2. Full formula [code, constants read; Tw verified to ratio 1.00000 on ~20 000 rows, [log]]

Per engine part `p` (the case runs once per engine part per step; `RSI` = part, `RBX` = its creature, `RDI` = the root Frame):

```
gate  = creature+0x180c = 2 * min(creature+0x1684, creature+0x1688)
m_at  = Stats+0x100 of the part                        (GetMdlAt 0x140048720; OL.seria m_mdl_at)
frac  = (gate == 0) ? 0 : m_at / gate
I     = Body_GetInertiaAboutOrigin(Frame)  (0x140048440) = (m*|lc|^2 + I_com) / 0.05^5     [game units]
w     = Frame+0x13c         (angular velocity, rad/s)
a     = wrap(Frame+0x138)   (0x14004ad40; result in [-pi, pi])
dt    = float 0x1403c126c = 0.02   (AddTorque call skipped if 0)

kd = kp = 0.05                                       (0x14035467c)
if creature+0xad4 > 0 and byte 0x147fc6fd4 (arcade flag): kd = 0.02, kp = 0    (0x140354674)

Tw = -w * I * kd * frac
Ta = -a * I * kp * frac
if creature+0x17fc == 0 or creature+0x1800 == 0:    # a bank applied no force THIS tick
        Ta = 0;  Tw *= 0.5                           # 0x1403527a4
if creature+0x15b4 == 0: Tw = 0                      # thrust-history sum
T = Tw + Ta
if |T| > m_at: T = sign(T) * m_at                    # clamp is to the part's own m_at, NOT scaled by gate or engine count
Body_AddTorque(Frame, T)    # 0x140019be0, vtable +0x1a0:  w_b2 += T * 0.05^5 * invI_com   (immediately)
```

Terms and where inputs come from:

| term | meaning / unit | source |
|---|---|---|
| `m_at` | "angular thrust" capability of this engine; same units as torque in game units (N-ish * game length) | `OL.seria` `m_mdl_at` -> Stats `+0x100` |
| `+0x1684` / `+0x1688` | sum of `m_at` of live engines whose command list has 0x66 (bank 1) / 0x67 (bank 2); no swivel test | `Creature_AccumulatePartStats` 0x140071380 (adds at 0x140071614 and 0x1400716f6); zeroed in `Creature_ResetStatAccumulators` 0x140061fbf |
| `gate` | `2*min(bank1, bank2)`; if the banks are equal, gate = total of m_at | `CalculateStats` 0x140080c24; readers: the stabiliser, `AiShipTick`, `AiShip_SteerController` |
| `frac` | share; dimensionless | computed per call |
| `I` | inertia of the Frame b2 body ONLY (children with own b2 bodies not included), about the body origin, game units (b2 inertia / 0.05^5). Larger than I_com by `R = I/I_com` (Intrepid 1.0985, stock Lightning 1.2892) | `hull-stabiliser-coupling.md` sec. 2 [V][log] |
| `w`, `a` | Frame spin and Frame angle. `+0x138` is written once per step by `Body_SyncFromB2` (0x140054bf0) from the unwrapped b2 angle, so **all engine calls in one tick read the same (stale) w and a** (sim flag `stab_stale`) | [code]; stale reading attributed to ghidra-curator in `flight.py` comments |
| `kd`, `kp` | 0.05 each (per-tick fraction of the "full" correction, dimensionless) | constants at 0x14035467c |
| arcade variant | `kd = 0.02`, `kp = 0` when `creature+0xad4 > 0` (player side) and arcade flag byte `0x147fc6fd4` != 0; normal Shipworks flights and campaign have the flag 0, so 0.05/0.05 applies [inference, flag meaning not established] |
| idle-bank rule | `+0x17fc` / `+0x1800` = force applied by bank 1 / 2 **in this tick** (about the bank thrust, e.g. 7e7). If either is 0 this tick: `Ta = 0`, `Tw *= 0.5`. Written by `Engine_ApplyThrustForce` 0x140028360 only where `cos(cmd - a) > 0` and power/fuel gates pass. **The per-tick clear is not found in the binary** [open]; the per-tick reading is measured (sim_runs21) [log] |
| `+0x15b4` rule | sum over the velocity-history ring (up to 500 records; ~30 samples are live after release) of the bank thrust sample `+0x1800 + +0x17fc`. Drains linearly after release, hits 0 at 0.6 s; `Tw = 0` then (torque stops) [log: sim.29 G rows, sim_runs21]. Note `Ta` is already 0 after release (both banks idle) |
| `Body_AddTorque` | `w += T * 0.05^5 * invI_com`; invI_com = Frame b2 body's own `+0x9c` = 1 / I about its centre of mass. Measured ratio to the logged spin jump: 1.000001 (Intrepid), 1.000000 (Lightning) over 750 ticks [log] |
| dt | 0.02 s = 1/50 (`b2World_Step` dt = frame scale / 50, 10+10 iterations) |

Order inside a frame: `SomethingInputTask` (thrust forces, bank sums) precedes `CreatureUpdate` (logic case 200 via `FUN_140054b20` -> vtable `+0x1e8`), so the case sees this tick's bank sums. Logic runs for a part only while part `+0x3c8` (m_logic_active) is nonzero. [code]

## 3. Simplified per-tick algebra

Key observation: `frac * I / m_at = I/gate`, so the unclamped output of every engine is `T/m_at = u` with the SAME `u` for all engines:

```
u = -(kd * I / gate) * ( s * w + a_on * (kp/kd) * a )        s = 1 (both banks fired), 0.5 (idle bank); a_on = 1 / 0
T_p = m_at(p) * u   (clamped to u in [-1, 1])
```

Because w and a are stale within a tick, the engines simply add. With `S = sum over live engines of m_at` (both banks):
`dw = (0.05^5 / I_com) * sum T_p = (0.05^5 / I_com) * S * u`, and `0.05^5 * I = I_b2` (b2 units), so

```
dw = -kd * R * (S/gate) * ( s*w + a_on*(kp/kd)*a ),     R = I / I_com,   S/gate = sum(frac)
sum(frac) = (bank1_sum + bank2_sum) / (2*min(bank1_sum, bank2_sum)) = 1/2 + max/(2 min)
```

* Balanced banks (equal m_at sums): each bank's fracs sum to 1/2, total sum(frac) = 1. Example, per bank 3.5e7: gate 7e7, a NK-25 (1e7) has frac 1/7, a D-30S (1.5e7) 3/14, bank = 2/7+3/14 = 1/2.
* Unbalanced: the WEAKER bank still sums to exactly 1/2 (it defines the gate), the stronger bank sums to `max/(2 min) > 1/2`, so sum(frac) > 1 and the correction is stronger than the balanced one, until the clamp. [inference from [code]]
* Per-tick factor, both banks firing, unclamped (balanced): `w' = w * (1 - 0.05 R) - 0.05 R * a`. Effective damping `k_w = 0.05 R`, spring `k_a = 0.05 R` (per tick; angle in rad, result in rad/s).
* Idle bank or after release: `w' = w * (1 - 0.025 R)`, no angle term, as long as `+0x15b4 != 0` (<= 0.6 s after the last thrust sample).
* Time constants (dt = 0.02, `tau = -dt/ln(1-k)`): both banks `tau = 0.02 / -ln(1 - 0.05R)`; idle `tau = 0.02 / -ln(1 - 0.025R)`. Box2D's own angular damping (0.05, `w/(1+dt*0.05)`) and the children coupling (below) are not included. [inference]
* Spring view (continuous approximation, both banks): `dw/dt = -(0.05R/dt)(w + a)`, i.e. `omega0^2 = 0.05R/dt` (rad/s)^2, damping rate `0.05R/dt` /s, `zeta = 0.5*sqrt(0.05R/dt)`. [inference]
* Clamp bites for ALL engines at once (same u) when `|u| > 1`: i.e. `(kd*I/gate) * |s*w + a_on*a| > 1`, threshold `|w| = gate/(kd*I)` (x2 under the idle halving). In the clamped regime each tick gives `|dw| = S * 0.05^5 / I_com`, independent of w, I and gate. [code, hull-stabiliser-coupling.md sec. 2]
* Stock Lightning is purely linear (never clamped in the logged window); Intrepid is clamp-bound ~49 % of calls. [log]

### Worked example (stock Lightning, numbers from the notes and OL.seria)
Engines (checked by loading `Designs/Lightning.seria` with `hfsim.seria`): per bank 2x `MDL_ENGINE_04` (NK-25, swivel, m_at 1e7) + 1x `MDL_ENGINE_05` (D-30S, static, m_at 1.5e7); bank sum 3.5e7, gate = 7e7 (matches the logged gate). Frame b2 numbers from `hull-stabiliser-coupling.md`: I_com 70.85, I (about origin) 91.33, R = 1.2892, so I = 91.33/3.125e-7 = 2.92e8 game units (derived here).
* `kd*I/gate = 0.05 * 2.92e8 / 7e7 = 0.209` per (rad/s). fracs: NK-25 1/7 = 0.143 (x4), D-30S 3/14 = 0.214 (x2); sum = 4/7 + 3/7 = 1.
* Both banks fire: `k = 0.05 * 1.2892 = 0.0645`/tick: `tau = 0.02/0.0666 = 0.30 s`. Restoring `omega0 = sqrt(0.0645/0.02) = 1.80 rad/s`, `zeta ~ 0.9`.
* Angle sign flip at +-pi: jump `2*pi*0.0645 = 0.405 rad/s` in one step; the notes log "about 0.38 rad/s" (the lurch). [inference vs log, close but not identical]
* Idle bank / tail: `k = 0.0322`: `tau = 0.61 s`; over the 30-tick tail the spin falls to `(1-0.0322)^30 = 0.37`. The notes log "about 40 %" for the statics-only design and "about half" for four swivels (different R); consistent in order, not an exact fit. [inference]
* Clamp threshold: `gate/(kd*I) = 4.79 rad/s` (notes: 4.8), idle x2. Max clamped step: `7e7 * 3.125e-7 / 70.85 = 0.309 rad/s` per tick. (Intrepid: threshold 1.39 rad/s; 4 x 1e7 -> `0.076 rad/s` per tick.)
* Kormoran (`Designs/Kormoran.seria`): per bank 1x ENGINE_01 (RD-59, swivel, m_at 7e7) + 2x ENGINE_05 (D-30S, 1.5e7): bank 1e8, gate 2e8; fracs 0.35 (x2) and 0.075 (x4), sum 1. Its Frame inertia and mass are NOT in the sources, so its tick factor and clamp threshold cannot be stated (`k = 0.05 R`, `R` unknown; `kd*I/gate = 0.05*I/2e8`).

## 4. How each OL.seria parameter enters

OL.seria `m_mdl_at` per engine (`hf_ml/data/Libraries/OL.seria`, read directly): ENGINE_01 7e7, 02 7e7, 02_OLD 7e7, 03 1e7, 03_OLD 1e7, 04 1e7, 05 1.5e7, 05_OLD 1.5e7, 06 4e6. Thrust `m_mdl_thrust` (+0xf8): 01 9e7, 02 1.1e8, 03 2.5e7, 04 3.6e7, 05 3.2e7, 06 4e6. Mod copy `hf_mods_unpack/hara_vera/.../OL.seria` adds `MDL_ENGINE_NERVA`: thrust 1.9e8, m_at 7e7 (other values identical).

| parameter | effect on the anti-tilt | tag |
|---|---|---|
| `m_mdl_at` per engine | sets its `frac` and its clamp level `+-m_at`; summed per bank into `+0x1684/+0x1688` -> gate. Doubling every m_at changes nothing in the unclamped regime (frac invariant) but doubles the clamp. Scaling one bank only: the weaker bank sets gate | [code] |
| engines per bank | adds to that bank's sum; a bank with no live engine gives `min = 0` -> gate 0 -> frac 0 -> no torque at all (sim returns when gate <= 0) | [code] |
| which bank is weaker | defines the gate; the weaker bank's fracs sum to exactly 1/2, the stronger's to `max/(2 min) > 1/2`, so total correction `> 1` times the balanced one | [inference] |
| swivel vs static | both count: no swivel test around the add (`player-attitude-stabiliser.md`). Static engines matter through the bank sums and, by whether a bank fires (`cos(cmd - a) > 0`, bank-2 statics get cos < 0 under Q on some designs), through the idle rule: a statics-only ship is "idle" on ~100 % of ticks (one bank never fires), a swivel-only ship ~4-9 % | [code][log] |
| bank membership | by command list: 0x66 = bank 1, 0x67 = bank 2, not by swivel/static | [code] |
| dead engines | drop out of the bank sums (the stats pass counts only live parts) and out of the torque loop | [code per sim comment; ghidra-curator] |
| locked-out engines (overheat lockout) | still counted in the sums; the lockout only stops their force, which can make a bank idle for that tick | [code per sim comment] |
| `m_mdl_thrust` (+0xf8) | not in the formula. It enters only indirectly: whether a bank applied force this tick (idle test), the `+0x15b4` history (the sum of thrust samples), and fuel/power/`+0xbc4` thrust factors (x0.01 while `+0xbc4 < 0.5`) | [code] |
| mass / inertia | via `I` (Frame body only, about its origin) in T, and via `invI_com` in `AddTorque`: net `dw` scales with `R = I/I_com` only, not with absolute inertia. Heavier hull -> same per-tick fraction; clamp threshold `gate/(kd*I)` falls with I, clamped step `S*0.05^5/I_com` falls with I_com. Children (swivel engines, guns, legs) are separate b2 bodies, excluded from I but they share the impulse in the solver (section 5) | [code][log] |
| creature mass `+0x15b8` | not used by the stabiliser | [code] |

Check of the simulator M_AT table (`flight.py` line 280) against OL.seria: ENGINE_01..06 values match exactly (7e7, 7e7, 1e7, 1e7, 1.5e7, 4e6). The sim table lacks `_OLD` variants and NERVA; `M_AT.get(oid, 1e7)` would return 1e7 for them (wrong for 02_OLD 7e7, 05_OLD 1.5e7, NERVA 7e7); `aipilot.py` reads `m_mdl_at` from the libraries correctly. No design checked here (Kormoran, Lightning, Intrepid) uses an `_OLD` engine.

## 5. What the simulator does differently / adds, and what is open

`Flight._stabiliser` with `stab_code=True` (flight.py ~282-336) implements the formula of section 2: per engine `tw = -w*Igame*0.05*frac*stab_gain*stab_kd_mult`, `ta = -wrap(angle)*Igame*0.05*frac*stab_gain*stab_kp_mult`, idle -> `ta = 0, tw *= 0.5`, clamp +-m_at, `w += t*S^5*invI` with `S = 0.05`. `Igame = (m*lc2 + Icom)/S^5` from a separate Frame-only reference body. Differences and additions:

| item | simulator | note |
|---|---|---|
| tuning knobs | `stab_gain` (global multiplier), `stab_kd_mult` (kd), `stab_kp_mult` (kp), all default 1.0 = exact code | not in the game |
| `stab_share` | the impulse is divided by `invI = 1/(Icom + share*(Iasm - Icom))`, share 0 = Frame alone, 1 = whole welded assembly; auto: 0.6 for designs named Lightning*, 0.9 otherwise. The code says `invI_com` of the Frame body alone (share 0); the real children-coupling happens in the b2 solver. Intrepid is rigid-coupled within ~1 % (ratio 0.924 vs rigid 0.916); stock Lightning responds ~9 % more than rigid (fitted extra 10.9 vs 18.2 predicted) | [log][open] |
| `stab_stale` | True: all engines read the same w and angle (game); False: older sequential feedback | [code] |
| idle-bank test | per tick from the sim's `last_force` bank sums (L/R force vector sums == 0), matching Correction 2; `stab_angle` None = angle term whenever not idle, True/False forces it | [log] |
| 0.6 s tail | `_since_thrust > 30` -> return: history = steps since any engine applied force. This is an emulation of `+0x15b4` draining over 30 samples; the real mechanism (what keeps the history, why 30) is not decoded | [log][open] |
| gate | computed from live engines per bank `L`/`R` of the design (equivalent to 0x66/0x67) with M_AT | [code] |
| legacy model | `stab_code=False`: old fit `kd = stab_c/sum(mats)`, 0.6 s timer after keys released; superseded | |
| not modelled | arcade variant (kd 0.02, kp 0), the `creature+0xad4` side test, `m_logic_active`/guard byte `0x143a11909`, AI ships' stabiliser | |

Open / unverified items:
* [open] The 0.6 s tail: no 0.6 s timer exists in the case, `FUN_140054b20`, or `Engine_ApplyThrustForce`. Measured: `+0x15b4` drains linearly 6.3e7 -> 0 between t = 8.06 and 8.66 after the E hold release (30 samples) and the torque stops there. The `+0x15b4` store (0x140081160..0x140081211) sums the history ring, but why exactly 30 samples stay is not shown. (Note `hull-stabiliser-engine-logic.md`'s own earlier candidate list (1)-(4) is superseded by the sim_runs21 measurements.)
* [open] The per-tick clearing of `+0x17fc/+0x1800`: no store found in the whole image (operand scan, byte search, LEA scan). Behaviour is measured per tick; mechanism unknown (hypotheses: a swapped copy of the creature, an unenumerated vtable method).
* [open] The Lightning excess: stock Lightning responds ~9 % more strongly to a Frame impulse than rigid coupling predicts, absorbed by `stab_share` 0.6; the Gladiator (same engines) fits 0.9. Candidates (swivel-servo motor reaction up to 300.76 * dt = 6.0 angular impulse per engine, static-engine thrust torque on the Frame, soft leg joints) are not separated. A decisive replay test is proposed in `hull-stabiliser-coupling.md` sec. 5.
* [open] Meaning of the arcade flag `0x147fc6fd4` and whether `creature+0xad4 > 0` identifies the player side; the engine parts' logic id 200 is inferred from the logger, not read from parts data.
* [open] Whether `AiShip_SteerController`'s separate bank-vector attitude hold (gate `+0x180c/I > 0.02`) runs for the player; irrelevant to this torque.
* Not in sources: Kormoran Frame mass/inertia (no value found), the user's definition of "headache parameter".
