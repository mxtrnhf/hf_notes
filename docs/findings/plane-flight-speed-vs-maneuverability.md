# Plane flight: speed vs maneuverability (1.163, static analysis)

Status: **[V]** verified from static disassembly and decompilation in Ghidra 1.163 on 2026-11-01 (image base `0x140000000`); **[file]** checked against `OL_stock.seria` / `parts.seria`. **No DLL was built and no game file was changed.**

Question: in the current plane code, maneuverability depends on speed. Is it possible to make "maneuverability" (how sharp a plane can turn) and speed independent, adjustable variables?

Answer: **Yes, with a small hook — not by data alone.** Speed is already a per-craft data stat (`m_launched_speed` at `Stats+0x158`), whereas maneuverability is not a stat: it is hardcoded inside `Aircraft_ApplyFlightForces` (`0x140009db0`). Because the forward thrust impulse is proportional to `(speed * dt)^2`, the plane's angular turn rate is proportional to its speed (`omega ∝ speed`), while its turn radius (`R = v / omega`) is already independent of speed. A hook at the impulse call (`0x14000a2a3`) can scale the perpendicular impulse independently of speed.

---

## 1. Per-tick flight pipeline (`logic = 500`)

Every physics frame (`dt = 0.02 s`), `creatureLogic` dispatches logic-500 bodies at `0x140038f7c` (`MOV RCX, [RSI+0xa20]; CALL 0x14000f7a0`):

| Step | Address | Function | Role |
|---|---|---|---|
| 1 | `0x140038f7c` | `creatureLogic` (case 500) | Loads `AircraftLogic*` from `body+0xa20` and calls `AircraftLogic_Tick`. |
| 2 | `0x14000f7a0` | `AircraftLogic_Tick` | Skips parked planes (state `+0x190` in `{6, 7}`). Builds the stack state block from `body = *(logic+0x50)` and runs steps 3–6. |
| 3 | `0x14000fbc0` | `aircraftStateHandler` | Selects/updates target link `logic+0x150` (`+0x158`) based on mode `logic+0x118`. |
| 4 | `0x14000b370` | `AircraftLogic_Update` | Dispatches on mode `logic+0x118` (`0, 1, 2, 3, 4, 5, 6`) and returns the desired world heading in `XMM0`. |
| 5 | `0x14000e6a0` | `Aircraft_SelectAvoidanceHeading` | Checks level bounds (`logic+0x194..0x1a0`) and runs 2-second lookahead rollouts via `Aircraft_SimulateTrajectoryRollout` (`0x140007de0`) and escape-angle search `Aircraft_SearchEscapeHeading` (`0x14000f2a0`). Writes the chosen target heading to `logic+0x70` and the turn-direction sign (`0` = CCW, `1` = CW) to byte `logic+0x74`. |
| 6 | `0x140009db0` | `Aircraft_ApplyFlightForces` | Called at `0x14000f9ca` with `(RCX=logic, RDX=&state_block, XMM2=[logic+0x70], R9B=1, [RSP+0x20]=[logic+0x74])`. Clamps the heading step, calls `Aircraft_UpdateSpeed`, computes the 2D linear impulse, and applies the body-angle PD torque. |
| 7 | `0x14001baf0` | `Body_ApplyLinearImpulseAtCenter` (vtable `+0x190`) | Called at `0x14000a2a3`. Multiplies the impulse by `0.05^4` and calls `b2Body_ApplyLinearImpulse` (`0x140018c40`). |
| 8 | `0x140019be0` | `Body_AddTorque` (vtable `+0x1a0`) | Called at `0x14000a308` when `param_4` (`R9B`) != 0. Rotates the sprite/body angle (`body+0x138`) to track the velocity vector. |

---

## 2. How speed is represented and updated

