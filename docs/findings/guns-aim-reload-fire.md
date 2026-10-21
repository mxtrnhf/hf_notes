# Guns: aim servo, reload, fire gates, spread, recoil (1.163)

Status: read in Ghidra 2026-10-21 [code] unless marked. Program `Highfleet.exe.unpacked.exe` 1.163. Companion: [blast-and-penetration.md](blast-and-penetration.md), [firing-and-shells.md](firing-and-shells.md). Ammo index to gun: [ammo-1151-vs-1163.md](ammo-1151-vs-1163.md).

Program `Highfleet.exe.unpacked.exe` (1.163). Tags: **[code]** read by me today in decompile; **[agent]** from the DeepSeek report `hf_ml/out/ds-gunaim/REPORT.md`, not re-read; **[guess]**.

## 1. How a gun turns (NOT instant)  [code]
* The gun barrel is a part on a **revolute joint with a motor**; it is steered by the same servo as the engine swivel: message id 200 `{200, angle}` -> dispatcher `0x1400533f0` -> handler `0x140053870` (not renamed yet; it is a servo update, not an "atan2f").
* Handler: error = wrap(commanded angle - part angle `+0x138`), deadband 0.01 rad (error set to 0 below that), then **sqrt easing**: `e = sign(err) * sqrt(|err|)`. Motor speed = `P * P * Stats+0x108 * e` with `P` = part power fraction `+0x818`; motor max torque = `mass(+0x1d8) / 100`. Applied through `Joint_SetMotor` on every joint in the part's joint list (`+0x230`). Needs power `+0x818` != 0 (it returns at once otherwise) and, when Stats `+0xec` != 0, also `+0x820` != 0.
* **Parallax correction** (if the owner has a target link in `+0xb00`, or `+0xb18` when part `+0x84c` (weapon type) == 1): the commanded direction is taken as a ray from the ship CENTRE (`+0x1840/+0x1844`); the point on that ray at the same distance as the target from the centre is computed, and the gun turns to point from ITS OWN position at that point. So off-centre guns converge on the aim ray at target range. Without a target the commanded angle is used as is.
* The AI commands ONE angle per ship for all guns (`-atan2(dir)`), computed in `AiWeaponController 0x14007a8d0` at `0x14007b600..0x14007b92f` [agent], direction stored at creature `+0xbf8/+0xbfc`, lead vector `+0xbc8/+0xbcc`. Lead uses the solver `FUN_140233490` [code, below]. AI fires only when `|gun angle +0x138 - aim| <= 0.025 rad` (float at `0x140354678`) [agent].
* `FUN_140233490(out, targetPos, targetVel, v0, accel, accelTime, shooterPos, shooterVel)`: bisection (100 iterations, stop at 0.5 range) for the flight time t of a projectile that accelerates at `accel` for `accelTime` seconds from base speed `v0` and then coasts; the aim point is shooter + t * (relative velocity) + target... i.e. a standard intercept with an acceleration phase. Whether the plain-shell AI call passes accel = 0 was not read.

## 2. Firing arcs  [code]
* **No arc check exists in FireGuns / FireGun / FireShell.** The Body list `m_sectors` (`+0x508/+0x510`) is only read by serializer / copy / constructor code (no game-logic reader found in a program-wide search for `+0x508`/`+0x510`). Stats `+0x12c/+0x130` (sectors shift/threshold) were not found in the turn or fire code either [agent, my search found no reader].
* So the only real limit on where a gun can point is the **revolute joint's angle limits** (`m_angle_enable/min/max`, Joint `+0xf4/+0xfc/+0x100`, DATA in the seria) plus physical blocking by its own hull (shells collide with the shooter's parts? see gun part 2). The QoL mod's arc blocking (`0x140032f22`) is the mod's own addition, not vanilla.

## 3. Fire gates, FireGuns -> FireGun  [code]
`FireGuns(gun)` (0x1400559e0, takes ONE gun; callers loop the groups): requires gun `+0x2f4 == 0`, `+0x818 != 0` (powered) and (Stats `+0xec == 0` or `+0x820 != 0`); then `FireGun(gun, side)` with side = -1 when owner `+0xad4 <= 0` and nonzero (enemy), else +1.
`FireGun` (0x140032e60): needs loaded `+0x860 >= 1.0`; sets latch `+0x874 = 1`; refuses if block timer `+0x870 > 0`, or rate timer `+0x86c != 0`. Fires: `+0x860 -= 1` (clears `+0x875` at <= 0), `+0x86c = 1 / (rpm/60)` with rpm = Stats `+0x150` (0 -> 0), then `FireShell`. (In the `DAT_147fc6fd4` mode a gun with the rate timer running returns "fired" without firing.)

