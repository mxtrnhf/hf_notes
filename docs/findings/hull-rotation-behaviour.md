# Why ships spin the way they do: engine thrust, the hidden hull stabiliser, and the lurch on swivel + static designs (v1.163), measured behaviour

Written 2026-10-21 from telemetry of Lightning variants (Shipworks test flights) plus the code reads in `hull-stabiliser-engine-logic.md` and `static-engine-force-path.md`. This note is the game-facing summary: what the player sees, the numbers, worked examples, what was ruled out, and what is still open. Tags: **[code]** read from the binary, **[data]** measured in flight, **[inference]** reasoned, not proven.

## 1. What you see in the game

| Design | Hold E or Q from rest | Release all keys |
|---|---|---|
| 4 swivel engines (Lightning, statics removed) | spin rises smoothly to a plateau of **7.15 rad/s** and stays there | spin falls to about half within **0.6 s**, then coasts at about 0.05 /s |
| 2 static engines only | spin rises to a constant rate: **0.3 rad/s** with the statics near the centre, **1.6 rad/s** with them spread wide | falls to about 40% within 0.6 s, then coasts |
| 4 swivel + 2 static (stock Lightning) | spin **lurches**: 1.5 to 4.5 rad/s, once per turn, a push just after the hull points straight down | same 0.6 s drop |
| 4 swivel + 2 static, statics wide | lurches, weaker than stock | same |

Plain-physics expectation (engines at the sides, a real rigid body): the spin keeps rising while the engines fire and the hull keeps its rate when they stop. None of the rows above does that. A rigid-body model of the same hulls without the stabiliser below ends at 13 rad/s and never drops after release.

## 2. The cause: a built-in per-engine stabiliser [code][data]

Every engine part calls `Body_AddTorque` on the hull's Frame every physics step (`creatureLogic` case logic id 200, return address `0x1400357d1`). It is not a force, so it never shows in a body's force or torque accumulators. `AddTorque` changes the angular velocity at once: `w += T * 0.05^5 / I_com(Frame)` (checked: measured jump 0.0145 vs 0.0146 predicted, within 1.2%, 0.1% and 0.3% on three designs).

```
gate = creature+0x180c = 2 * min(bank-1 sum, bank-2 sum of Stats+0x100 [m_mdl_at])
frac = m_at(part) / gate
I    = Frame body alone, about its own origin = (m*|lc|^2 + I_com) / 0.05^5      (game units)
Tw   = -w * I * 0.05 * frac                     (spin damping)
Ta   = -wrap(hull angle) * I * 0.05 * frac      (pull towards level, angle 0)
if a thrust bank applied no force this tick:  Ta = 0 and Tw *= 0.5
if creature+0x15b4 (thrust history, ~30 ticks) == 0:  Tw = 0
T = clamp(Tw + Ta, +-m_at)
```
Verified at register level by logging the stabiliser's own values on every call: the logged `Tw` equals `-w * I * 0.05 * frac` with ratio 1.00000 and no scatter on about 3 100 (four swivels), 2 300 (two statics), 8 800 (stock) and 6 500 (wide statics + swivels) active rows. Where both terms are live and nothing is clamped (300, 8 460 and 2 916 rows) the logged total minus `Tw` equals `-a * I * 0.05 * frac` to the same precision. Enemy ships' calls follow the same formula (see section 6).

Properties that follow:
* **Position of the engine does not matter.** Each engine part contributes `m_at * u` whatever its place on the hull. A static near the centre gives the same stabiliser torque as one at the edge, but produces almost no turning torque.
* **Static and swivel engines both count**, in the gate and in the sum of calls. The gate is twice the weaker bank's total `m_at`.
* **It is active while the ship thrusts and for 0.6 s after.** `+0x15b4` is a rolling sum of recent thrust samples. After the last thrust it drains in a straight line and reaches zero 0.6 s later, and the case then sets `Tw = 0`. [data: drained from 6.7e7 to 0 over exactly the 0.6 s in which the torque stopped.]
* **Coasting afterwards is normal**: Box2D linear/angular damping is 0.05, set at body creation and never changed.
* **Arcade variant** [code]: if creature `+0xad4` > 0 and the arcade byte `0x147fc6fd4` is non-zero, `kd` becomes 0.02 and `kp` 0. All flights here had the normal 0.05 values.