### 2.1 Initialization at launch
In `loadAmmoForAircraft` (`0x14002e930`):
- At `0x14002ee18..0x14002ee28`, the code calls `GetStats(*(int *)(plane + 0x188))` (`0x140281e00`) and reads float `Stats+0x158` (`m_launched_speed`) into `XMM7`.
- At `0x14002ee40..0x14002ee4a`, it passes `XMM1 = XMM7` to `AircraftLogic_InitAndPickMode` (`0x14000ae90`).
- At `0x14000af66..0x14000af70`, `AircraftLogic_InitAndPickMode` writes that value into three contiguous floats on `AircraftLogic`:
  - `logic + 0x64`: base nominal speed (`m_launched_speed`)
  - `logic + 0x68`: current ramped speed scalar
  - `logic + 0x6c`: target speed scalar

Stock values in `OL_stock.seria`:
- `CRAFT_LA29`: `m_launched_speed = 220`
- `CRAFT_T7`: `m_launched_speed = 350`

### 2.2 Per-tick speed update (`Aircraft_UpdateSpeed` `0x14000a620`)
Called only from `Aircraft_ApplyFlightForces` at `0x14000a0d0` with `(RCX = logic, RDX = &hdir, R8 = &velocity)`:
1. **Base target speed (`logic+0x6c`)** from `base = *(float *)(logic + 0x64)`:
   - Mode `0` (`logic+0x118 == 0`, fighter): `target = base * 1.1` (`0x1403527bc` = `1.1f`)
   - Mode `1` (`logic+0x118 == 1`, retirement): `target = base * 0.9` (`0x1403527b0` = `0.9f`)
   - Modes `2..6`: `target = base`
2. **Dive bonus**: `RDX` points to the 2D unit heading vector `hdir = (sin(param_3), -cos(param_3))`. In HighFleet combat coordinates `+y` is downward, so `*(float *)(RDX + 4) = -cos(param_3) > 0` when the nose points below horizontal. When `hdir.y > 0`, `target += hdir.y * 100.0` (`0x1403524e0` = `100.0f`).
3. **Egress floor**: in modes `!= 1`, if state `logic+0x190 == 5` (`STATE_TO_OUT_OF_SCREEN`), `target = max(target, 400.0)` (`0x140352834` = `400.0f`).
4. **Ramp (`logic+0x68`)**: steps `current = *(float *)(logic + 0x68)` toward `target`:
   - If `|target - current| <= 1.0`: `current = target`
   - If `current < target`: `current += 1.0` (or `+0.25`, `0x14035279c`, when `state == 5` and `|v|^2 > base^2`)
   - If `current > target`: `current -= 0.5` (`0x1403527a4` = `0.5f`)
5. **Return value**: `max(current, 100.0)` in `XMM0`.

---

## 3. How turning works and why it depends on speed

All turning physics live in `Aircraft_ApplyFlightForces` (`0x140009db0`).

### 3.1 Velocity heading and desired heading difference (`0x140009de9..0x140009f02`)
1. Reads `vx = body->velocityX` (`+0x130`), `vy = body->velocityY` (`+0x134`), speed `v = sqrt(vx^2 + vy^2)`, and unit velocity `vdir = (vx/v, vy/v)`.
2. Computes the current velocity heading `theta_v`:
   - If `v > 5.0` (`0x140352810`): `theta_v = vectorCalculateAngles_(&vdir) = atan2f(vdir.x, -vdir.y)` (`0` = straight up, `+pi/2` = right, `+-pi` = down).
   - If `v <= 5.0`: keeps the previous `*(float *)(logic + 0x70)`.
   - Stores `theta_v` into `logic + 0x70`.
3. Computes the wrapped angular error `delta = Math_NormalizeAngleDifference(theta_v, param_3)` in `(-pi, pi]`.
4. Applies the forced turn direction `param_5` (`logic + 0x74`):
   - If `param_5 == 0` and `delta > 0`: `delta -= 2*pi` (`0x140352864` = `-6.2831855f`)
   - If `param_5 != 0` and `delta < 0`: `delta += 2*pi` (`0x140352814` = `+6.2831855f`)