## 4. Reload model (per-frame, `Part_Tick` 0x140054fb0, code at `0x1400553b5..0x140055516`)  [code]
Fields (gun part): `+0x860` loaded rounds (float), `+0x858` reserve rounds (int), `+0x864` reload timer, `+0x868` rounds-in-flight-of-reload (0/1), `+0x86c` rate timer, `+0x870` AI block float, `+0x874` latch, `+0x85c` second ammo reserve. Stats: `+0x148` magazine (int), `+0x14c` reload time (s), `+0x150` rpm.
* Reload runs only if Stats `+0x14c != 0`, part enabled `+0x80c != 0` and powered `+0x818 != 0`, and the part has an owner (or is a GUI body).
* **Rounds are loaded ONE AT A TIME.** When `timer == 0` and `loaded < magazine`: `timer = reload_time / magazine` (x0.8 with perk id 1 in creature `+0x1a30` list). If reserve `+0x858 >= 1`: reserve -= 1 and step = 1, else step = 0 (a round is only added if the reserve paid for it). While `timer > 0` it counts down by `dt * k` with **k = 1.75 for the player's ship, 1.0 for everyone else**; at <= 0: `loaded += step` (skipped for parts named `MDL_FIGHTER01`), `timer = 0`, and the next round starts on the next tick.
* One exception to the countdown: when `DAT_147fc6fe0 != 0`, for a non-player part the timer only runs if `FUN_1402213e0()` is true or `FUN_14021ccb0(owner,0,1)` is true (a campaign-mode condition I did not decode) [V code, meaning open].
* The rate timer `+0x86c` counts down by dt (the global `time_related_global_`); at <= 0 it is set to 0.
* **AI burst/pause cycle** (non-player only): a fire attempt sets latch `+0x874`; while the latch is set `+0x870 -= dt`; when it falls below -3.0 it is reset to **+1.5** and the latch is cleared. FireGun refuses while `+0x870 > 0`. Net: roughly 3 s of allowed fire then a 1.5 s pause, repeating while the AI keeps trying (the first cycle starts at 0, so the first pause comes after ~3 s of attempts). The player's `+0x870` is forced to 0 every tick.
* Player-only: if reserve, loaded and step are all 0 and the extra reserve `+0x85c > 0`, `FUN_1401b6e00(owner)` runs (swap to the second ammo type) [guess on meaning].

