# Zenith (guided missile) steering law (v1.163), 2026-10-21

Tags: **[V]** read in the 1.163 program (disassembly + decompile of the helpers); **[guess]** inference. Read-only: nothing was renamed or commented in Ghidra. Continues the "steering law still open" item of [flares-and-missiles.md](flares-and-missiles.md) section 4. `creatureLogic` has no Ghidra function around these addresses, so everything below comes from `disassemble_bytes` of `0x140035f50..0x1400372c0`.

"Zenith" = `MDL_MISSILE_01`, logic id 1, `creatureLogic` state `+0x3cc == 2` (flight). Self = the missile body (`RSI`), `EBX` = logic id.

## 1. The final output: a PD torque plus a force [V]
Last lines of state 2 (`0x1400371e7..0x140037286`):

```
omega  = body +0x13c                         (angular velocity)
force  : vtable+0x178(self, dir * body[+0x1d8])       // only if dir.x and dir.y are finite (0x1400152e0)
target angle : angle of vector V measured from (0,-1) ("up", heading 0 points up, y is down)
err    = wrap(angle - heading[+0x138], -pi, pi)
torque = I * ( 20.0 * err  -  omega )        // I = [rsp+0x78]; 20.0 = const 0x140352820
         vtable+0x1a0(self, torque)           // only if the sum is finite
```
* `I` = `FUN_140048440(self)` (the same "turn/inertia scale" the AI ship tick reads, see steering_spec). `[rsp+0x7c]` = body `+0x1d8` is the force scale (looks like mass; **not verified**).
* So the missile has an ordinary **critically-ish damped PD controller on heading**: Kp = 20, Kd = 1 (in torque per unit inertia). No agility term here; agility acts on the aim, see 2.
* `V` is the commanded velocity. `COMISD (double)[+0x3d4], 0.3` then `JBE 0x140037214` (re-checked): while the timer `+0x3d4 > 0.3` the missile points along `V = dirRef * speed2` (the desired velocity); once `+0x3d4 <= 0.3` it points along its **own velocity** (`+0x130`) [V].
* `+0x1d8` is the body **mass** (box2d-physics-setup.md), so `force = mass * (dirRef * speed2 - v)` is a velocity P-controller with gain 1/s: acceleration = (desired velocity - velocity) per second [V]. Frame time `0x1403c126c` = 0.02 s [V].
* State 4 (the tumble after giving up, `0x1400360de`) uses the same shape with gains 0.5/0.5: `torque = I * 0.5 * (wrap(wrap(angle) - heading) - omega)` (`0x1403527a4` = 0.5) [V].