### 3.2 Per-tick heading step clamp (`0x140009f02..0x14000a05c`)
Next, the code limits how far the commanded thrust heading `param_3` can lead the current velocity heading `theta_v` on a single tick:
- If `*(byte *)(logic + 0x88) == 0` (always `0` in stock: initialized to `0` at `0x14000ae44` and `0x14000b05f`, never written elsewhere):
  - `f = clamp(max((|delta| - 0.34906587) / 2.792527, dist_to_attack_pt / 300.0), 0.0, 1.0)`
    where `0.34906587 rad = 20 deg` (`0x1403527a0`), `2.792527 rad = 160 deg` (`0x140352800`), `300.0` is at `0x140352830`, and `attack_pt` is `state_block + 0x38/+0x3c`.
  - `divisor = (int)((1 - f) * 20.0 + f * 10.0)` (integer in `10..20`)
  - `min_step = (1 - f) * 0.10471976 + f * 0.17453294` (`6 deg` to `10 deg`; `0x140352790` = `6 deg`, `0x140352794` = `10 deg`)
  - `max_step = 0.17453294` (`10 deg`)
- If `*(byte *)(logic + 0x88) != 0`:
  - `divisor = 10`, `min_step = max_step = 0.17453294` (`10 deg`).
- If `state (logic + 0x190) != 0` and `|delta| >= min_step`:
  ```c
  step = clamp(|delta| / (float)divisor, min_step, max_step);
  param_3 = theta_v + copysign(step, delta);
  ```
  When `state == 0` (carrier takeoff / deck-clearance toward horizontal world heading `logic+0xd0 = +-pi/2`), `0x14000a00e` (`CMP dword ptr [RBX + 0x190], 0x0; JZ 0x14000a059`) skips the `6..10 deg` clamp; in all active flight states (`state != 0`), `delta_cmd = Math_NormalizeAngleDifference(theta_v, param_3)` is clamped to at most `10 deg` (`0.17453294 rad`).

### 3.3 The linear impulse formula and exact Box2D scaling (`0x14000a059..0x14000a2a3`)
Let:
- `hdir = (sin(param_3), -cos(param_3))` be the unit vector along the clamped heading `param_3`
- `vdir = (vx / v, vy / v)` be the unit vector along the current velocity
- `delta_cmd = Math_NormalizeAngleDifference(theta_v, param_3)` be the clamped heading lead angle (`|delta_cmd| <= 10 deg` for `state != 0`)
- `s = Aircraft_UpdateSpeed(...)` be the ramped speed scalar
- `dt = time_related_global_` (`0.02 s` at `50 Hz`)

`Aircraft_ApplyFlightForces` computes (`0x14000a0d5..0x14000a29a`):
```c
T2 = powf(|delta_cmd| + 1.0f, 2.0f);          // 0x14000a1eb..0x14000a1fb
T3 = powf(2.0f * |delta_cmd| + 1.0f, 3.0f);   // 0x14000a0f8..0x14000a109

brake_vec  = -vdir * (0.5f * powf(v * dt, 2.0f) * T3);
// Clamped at 0x14000a1c4 so |brake_vec| <= |b2b->m_linearVelocity| / 0.05 (== v):
if (|brake_vec| > |b2_vel| / 0.05f)
    brake_vec = -b2_vel;

thrust_vec =  hdir * (0.5f * powf(s * dt, 2.0f) * T2);

dv_vec     = thrust_vec + brake_vec;
impulse    = dv_vec * returnMass(body);       // stored at [RSP+0xf0], [RSP+0xf4]
body->vfTable[+0x190](body, &impulse);        // 0x14000a2a3 -> 0x14001baf0
```