## 5. Spawn, spread, speed, recoil (`FireShell 0x1400300d0`, `Body::BulletImpact__ 0x140052a80`)  [code]
* FireShell dispatches on the **ammo index** (not calibre): 5, 10, 15, 20, 25, 30, 40, 90 are ordinary shells through `BulletImpact__`; 51/52/54/55 (0x33 0x34 0x36 0x37) are missiles (their own setup); 60 and 70 are multi-pellet flak (3 and 6 pellets, fixed fan 0.3 / 0.1 rad steps, speed rand * 300 / 250 * mass); 80 is the EMP pulse; the rest of FireShell is muzzle flash and sound.
* **Spread** = uniform random angle in `[-s, +s]` rad around the aim: `s = 0.05` for ammo 5, 10, 15; `s = 0.02` for ammo 20, 25, 30, 40, 90. [V: the `param_13` argument of each call: `0x3d4ccccd` = 0.05, `0x3ca3d70a` = 0.02]
* **Muzzle speed** = `rand(0.98, 1.20) * ammo.speed` (HGE uniform), direction = gun's local forward (0,1) rotated to world by the gun angle, then rotated by the spread. It is applied as an **impulse = speed * mass** on the shell body (vtable `+0x190`; so v = speed * rand). The shooter's velocity IS added: see section 7 (the shell's velocity is first set to the root body's velocity, then the muzzle impulse is added).
* **Recoil**: see section 7 (corrected 2026-10-21: only the PLAYER's ship gets recoil; the earlier "real momentum conservation for everyone" was wrong).
* Shell body setup (BulletImpact__): ttl = `ammo.ttl` (1.0 for armour-piercing), explosive `+0x2dc = ammo.explosive_power`, penetration `+0x2e0 = ammo.penetrative_power`, incendiary `+0x2e8 = ammo.incendiary_power`, calibre `+0x3c4`, `ap_drag` -> `+0x1dc`, health 1.0 (`+0x2c8/+0x2cc`), bullet flag `+0x1fc = 1` (continuous collision); owner links set by `SetLink` (shooter creature and gun). Exact link offsets not decoded here.

## 6. Not done / open
* Ammo index <-> item table: `AMMO_LIST_BEGIN 0x143a13be0`, stride 0x188, fields (`ttl`, `speed`, `explosive_power`, `penetrative_power`, `incendiary_power`, `ap_drag`, `caliber`); whether FireShell index == calibre key for the shells (5 = 37 mm, 10, 15, 20, 25 = 180 mm?, 30, 40, 90 ...) should be read from the Ammo table, not guessed.
* `DAT_147fc6fe0` reload-pause conditions (`FUN_1402213e0`, `FUN_14021ccb0`).
* Player-side aim sender (who pushes the player's `+0xbb4` into `{200, angle}`): not found; likely through a vtable.
* (Answered, section 7: yes.)
* Gun part 2: section 7 (done 2026-10-21); still open there: the per-ammo shell size/density constants in `FireShell`, the AI trigger decision.

## 7. Part 2 (2026-10-21): shell velocity, recoil, flight, how a shell hit becomes damage [code]
**Initial velocity and recoil** (`Body::BulletImpact__` `0x140052a80`, helper `0x140051e20` = `Body_SetLinearVelocity(body, vx, vy)`, which writes `+0x130/+0x134` and `b2 v = 0.05 * v`):
* If the root body (the ship Frame) exists, the shell is first given **the root body's velocity** (`root +0x130/+0x134`), then the muzzle impulse `dir * rand(0.98, 1.2) * ammo.speed * param_8 * shell mass` is added (spread rotation applied to `dir`). So **world-frame shell velocity = ship velocity + muzzle velocity** (muzzle velocity independent of the shell's mass).
* **Recoil only for the player's ship**: the impulse `-(muzzle velocity * shell mass)` on the root body is applied only when `param_9 != 0`; `FireShell` passes `param_9 = Profile_IsPlayerShip(profile, shooter creature)` (`R12B` at `0x140030405`). AI ships (and allies that are not the profile's flagship) get no recoil.
* Spawn point: gun position plus **10 x** the world-rotated muzzle offset vector (`FireShell` `0x1400301b0..0x14003023e`, factor `[0x140352818]` = 10.0) [read, role of the offset vector inferred as the unit barrel direction].
* Other `BulletImpact__` facts: owner link (`+0xb0`), firing-gun link (`+0x490`), root-body link (`+0x4a8`); `+0x1c0 = 0xd` (projectile flag bits), **collision layer `+0x1f0 = 0xf`**, stage `+0x8d8 = max(0x29, param)`, hit points `+0x2c8 = +0x2cc = param_11 = 1.0` for every cannon shell, `+0x3c4` = ammo `caliber` (logic id), `+0x1dc` = `ap_drag`, `+0x2dc/+0x2e0/+0x2e8` = explosive / penetration / incendiary power, ttl `+0x2c0`/`+0xf4`-fields = `ammo.ttl` (1.0 s if the ammo has penetration).
* The shell body itself is made by `CreateShell?` `0x14004edd0`: a regular polygon (n sides, half-extent factor 0.5, n = -1 means a 4-vertex diamond), density given by the caller; mass follows the usual rule (`min(w,h) * density * area`, from Box2D). Per-ammo size/density/n are literals inside `FireShell` and were not tabulated.

**Flight**:
* Gravity: stock Box2D gravity 9.82 game units/s^2 (down, +y), plus Box2D linear damping 0.05/s, as for every body (`box2d-physics-setup.md`).
* Extra forces from `Body_PreStepUpdate` (non-Frame branch): drag `-v_hat * 0.5 * 1.29 * c * |v|^2` with `c = +0x1dc = ammo.ap_drag` (0 for plain shells; 0.0007 for AP rounds), gravity-like `(0, -9.82 * mass * +0x1e4)` and a wind term `+0x1e8`. A cannon shell never gets `+0x1e4` / `+0x1e8` written (those stores in `FireShell` belong to the rocket / effect cases, values 0.326 / 0.463 and 1.0 / 0.6), so they keep the body default 0 [inferred from the absence of stores]: **no extra lift or wind on cannon shells**.
* Lifetime `ammo.ttl` s (AP: 1.0 s); the shell is a Box2D "bullet" (`+0x1fc` set where the body is built, continuous collision).

**Collision filtering for shells**: `ShouldCollide` (box2d-physics-setup.md section 5): the layer rule `(A+0x1f0 & B+0x1f0) != 0` with the shell's `0xf`; ground bricks carry `0x1f` (see battle-terrain.md), so shells hit terrain. The ship-part masks were not read.