### Worked example: four swivel engines at full effect
| Step | Value |
|---|---|
| `m_mdl_at` of one swivel engine (ENGINE_03/04) | 1e7 |
| Spin change per call: 1e7 * 0.05^5 * (1/68.45) | 0.0457 rad/s |
| Four engines, per 20 ms step | 0.183 rad/s = 9.1 rad/s^2 |
| As a torque, I * alpha (I about COM = 68.45 b2) | about 624 N*m |
| Engine thrust per engine 36e6 game units * 0.05^4 | 225 N, summed engine torque about 730 N*m |
So the stabiliser caps at about the same torque the engines make, and the spin stops climbing at the plateau.

### Gains per rad/s: code against measurement
Frame body numbers from the torque probe (mass, I about COM, offset of the COM from the body origin): four swivels 162.34 / 68.45 / 0.334 m; two statics 161.30 / 67.49 / 0.327 m; stock 166.98 / 70.85 / 0.350 m. `I` about origin = 2.77e8 / 2.71e8 / 2.92e8 game units, the values the stabiliser reads. `0.05 * I / gate` with gates 4e7 / 3e7 / 7e7:

| Design | Full gain (code) | Used | Observed |
|---|---|---|---|
| four swivels | 0.346 | 0.346 (saturated at the cap most of the time) | 0.1744 on the post-release taper (halved by the idle-bank rule on the release ticks) |
| two statics | 0.452 | 0.226 (one bank always idle: halved, `Ta` = 0) | 0.226 to 0.232 |
| stock | 0.209 | 0.209 | 0.22 on spin, 0.20 on angle |
| wide statics + swivels | 0.230 | 0.230 | consistent |

## 3. Why each design behaves as it does [data + code]

* **Swivels only: smooth.** The braking `Tw` alone exceeds the cap `m_at` above about 2.9 rad/s, so `T = +-m_at` on 84% of active ticks. The angle term has amplitude at most `kp * pi * m_at = 1.1e7`, too small to pull `T` below the cap, so it is invisible. The plateau is where the capped stabiliser torque (about 624 N*m) matches the engine torque.
* **Statics only: smooth, any position.** One static sits in the wrong half-plane for a pure rotation command, so one thrust bank applies no force on every tick: the angle term is off (`Ta` = 0) and the damping is halved. What remains is pure damping `u = -0.226 * w`, so the plateau is the engine torque divided by about 105 N*m per rad/s. Statics near the centre make 31 N*m (plateau 0.3 rad/s), statics wide make 178 N*m (1.6 rad/s). The plateau follows the lever arm, as it would for a rigid body with simple drag.
* **Swivels plus statics: the lurch.** The gate is 7e7, so the gain is lower (0.21) and the braking is not at the cap. Both banks fire, so the angle term is live. `Ta = -0.20 * wrap(angle) * m_at` pulls the hull back towards level and flips sign where the wrapped angle jumps from +pi to -pi. At that point each swivel call's torque changes by about 1.2e7 in one step. The six calls (four swivels, two statics at 1.5x weight) add up to about 8.3e7, a push of 0.38 rad/s in 20 ms (about 19 rad/s^2). The spin climbs, is pulled back, then jumps once per turn. With the statics spread wide the lurch is weaker in flight (gain 0.23 against 0.21, Frame inertia about COM 81.6 against 70.9) but still there; why it weakens was not isolated [inference].
* **Why the lurch starts "just after pointing down".** Spin climbs against the level-seeking pull from angle 0 up to 180 degrees; past 180 degrees the same pull helps the rotation instead of resisting it.

Idle-bank statistics on the player's active ticks: four swivels 8.5%, two statics 100%, stock 4.1%, wide statics + swivels 7.7%.

## 4. What was ruled out [data]
* **Physics engine behaviour**: Box2D step, solver and damping are stock (see `box2d-physics-setup.md`). The only change in spin between one step's exit and the next step's entry is the `AddTorque` jump.
* **Antenna chains**: 24 welded ghost bodies (mass 1.25e-10) were tested; designs with the antennas deleted give the same plateau and the same lurch.
* **Contacts**: zero touching-contact rows in the constant-spin window.
* **Joint motors**: gun motors had a motor impulse of about 1e-5 in a 1.6 rad/s spin; leg joints under 0.2 N*s.
* **Hull air drag** (`Body_PreStepUpdate`): about 15 N*m at 50 u/s against 700 to 900 N*m of engine torque; real but irrelevant to rotation.
* **Engine force application**: `Body_AddForceAtPoint` applies each engine force correctly at the part centre; the engine joints pass 90 to 105% of it to the hull.
* **AI attitude hold** (`AiShip_SteerController`): a separate system run from the AI list only [code; one detail about list registration is unverified, see `player-attitude-stabiliser.md`]. It is not this stabiliser.