**Exact cancellation of mass and `0.05` factors (`[V]`):**
- `returnMass(body)` (`0x1400486e0`) returns `body->mass` (`+0x1d8`), which `Body_UpdateMassFromB2` (`0x140054b80`) sets to `m_b2 / 0.05^3`.
- Vtable `+0x190` (`0x14001baf0`) multiplies `impulse` by `0.05^4` and calls `b2Body_ApplyLinearImpulse` (`0x140018c40`), which multiplies by `1 / m_b2`:
  `Δv_b2 = dv_vec * (m_b2 / 0.05^3) * 0.05^4 * (1 / m_b2) = dv_vec * 0.05`.
- After `b2World_Step`, `Body_SyncFromB2` (vtable `+0x160`, `0x140054bf0`) writes `body->velocity = b2b->m_linearVelocity / 0.05`:
  `Δv_game = Δv_b2 / 0.05 = dv_vec`.

Thus `dv_vec` is **literally the per-tick velocity change `Δv` in game units/second**.

### 3.4 Why turn rate scales with speed (and why hard turns bleed speed)
Decomposing `dv_vec` into components parallel and perpendicular to `vdir`:
```
Δv_par  = 0.5 * dt^2 * [ s^2 * T2 * cos(delta_cmd) - v^2 * T3 ]
Δv_perp = 0.5 * dt^2 * [ s^2 * T2 * sin(delta_cmd) ]
```

From these two equations:
1. **Built-in turn speed bleed (`T3 > T2`)**:
   - In straight flight (`delta_cmd = 0`), `T2 = T3 = 1`, so `Δv_par = 0` when `v = s`.
   - At the `10 deg` clamp (`|delta_cmd| = 0.17453294 rad`), `T2 = 1.3795` while `T3 = 2.4553`.
   - In a sustained `10 deg` turn, `v` settles where `|v * vdir + Δv| = v`, which occurs at:
     `v_turn ≈ s * sqrt(T2 * cos(10 deg) / T3) = 0.7445 * s`
     (a ~25.5% speed bleed during sustained max-rate turns: `220 -> 163.8 u/s` for LA-29, `350 -> 260.6 u/s` for T-7).
2. **Angular turn rate `omega` is proportional to `s`**:
   ```
   omega = atan2(Δv_perp, v + Δv_par) / dt ≈ Δv_perp / (v * dt)
         = 0.5 * dt * T2 * sin(delta_cmd) * (s^2 / v)
   ```
   With `dt = 0.02 s` and `|delta_cmd| = 10 deg` (`0.5 * dt * T2 * sin(10 deg) = 0.0023956 rad/u = 0.13726 deg/u`):
   - **Initial turn rate** (at turn entry, `v = s`):
     `omega_init = 0.1373 * s deg/s` (`30.2 deg/s` at `s = 220`, `48.0 deg/s` at `s = 350`)
   - **Sustained turn rate** (at `v = 0.7445 * s`):
     `omega_sust = 0.1844 * s deg/s` (`40.6 deg/s` at `s = 220`, `64.5 deg/s` at `s = 350`)
3. **Turn radius `R = v / omega` is independent of `s`**:
   - **Initial turn radius** (`v = s`): `R_init = s / omega_init = 417.4 units` for both planes.
   - **Sustained turn radius** (`v = 0.7445 * s`): `R_sust = v_turn / omega_sust = 231.3 units` for both planes.

### 3.5 Body-angle PD controller (`0x14000a2a9..0x14000a308`)
When `param_4` (`R14B`) != 0, `Aircraft_ApplyFlightForces` rotates the body sprite/collision angle (`body+0x138`) toward the velocity angle:
```c
ang_err = Math_NormalizeAngleDifference(body->angle, vectorCalculateAngles_(&body->velocity));
torque  = Body_GetInertiaAboutOrigin(body) * (20.0f * ang_err - body->angleVelocity);
body->vfTable[+0x1a0](body, torque);   // Body_AddTorque (0x140019be0)
```
This only aligns `body->angle` with `body->velocity`; it does not steer the trajectory.