**How a hit becomes damage** (corrects the PreSolve claim in section 5 of box2d-physics-setup.md and in blast-and-penetration.md):
* `b2CListener_PreSolve` `0x140284730` implements **only** the flare/decoy rule (explosive projectile touching a Stats-category-0x80 body: 90 % chance of a small blast, contact disabled once per pair). It does **not** detonate shells.
* A shell contact reaches `Physics_ProcessContactRecord` `0x1402849a0`, which calls `vtable+0x210 = Body_ApplyDamage(d = 0.8 * rec[+0x40])` on both bodies (subject to its skip rules), where `rec[+0x40]` is the Box2D impulse (b2 units; momentum in game units x 0.05^4 / 0.05^... i.e. `d = I * 5e-6` with `I` the game-unit impulse). **Correction 2026-10-21 (later): this cannot be what kills a shell.** With the real shell masses (table below) the momentum of a heavy shell is `m * v` of about 86 * 700 = 6e4, so `d` is about 0.3, and a 37 mm shell (m about 0.95) gives about 0.003, against the shell's 1 hp. The set-health slot (`vtable+0x208` at `0x140051de0`: if not invulnerable, `hp = min(max hp, new hp)`, and when it reaches 0 it tail-jumps to `vtable+0x200`) is the generic death path, but a normal impact does not reach it.
* **What detonates a plain shell is therefore NOT established.** Candidates: the per-frame projectile logic in `creatureLogic` (logic id = ammo `caliber`, 100 for plain shells), reading the last-contact record that the contact handler stores for every logic-active body (`+0x390` point, `+0x398` normal, `+0x3a0` impulse, `+0x3a8` link to the other body); or ttl expiry. Not read: `creatureLogic` is too large for the decompiler. Do not model "d >= 1 kills the shell".
* The second path, `Projectile_DetonateOnImpulse` `0x14001d1e0` (called at the end of the contact handler when `0 <= body +0x38c < impulse`), is for projectiles whose `+0x38c` has been set: the default is -1 (never) and cannon shells do not set it; the per-frame projectile logic sets it for some missile logics (`0x140035597`: `+0x38c = mass * [0x140354828]` once armed in state 1 of `+0x3cc`).
* So the damage of a plain explosive shell on a ship = contact damage `0.8 * impulse` to the part touched (armour threshold Stats `+0xc4` for direct hits) **plus** the area blast from the shell's death (shadow-cast model in blast-and-penetration.md); AP shells (explosive 1.0, radius 1) do their damage through the contact plus the penetration chain.

**Still open here**: what actually triggers a plain shell's detonation (above), the armour-threshold gate for shell-vs-armour direct hits in `Body_ApplyDamage` (`param_3` and Stats `+0xc4` per part), the AI trigger decision in `AiWeaponController` (range / lead gates beyond the 0.025 rad aim error), the ship parts' `+0x1f0`.

### Shell body constants per ammo index (`FireShell` 1.163, read in full 2026-10-21) [code]
`CreateShell?(body, ..., size A, density rho, n)`: a regular `n`-gon inscribed in an ellipse with half-extents `0.5 * A` x `0.5 * A` (xDir and param_5 are the same number A for the cannon shells), `n = 3` (a **triangle**) for all cannon shells; mass (Box2D, then `/0.05^3`) is `min(w,h) * rho * area`; for a triangle `min(w,h) = 1.5 r`, `area = 1.299 r^2`, `r = A/2`, so `m = 1.949 * rho * r^3`. `BulletImpact__` arguments in the same call: speed factor 1.0, hp 1.0, spread 0.05 (ammo 5, 10, 15) or 0.02 (others).
| ammo index | calibre | A (size) | rho | n | mass (game units, computed) | shake | notes |
|---|---|---|---|---|---|---|---|
| 5 | 37 mm | 1.25 | 2.0 | 3 | 0.95 | 5.0 | `+0x3c0` = FUN_1401af7b0(5 or 4) timer |
| 10 | 57 mm | 1.25 | 7.5 | 3 | 3.6 | 7.0 | |
| 15 | 100 mm | 0.25 | 4185.0 | 3 | 15.9 | 7.0 | |
| 20 | 130 mm | 0.25 | 8317.5 | 3 | 31.7 | 8.0 | |
| 25 and 40 | 180 mm and 305 mm (shared code) | 0.375 | 6666.7 | 3 | 85.6 | 10.0 | both indices use the same shape |
| 30 | 203 mm | 0.625 | 1920.0 | 3 | 114 | 15.0 | |
| 90 | harpoon | 0.625 | 3200.0 | 3 | 190 | 20.0 | also sets flags `0x10015`, changes the shooter's logic to `0x89` |
Rockets (51, 52, 54, 55) use A = 2.87 / 7.5 style sizes with density 507.0 and n = 4, hp 10, ttl 10 (51, 55) or 30 (52, 54), collision mask 7; canister (60: 3 pellets, 70: 6 pellets) A = 1.0 / 2.0 with density 1000, n = 3, pellet speed `rand * 300 * mass` / `rand * 250 * mass`. Muzzle flash: a separate short-lived 4-vertex body (A = 20, density 1.0) with sprites `flash` / `flash_fire`.
Mass check: muzzle momentum `m * v` for the 180 mm shell is about 85.6 * 700 = 6.0e4 (game units); that is also the recoil impulse the player's ship receives.