## 5. Consequences
* **Design guidance.** A ship's turn rate is set by two things only: the engines' turning torque (lever arm times thrust) and the stabiliser's cap `sum(m_at)`. The `m_mdl_at` values (OL.seria): ENGINE_01 and 02 7e7, ENGINE_03 and 04 1e7, ENGINE_05 1.5e7, ENGINE_06 4e6. More or heavier engines raise both the gate and the cap; the gain `0.05 * I / gate` falls as the gate rises. A big hull with a small gate has a large gain and saturates the cap.
* **To remove the lurch** on a swivel + static design [inference, not flown]: make it saturate (lower gate: fewer or lighter angular-thrust parts), or keep a bank idle in a rotation (statics on one side only).
* **Players' description** ("anti-tilt", `m_mdl_at`, "applies every frame while an engine produces thrust, regardless of where it is, remove it and the ship is uncontrollable") matches this note.
* **A test flight that would confirm** [not flown]: set `m_mdl_at` to 0 on the engines in OL.seria (back the file up first), fly the four-swivel Lightning, hold E for 5 s and release. Prediction from the rigid-body model: the spin runs to about 13 rad/s and, after release, coasts at about 0.05 /s with no 0.6 s drop. AI ships lose their stabiliser and their attitude hold (the gate comes from `m_at`), so fly with no enemies.

## 6. AI ships get it too [data]
The probe's calls from the enemy ship (gate 2e7, `m_at` 1e7 per call, I = 1.0e8 to 1.2e8) follow the same formula to five digits. AI ships therefore have this stabiliser on top of the steering attitude hold in `AiShip_SteerController`; any analysis of AI hull motion has to include both.

## 7. Open
* **Frame body origin rule**: `I` uses the offset of the COM from the Frame body's origin (0.334 / 0.327 / 0.350 m measured). The offset implied by the design file's coordinates differs on two of the three designs (0.514 against 0.327, 0.454 against 0.350). Where the game puts the body origin for an arbitrary design is not established; it is needed to predict a new hull from its design file alone.
* **Ship classes beyond Lightning**, and campaign or arcade battles. All flights were Lightning variants in Shipworks test flights. A thrust-scaling rule in `Engine_ApplyThrustForce` (factor `f(X)` gated to editor and test flights, see `static-engine-force-path.md`) was not needed for the rotation but may matter for linear motion.
* **How the solver redistributes the impulse** to engines, legs and guns that sit on their own joints in the steps after the Frame's jump. A model that lets the whole welded assembly absorb the impulse reproduces 14 flights; a sweep of that share from 0 to 1.3 has a flat optimum at 0.85 to 1.0. A direct measurement was too confounded by engine force. Not proven.
* **Lurch period on long runs**: the model's lurches come about 10% faster than the game's after a few turns, so the angle drifts over tens of seconds. Short windows (2 to 5 s) are accurate. The cause is not found.

## 8. Evidence
* Telemetry probe files: per-step torque and body states for the player's bodies, hook rows for every `AddTorque`, `AddForce*` and `SetAngularVelocity` call on the hull with the caller address, per-step creature fields (`+0x17fc`, `+0x1800`, `+0x15b4`, `+0x180c`, `+0xbc4`), per-engine-part rows, and the stabiliser's own register values. The enemy ship's calls appear in the same rows; they were filtered out before the numbers above.
* Flights: four-swivel (5), statics-only wide (3 plus one close), stock (5), wide statics + swivels (1), 14 sessions in the validation.
* Check of the formula against logged flights from key presses alone, no fitted gain, reset every 5 s, median per session: spin error 0.00 to 0.40 rad/s with the stabiliser against 2.6 to 10.5 without, hull angle error 0.05 to 1.3 rad. A held-out design (statics wide plus swivels) was predicted to 0.07 rad/s.
* Related notes: `hull-stabiliser-engine-logic.md` (the decompile), `static-engine-force-path.md` (force path and frame drag), `player-attitude-stabiliser.md` (AI attitude hold and who reads `+0x180c`), `box2d-physics-setup.md`, `box2d-struct-layouts.md`.