### 3.6 Important caller detail: the obstacle predictor (`0x140007de0`)
The function at `0x140007de0` (`Aircraft_SimulateTrajectoryRollout`, formerly mislabelled `rep_1400078b0_WriteToClientLogAircraftLogic` in Ghidra) is **not** a logger: it is the **100-step (2.0 s) forward trajectory simulator** used by `Aircraft_SelectAvoidanceHeading` (`0x14000e6a0`) and `Aircraft_SearchEscapeHeading` (`0x14000f2a0`).
- It saves `body->velocity`, `b2b->m_angularVelocity`, `logic+0x68`, and `logic+0x6c`.
- It calls `Aircraft_ApplyFlightForces(logic, state_block, candidate_heading, 0, turn_sign)` in a loop up to `2.0 / dt = 100` steps (`param_4 = 0`), reading back `b2b->m_linearVelocity / 0.05` after each step to advance a simulated position and test against terrain bounds (`logic+0x78..0x84`) and obstacle circles from `Aircraft_CollectAvoidanceObstacles` (`0x1400085d0`).
- At the end it restores `logic+0x68`, `logic+0x6c`, `b2b->m_angularVelocity`, and `body->velocity`.

This has two major consequences for modding:
1. Any hook inside `Aircraft_ApplyFlightForces` (such as `0x14000a2a3`) automatically runs inside the 2-second obstacle predictor too, so the AI's terrain/ship avoidance lookahead matches the modified turn sharpness.
2. Because `0x140007de0` calls `Aircraft_ApplyFlightForces` 100–200 times per tick per plane (and up to ~6,000 times if `0x14000f2a0` sweeps 62 escape angles), a hook inside `Aircraft_ApplyFlightForces` **must be lock-free and allocation-free**. If the hook ever needs to distinguish the real physics tick from lookahead rollouts, `R14B` (`param_4`) is `1` on the real tick (`0x14000f9ca`) and `0` in all lookahead rollouts.

---

## 4. Can speed and maneuverability be made independent?