## 2. The aim point: constant-speed intercept ("lead") [V]
Stack of steps before the torque (`0x1400365b1..0x140036b5f`):
1. Target point = the aim object's position (`aim +0x1840`, the flare's owner position if a flare is locked, see the seeker section of flares-and-missiles.md), target velocity `aim +0x130` (`[rbp+0x58]`), aim radius `aim +0x20c`.
2. `dist = |target - self|` (`FUN_140018e70`, `XMM11`).
3. Speed for the lead: `speed2 = Stats +0x15c` (`FUN_140048640`). For logic id 1 it is used as is; id 4 multiplies by 5.0 (`0x140352810`), other ids by 3.5 (`0x1403547c4`). The divisor `[rbp-0x80]` is 1.0 for id 1, else 2.5 (`0x1403547b0`).
4. If `dist > 5.0` (`XMM14` = 5.0 at `0x1400367be`, test at `0x1400369a0`): call `0x14022c250(out, selfPos, speed2/div, targetPos, targetVel)`. It is the textbook **intercept solver**: ratio `s = speed / |targetVel|`, rejects `s > 50` or `|targetVel| < 1`, quadratic `(1 - s^2) t^2 + 2 d cos(theta) t ...`, takes the smallest positive root, `out = targetPos + unit(targetVel) * t` (decompiled; the variables are named oddly but the quadratic and the `cos(atan2(...))` term are in the .c). If there is no real/positive solution it returns the plain target position. After it, if `|out - self|^2 > 2.5e6` (`0x1403548f8`, i.e. 1581 u) the code falls back to the unit vector to the plain target (`0x1400369e1..0x1400369f2`) [V].
5. If `dist <= 5.0` (and above 1e-4, below 0.1: `0x1403546e0`, `0x140354770` doubles) the aim is the straight unit vector to the target (pure pursuit) [V: structure, thresholds read].
6. `dir = unit(out - self)` is then **rotated into a reference heading**: `+0x3d8` (heading reference) is advanced `ref = wrap_2pi(ref + (1.0 - t3d4) * errorAngle)`, where `errorAngle` is the wrapped angle between the current reference and the bearing (`0x140036b3e..0x140036da9`; `+0x3d4` is the timer counted down by dt, floor 0). `dirRef = rotate((0,-1), ref)` (`0x140019480`) is what the thrust `dir` above comes from [V structure; the meaning of `(1 - t3d4)` as a "seeker warm-up" is a **[guess]**: if `t3d4` can exceed 1 the factor turns negative].
7. **Turn-rate limit [V]:** for logic id 1 the bearing error `XMM15 = wrap(bearing(aim) - ref)` is clamped (`FUN_14001c7b0`, `0x140036d55..0x140036d65`) to `+-A`, `A = agility * dt * [+0x3dc]` (`Stats +0x174` = `m_missile_agility`, 4/5/10 in OL.seria; dt = 0.02), before step 6 applies it. So the reference heading turns at most `agility * [+0x3dc]` rad/s (10 rad/s for agility 10). `+0x3dc` is 1.0 normally and 0.2 in the terminal phase (set to 0.2 at `0x1400370d4` when the missile is aligned, error < pi/20 = 0.157 rad `0x1403546a0`, and close; set back to 1.0 when the distance > 150, `0x14003719c`).
8. **Launch clearance [V]:** if the owner ship (`+0x4b0`) is alive and the missile is closer than `1.5 * owner +0x1850` (`0x1403527cc`) to it, the aim direction is replaced by the direction missile->owner rotated by `sign(angle) * pi * 0.75` (135 degrees, `0x14035470c`), sign = side of the previous aim relative to the owner (`0x140036a5a..0x140036ae5`). The `3pi/2` compare (`0x1403547e4`) is always true. So a fresh missile veers off its own ship's hull before homing.

**Seeker cone and lock loss [V]:** `cone_eff = 0.5 * radar_cone * (|v| / speed2)^2` (`Stats +0x17c`). The flag `EDI` is 1 only when `dist - aimRadius <= 100` and `|bearing error| >= cone_eff`; if the aim object is the primary target and `EDI` is set, the primary link `+0x490` is cleared (`0x140036b74..0x140036b88`): a missile that is close and still pointing too far off the bearing loses the target.

## 3. Facts you can use right now
* The torque law is a PD on the heading angle with Kp 20 and Kd 1 times the body inertia scale: heading follows the commanded direction with a time constant of roughly 0.2 s, not instantly. A turn-rate cap is **not** present in this tail; any limit comes from the saturating force scale and from the `agility` factor on the reference heading.
* Lead pointing is only done when `dist > 5` and the solver has a real root; inside 5 u it points straight at the target, and beyond 1581 u of lead it points straight at the target.
* Ids other than 1 (rockets, id 4 AA missiles) use speed x 3.5 / x 5 in the solver, so they lead for a different (faster) speed than a Zenith.

## 4. Still open
1. The `[+0x3dc] == 1.0` side block `0x140036f68..0x1400370de` (it only decides when `+0x3dc` drops to 0.2; its inputs are |v| direction vs the velocity error, not read line by line).
2. Observed top speed 276 u/s vs `speed2`: with force = mass * (desired - v) the speed settles at `speed2` only if drag and the 0.05 damping are small; check `speed2` for the Zenith in OL.seria.
3. `+0x3d4` start value for the Zenith (set at launch), to settle the `(1 - t3d4)` factor; it also gates the 0.3 s switch in section 1.
4. A runtime check: the probe could log `+0x3d8`, `+0x138`, `+0x13c` and the `dist` once per frame for a Zenith to confirm Kp = 20.
