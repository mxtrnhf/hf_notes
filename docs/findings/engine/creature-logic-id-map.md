# `creatureLogic` (0x140033b90) dispatch: logic id (+0x3c4) to code block (v1.163), ghidra-miner, 2026-10-21

Tag **[V]** (jump and byte tables read from the image). `creatureLogic` is vtable `+0x1e8` of a body; `Part_UpdateDispatch` `0x140054b20` calls it every tick after `Part_Tick` when `+0x3c8` (m_logic_active) is non-zero. Dispatch: `id = [body+0x3c4]`; `id > 400` jumps to `0x140038d27`; `id == 400` to `0x140038767`; otherwise `idx = byte[0x140045170 + (id - 1)]` (ids 1..210, others fall to idx 16) and the target is `0x140000000 + dword[0x14004512c + 4 * idx]`.

| logic id | block | what it does |
|---|---|---|
| 1, 3, 4 | `0x140036024` | missile / rocket logic (ejection `0x140035e3b..`, fuze block `0x140036780`, see flares-and-missiles.md) |
| 2 | `0x14003798d` | not read |
| 10 | `0x140037fb7` | not read |
| 100 | `0x140033d47` | **plain cannon shell**: arming (`+0x3d0 = 20/|v|`, then `+0x38c = 25 * mass`), no spin, align to velocity; see shell-detonation-paths.md |
| 110 | `0x140033ce8` | timed fuse: state 0 `+0x3d0 = +0x3d4`; state 1 `Body_DieExplode` when the timer is spent |
| 120 | `0x140033c5a` | delayed warhead: state 0 `+0x3d0 = +0x3d4`-style delay, then `+0x38c = 10000.0`, `+0x2dc = +0x3d8`, logic id := 0 |
| 130 | `0x1400348be` | **rocket** (ammo 51/52/55): thrust 500*mass for 1.5 s, cone/range cluster burst; weapons-index.md s5.2 |
| 132 | `0x140034b78` | **300 mm rocket** (ammo 54): heading lag to launcher angle, closest-approach fuze, 5..50 bomblets; weapons-index.md s5.3 |
| 135 | `0x140035553` | missile arming: state 0 `+0x3d0 = 0.05`, state 1 when spent `+0x38c = 25 * mass` |
| 137 | `0x1400355c5` | set by `FireShell` on the firing part for the harpoon (ammo 90); not read |
| 140 | `0x14003447b` | **laser-guided shell** (`_LG`): steers to owner's aim line, 0.4 rad/tick cap; weapons-index.md s5.4 |
| 150 | `0x140033e0b` | not read |
| 160 | `0x14003409f` | **proximity shell** (`_PROXY`): 150 range, 36 deg cone, 5..15 fragments; weapons-index.md s5.5 |
| 190 | `0x1400342a1` | **rocket-burst bomblet** (made by `FUN_14001c890`); weapons-index.md s5.6 |
| 200 | `0x140035652` | **all engine parts: hull stabiliser** (user-confirmed 2026-11-25). Uses `Stats.m_mdl_at` (`+0x100`, getter `GetMdlAt 0x140048720`); one `Body_AddTorque` per engine part per tick on the root Frame, clamped to +-`m_at`. The further the hull is from level, the stronger the restoring term. Formula: hull-stabiliser-engine-logic.md, hull-stabiliser-coupling.md |
| 210 | `0x1400357d6` | **escape pod** (`MDL_EVAC`) (user, 2026-11-25). While the pod is inside the level bounds (`Body_IsInsideLevelBounds 0x14021ccb0`) it flies its attitude/velocity controller; once outside it calls `Creature_OnDestroyed 0x140210620` (removal) |
| 400 | `0x140038767` | **landing legs, not a rotor** (user + code, 2026-11-25). Only runs when the landing/arcade flags `0x147fc6fd4`, `0x147fc6fb7` or `0x147fc6f82` are set; finds the leg bodies in the `creature+0x230` list and drives their joint motors (`Joint_SetMotor 0x1401949d0`), i.e. the landing-gear controller. Inactive in an ordinary battle |
| all other ids | `0x14004501f` | nothing |
| 550 | `0x140038d8d` (via `0x140038d63` table) | **debris fragment** from `Body_DieExplode`; weapons-index.md s5.7 |

## Update 2026-11-25 (user, checked against the 1.163 code)

* **200 is every engine part, not a separate "hull stabiliser part".** The user confirmed it in play; the case itself is one call per engine part. `m_mdl_at` (`OL.seria` -> `Stats+0x100`, `GetMdlAt 0x140048720`) is the per-part torque authority: the case applies `-w*I*kd*m_at/gate` plus an angle term `-a*I*kp*m_at/gate` (clamped to +-`m_at`) through `Body_AddTorque` **once per engine part per tick/frame**; the further the hull tilts from level, the larger the restoring term. Full formula and constants: `../physics/hull-stabiliser-engine-logic.md`.
* **210 is the escape pod** (`MDL_EVAC`). The block (`0x1400357d6`) checks `Body_IsInsideLevelBounds` and then runs an attitude/velocity controller; when the pod leaves the level bounds it calls `Creature_OnDestroyed 0x140210620` (the pod is removed).
* **400 is the landing-leg controller**, not a rotor. The block (`0x140038767`) is gated on the arcade/landing flags `0x147fc6fd4` / `0x147fc6fb7` / `0x147fc6f82`, walks the `creature+0x230` list for the leg bodies and drives their joints via `Joint_SetMotor 0x1401949d0` with a contact-angle target. It does nothing in a normal battle. The old "rotor / helicopter-style motor" label was wrong.
* 1.151 block addresses for the same cases: 200 -> `0x1400342D9`, 210 -> `0x14003447A`, 400 -> `0x1400372A6` (from the 1.151 dispatch tables `0x140043060` / `0x14004302C`).