### 4.1 Why data-only (`OL.seria`) is not enough
- `Stats+0x158` (`m_launched_speed`) is the only aircraft stat read by the flight code. Changing it (or scaling `logic+0x64/+0x68/+0x6c`, as `hf_ally`'s `plane_aa_speed` does) scales both flight speed and turn rate together.
- `Stats+0x174` (`m_missile_agility`) **is** registered unconditionally on every `Stats` object as a `float` (default `0.0` in `Stats_ConstructorDefault` `0x140281e30`, property `"m_missile_agility"` bound to `RDI+0x174` at `0x140283663` in `populateObjects`, read by `Part_GetAgility` `0x140048810`), but its only callers in stock 1.163 are `0x1400368c3` (missile guidance) and `0x1400ed1e3` (`initProfileMissiles`). No aircraft function calls `Part_GetAgility`.

### 4.2 Two definitions of independent "maneuverability"
Because `omega = v / R`, making speed and maneuverability independent depends on which quantity you want the maneuverability knob `M` to control:

| Mode | What `M` controls | Perpendicular impulse multiplier `A` | Turn radius `R` | Turn rate `omega` |
|---|---|---|---|---|
| **1. Independent turn radius (arc tightness)** | Turn sharpness in space (`R = R_vanilla / M`) | `A = M` | **`231 / M` units** (independent of speed) | `40.6 * M * (s / 220) deg/s` (scales with speed) |
| **2. Independent turn rate (nose swing speed)** | Angular rate in time (`omega = omega_ref * M`) | `A = M * (v_ref / s)` (or `M * (v_ref / v)`) | Scales with speed (`R = v / omega`) | **`40.6 * M deg/s`** for `v_ref = 220` (independent of speed) |

Both can be supported simultaneously with two per-plane config values:
- `speed` (or `speed_multiplier`): sets `logic+0x64/+0x68/+0x6c` (or `Stats+0x158`).
- `maneuverability` (`M`): scales the perpendicular component of the flight impulse at `0x14000a2a3`.

---

## 5. Recommended hook design (`0x14000a2a3`)

### 5.1 Hook site and live registers
At `0x14000a2a3` inside `Aircraft_ApplyFlightForces`:
```
14000a290: f3 0f 11 94 24 f0 00 00 00   MOVSS dword ptr [RSP + 0xf0], XMM10   ; impulse.x
14000a29a: f3 0f 11 bc 24 f4 00 00 00   MOVSS dword ptr [RSP + 0xf4], XMM7    ; impulse.y
14000a2a3: ff 90 90 01 00 00            CALL  qword ptr [RAX + 0x190]         ; 6 bytes, no RIP-rel
14000a2a9: 45 84 f6                     TEST  R14B, R14B
```
Live registers at `0x14000a2a3`:
- `RDI` = `Body*` (plane body; `velocity` at `+0x130/+0x134`, `stats_index` at `+0x188`)
- `RBX` = `AircraftLogic*` (`base_speed` at `+0x64`, `ramped_speed` at `+0x68`, `target_heading` at `+0x70`)
- `RAX` = `Body` vtable pointer
- `R14B` = `param_4` (`1` on real tick, `0` inside `0x140007de0` lookahead rollout)
- `[RSP + 0xf0]`, `[RSP + 0xf4]` = `impulse.x`, `impulse.y` (`dv_vec * mass`)

### 5.2 Fast per-craft storage (zero-lock, safe in rollouts)
Because `Stats_ConstructorDefault` (`0x140281e30`) initializes `Stats+0x174` (`m_missile_agility`) to `0.0f` on every `Stats` record and `populateObjects` (`0x140283663`) already parses `m_missile_agility` from `OL.seria` for any part:
- A mod (or `OL.seria`) can store the plane's maneuverability multiplier directly in `Stats+0x174` (`m_missile_agility`), or in a small static array indexed by `*(uint32_t *)(RDI + 0x188)` (the plane's `Stats` index).
- If the value is `<= 0.0` (unconfigured), treat `A = 1.0` (vanilla).
- Reading `Stats+0x174` via `GetStats(*(int *)(RDI + 0x188))` (or a static array by stats index) takes a few instructions, requires no heap or lock, and works identically during the 100-step obstacle-avoidance rollout.

### 5.3 Impulse decomposition at `0x14000a2a3`
```c
float vx = *(float *)(body + 0x130);
float vy = *(float *)(body + 0x134);
float v2 = vx * vx + vy * vy;
if (v2 > 1.0f) {
    float inv_v = 1.0f / sqrtf(v2);
    float ux = vx * inv_v;
    float uy = vy * inv_v;

    float ix = impulse->x;
    float iy = impulse->y;
    float par = ix * ux + iy * uy;      // throttle / turn-bleed component along velocity
    float px  = ix - par * ux;          // turning component perpendicular to velocity
    float py  = iy - par * uy;

    // Mode 1 (radius multiplier M): A = M
    // Mode 2 (speed-independent turn rate): A = M * (v_ref / *(float *)(logic + 0x68))
    px *= A;
    py *= A;

    impulse->x = par * ux + px;
    impulse->y = par * uy + py;
}
```
Why this works cleanly:
- The parallel impulse `par` is untouched, so straight-line acceleration, top speed (`logic+0x68`), dive bonus, state-5 egress speed, and the ~25.5% turn speed bleed (`T3` vs `T2`) remain vanilla.
- Only the perpendicular impulse `(px, py)` is scaled by `A`, directly scaling `Δv_perp` and therefore `omega` (by `A`) and `R` (by `1 / A`).
- For `A <= 4.0`, the single-tick velocity rotation at `10 deg` clamp is `~0.8 * A deg` (`<= 3.2 deg/tick`), which stays well inside the `10 deg` heading lead `delta_cmd` and never overshoots `logic+0x70`.
