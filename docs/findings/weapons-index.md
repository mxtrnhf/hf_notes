# Weapons index: firing, guns, shells, blast, missiles (1.163)

Index note for the simulator session (request 2026-10-23). It links the per-topic notes, lists the routines with addresses, and marks what is open or superseded. Program `Highfleet.exe.unpacked.exe` 1.163, image base `0x140000000`.
Tags: **[code]** read in decompile/disassembly by a Ghidra session; **[V]** same, with constants read from the image; **[agent]** from an external-AI report, not re-read; **[log]** measured on probe logs; **open** = not read.
This note does not repeat formulas; the linked section has the pseudocode and constants. "Section" below means the section of the linked note.

## 1. Topic map

| Topic | Routine (address, name) | Note and section | Status |
|---|---|---|---|
| Gun fire gate | `FireGuns 0x1400559e0` (one gun; needs `+0x2f4 == 0`, `+0x818 != 0`) -> `FireGun 0x140032e60` (loaded `+0x860 >= 1`, block `+0x870 <= 0`, rate `+0x86c == 0`) | [guns-aim-reload-fire.md](guns-aim-reload-fire.md) s3 | [code] |
| Reload, rate timer, magazine, reserve | `Part_Tick 0x140054fb0`, code `0x1400553b5..0x140055516`; one round per `reload_time / magazine` s; player ship counts down 1.75x | guns s4 | [code]; one condition open (`DAT_147fc6fe0`) |
| AI burst / pause cycle | same Part_Tick block: latch `+0x874`, `+0x870 -= dt`, reset to +1.5 below -3.0 | guns s4 | [code], constants re-read in section 3 below |
| FireShell dispatch | `FireShell 0x1400300d0`: ammo index 5/10/15/20/25/30/40/90 shells, 51/52/54/55 rockets, 60/70 canister, 80 EMP | [firing-and-shells.md](firing-and-shells.md), guns s5 and s7 table | shells [code]; rockets, canister, EMP only partly tabulated |
| Shell body, spawn, spread, muzzle speed, recoil | `Body::BulletImpact__ 0x140052a80`, `CreateShell? 0x14004edd0`, `Body_SetLinearVelocity 0x140051e20` | guns s5 and s7 | [code]; ship velocity IS inherited, recoil is player-only |
| Ammo table | `DefineAmmos 0x140256f10..0x14025afc4`, `AMMO_LIST_BEGIN 0x143a13be0`, stride `0x188` | [ammo-1151-vs-1163.md](ammo-1151-vs-1163.md) | [code], live dump on 1.163 |
| Gun servo and motor | message id 200 -> `0x1400533f0` -> handler `0x140053870` (deadband 0.01, sqrt easing, `P^2 * Stats+0x108`, torque `mass/100`) | guns s1; [ref/engine-servo-error.md](../../ref/engine-servo-error.md) (untracked, not mine) | [code] |
| Parallax and lead | parallax in the handler; plain solver `0x1402333c0` / `0x1401a8780` (quadratic); accelerating solver `FUN_140233490` (ammo 52 only) | guns s1, s8, s9 | [code] |
| AI aim angle | `AiWeaponController 0x14007a8d0` (aim stored `+0xbf8/+0xbfc`, lead `+0xbc8/+0xbcc`, one angle for all guns); tolerance 0.025 rad at `0x140354678` | guns s8; [ai/ai-intercept-targets.md](ai/ai-intercept-targets.md) (gate order, line 69) | [code]; tolerance re-read in section 3 below |
| AI fire decision | same function: latch skip, `+0x860 <= 0` skip, range gates `+0x1838/+0x183c`, zoom, friendly-fire segment test `FUN_14021c790`; ammo re-roll `AiRerollAmmoFlags 0x140079810` | guns s8; [ai/ai-tick-patch-sites.md](ai/ai-tick-patch-sites.md); [ai/ai-intercept-targets.md](ai/ai-intercept-targets.md) | [code] |
| Player fire path and input | player input `0x14018dbf0`; caller of `FireGuns` other than the AI | not documented | **open** (section 3 below) |
| Shell flight, drag, TTL | `Body_PreStepUpdate 0x14001d440` (non-Frame branch: `-v_hat * 0.5 * 1.29 * c * v^2`, `c = ap_drag +0x1dc`); ttl `ammo.ttl` | guns s7; [box2d-physics-setup.md](box2d-physics-setup.md); [cluster-bomblet-ttl.md](cluster-bomblet-ttl.md) | [code] |
| Shell detonation | arming `creatureLogic 0x140033b90` block `0x140033d47` (logic 100: `+0x3d0 = 20/|v|`, then `+0x38c = 25 * mass`); `Physics_ProcessContactRecord 0x1402849a0` -> `Projectile_DetonateOnImpulse 0x14001d1e0` -> `Body_DieExplode 0x140023ac0` | [shell-detonation-paths.md](shell-detonation-paths.md) | [V] + [log] 64/64 chains |
| Contact damage, armour threshold | `Body_ApplyDamage 0x1400519d0` (threshold Stats `+0xc4`, direct-hit flag only), `0x1402849a0` | guns s9; [contact-damage-and-fire.md](contact-damage-and-fire.md) | [code]; the gate per part is open |
| Blast, area damage, occlusion | `FUN_140029b60` (S = 2 sqrt E, R = sqrt E, x0.66 unless player), `Body_AreaDamageFromBlast 0x14002cdc0`, `FUN_14002d610`, `FUN_140045800` | [blast-and-penetration.md](blast-and-penetration.md); [explosion-damage-1151-vs-1163.md](explosion-damage-1151-vs-1163.md) | [code] |
| Penetration chain | inside `FUN_140029b60`: direct `strength * 4`, `strength -= hp/20`, `-10` per part | blast-and-penetration | [code], roles approximate |
| Truss / hardpoint rule | `b2CListener_PreSolve 0x140284730` | [flares-and-missiles.md](flares-and-missiles.md) s1 | [V] |
| Missile guidance (Zenith and rockets) | `creatureLogic` logic 1/3/4 block `0x140036024`; steering law, intercept `0x14022c250`, PD torque Kp 20 Kd 1 | [zenith-steering.md](zenith-steering.md) | [V]; s4 leftovers open |
| Seeker, flare lure, proximity fuze | seeker block `0x1400361c5..0x1400372ac`; flares logic 1100 within 400 units | flares-and-missiles ("Seeker and flare lure") | [V] |
| Flares | `FireFlareLauncher 0x14002eed0` (triangle, ttl 5.0, mask 0, drag 0.0007, speed `rand(0.9,1.5) * 400`) | flares-and-missiles s2; [ai/ai-flares.md](ai/ai-flares.md); [flare-crash-hunt.md](flare-crash-hunt.md) | [V] |
| Anti-air / flak gun (KAZ) | `Weapon_FlakInterceptScan = FUN_14002f480` (cone 45 deg, 60/120 units) | shell-detonation-paths s2; firing-and-shells (KAZ) | [V] + [log] |
| Launches (Zenith) | AI `FUN_140062f90` -> `LaunchZenithAtOwnerTarget FUN_14002ff60` (call `0x140065edb`, cooldown `+0xd60 = 2.0`) | [combat-missile-launch.md](combat-missile-launch.md); [ai/ai-aircraft-launch.md](ai/ai-aircraft-launch.md) | [code] + probe |
| Strategic missiles | `FUN_1400eced0` (map level) | [strategic-missile-target-assignment.md](strategic-missile-target-assignment.md) | separate from combat |
| Logic id table | `creatureLogic` dispatch, ids 100/110/120/135/200/400 read | [creature-logic-id-map.md](creature-logic-id-map.md) | ids 130/132/137/140/150/160/190/210 not read |
| Cluster bomblets | `FUN_140032fb0`, `Projectile_ExplodeAndCluster` | [cluster-bomblet-ttl.md](cluster-bomblet-ttl.md) | partial |
| Randomness of the above | FireShell spread/speed, AI ammo and launch rolls | [determinism-randomness-audit.md](determinism-randomness-audit.md) (untracked, not mine) | [code] |

## 2. Superseded or wrong statements (read before using the old notes)

1. **guns-aim-reload-fire.md s7 and s9: "what detonates a plain shell is NOT established".** Superseded by [shell-detonation-paths.md](shell-detonation-paths.md): arming after `20/|v|` s, then detonation at the first contact with `160000 * raw impulse > 25 * mass`. The probe confirmed 59 of 59 chains. The "do not model d >= 1 kills the shell" advice in s7 still stands.
2. **blast-and-penetration.md, bullet 1: "a plain shell has 1 hp and dies from contact damage".** Wrong: contact damage is 0.003 to 0.3 against 1 hp. The detonation is `Projectile_DetonateOnImpulse`, see 1.
3. **blast-and-penetration.md, last bullet "NOT decoded: ... whether the ship velocity is inherited".** Answered: inherited (guns s7, slope ~1 in the telemetry).
4. **guns s1: "lead uses `FUN_140233490`".** Only for ammo 52 and targets beyond 300. The plain-shell solver is `0x1402333c0` / `0x1401a8780` (guns s9).
5. **`hf_ml/DESIGN_NOTES.md`, section "ghidra-miner gun part 1"** (simulator's file, not edited here): "the shooter's Frame body gets the equal and opposite impulse (true recoil)" is wrong, recoil is applied only to the player's ship (guns s7). "Ship velocity added to the shell: not seen in the code" is answered, it is added.
6. **guns s8: the target-speed clamp "for |v| > 200"** is flagged as non-monotonic; see section 3 below for the disassembly check.
7. Shell mass table in guns s7 is computed from the `CreateShell?` literals, not read from a running game.

## 3. Gap checks done for this index (2026-10-23)

Method: Ghidra 1.163 (`Highfleet.exe.unpacked.exe v1.163`), decompile of `AiWeaponController` plus disassembly and `read_memory` of each constant. Tag per value: **[mem]** = value read from the image, **[imm]** = immediate in the instruction, **[dec]** = decompile literal only.

### 3.1 Constants confirmed
| Value | Address | Read | Meaning |
|---|---|---|---|
| 0.025 | `0x140354678` (bytes `cdcccc3c`) [mem] | loaded into XMM12 at `0x14007b959`, used in the angle gate | AI aim tolerance, radians |
| -3.0 | `0x140354930` (bytes `000040c0`) [mem] | `COMISS` at `0x14005558f` in `Part_Tick` | burst-cycle lower limit |
| +1.5 | immediate `0x3fc00000` at `0x14005559b` [imm] (also the ctor default at `0x140049a11`) | | block timer reset value |
| 0.02 s | `0x1403c126c` (bytes `0ad7a33c`) [mem] | `SUBSS` at `0x140055577` | frame dt |
| 200.0 / -200.0 / 1.0 | `0x14035282c`, `0x140352868`, `0x1403524d8` [mem] | clamp at `0x14007b251..0x14007b2ce` | target-speed clamp, below |
| +-0.3 | `0x1403546b0` / `0x140354920` (bytes `9a99993e` / `9a9999be`) [mem] | `Random_Float(min=XMM15, max=XMM14)` at `0x14007abc1` | aim jitter in the aircraft branch, below |
| 2000 / 10000, radius 2.0 or 3.0 | [dec] | friendly-fire segment | below |

Burst cycle re-read in the disassembly (`0x140055561..0x1400555a7`), for a non-player part with a fire attempt latched (`+0x874 != 0`): `+0x870 -= dt`; `if +0x870 < -3.0 { +0x874 = 0; +0x870 = 1.5 }`. For a player part (`R14B == 0`) `+0x870` is forced to `R15D` = 0 every tick. `FireGun` refuses while `+0x870 > 0` (`0x140032ec1`). Consequence: after a latch the AI may fire while `+0x870` goes 0 -> -3.0 (3.0 s = 150 ticks at dt 0.02), then `+0x870 = +1.5` blocks fire until it decays back to 0 (1.5 s), then the cycle can start again. So **3.0 s fire, 1.5 s pause**, period 4.5 s while the AI keeps trying. [mem]

### 3.2 AI fire decision, corrected (`AiWeaponController 0x14007a8d0`, decompile read in full 2026-10-23)
The function has THREE shapes. The old header comment and guns s8 describe only the third.
* **A. Aircraft or missile target and no ship target** (`creature +0xb18 != 0` and `+0xb00 == 0`; code `0x14007aa2d..0x14007af56`, loops at `0x14007abaf` group 0 and `0x14007ad74` group 1). The lead solver is the plain one `0x1402333c0` with the target velocity times `creature +0xc08` (0.5). **Every tick every gun gets angle `-aim + Random_Float(-0.3, +0.3)` (a fresh +-17 degree jitter, spray)**. **Group 0 guns are only tested and fired in this shape when group 1 is empty** (`if +0x13c0 == +0x13c8`, decompile); with two gun groups only group 1 shoots at aircraft/missiles. Fire gate per gun: NO latch, NO magazine test, NO aim-tolerance test. Distance root-to-target `< R` where `R = creature +0x1838` (group 0) or `+0x183c` (group 1), replaced by `3500` if the target part has flag `0x8000000`, `0.75 * R` if flag `0x4000`, `max(2R, 3000)` if flag `0x400`, and `700` if creature byte `+0x228` is set (checked in that order, the last one overrides). Then the friendly-fire segment test `FUN_14021c790(start, start + 2000 * muzzle_dir, side, radius factor, creature)`: factor 2.0 for group 0, 3.0 for group 1 here; hit -> hold fire, else `FireGuns(gun)`. [dec + mem for the 0.3]
* **B. No target at all** (`+0xb00 == 0`, `+0xb18 == 0`): return, nothing fires.
* **C. Ship target** (`+0xb00`): returns at once if `dist(centres) < radius(target) + radius(self) + 30.0` (30.0 at `0x1403524dc` is pooled). Aim = lead of section 8 of the guns note (with the clamp below); ONE angle `-atan2` sent to all guns (command 200, no jitter). Per gun, in order:
  1. latch `+0x875 != 0` -> `FireGuns` directly (skips 2 to 7);
  2. `loaded +0x860 > 0`, else skip;
  3. creature byte `+0x228` set and `dist > 700` -> skip;
  4. `FUN_1402213e0()` true (a zoom/scene predicate) and calibre key `Stats+0x144 <= 10` and `dist > 1500` -> skip;
  5. range: `dist(root, aim point) <= R` with `R = +0x1838` (group 0) / `+0x183c` (group 1), **doubled unless** `(FUN_1402213e0() == 0 and ZOOM_LEVEL < 4 and FUN_14021ccb0(creature,0,1) != 0)` (byte `local_res8`); the doubling is therefore the usual case;
  6. angle: `|wrap(gun +0x138 - aim)| <= 0.025`, wrap = subtract `2 pi * round(x / 2 pi)`;
  7. friendly fire, only if the list at `DAT_147fc73d8` has more than one entry (24 bytes per entry) or `DAT_147fc75b0 != 0` or creature `+0xbd8 == 3`: segment 2000 long (10000 when `DAT_147fc6fe0`), radius factor 3.0; hit -> hold fire;
  8. start: normally require `loaded >= magazine (Stats+0x148)`, set latch `+0x875 = 1`, `FireGuns`. **Exception**: if the target is an aircraft/missile link (`+0xb18`), group 1 is empty and the gun's calibre key `<= 10` and `Profile +0x165 != 0`, it sets `+0x870 = 0` (no pause) and fires without needing a full magazine and without the latch.
  Because the latch is only cleared by Part_Tick when the burst timer runs out, a latched gun keeps firing past gates 2 to 7 until `+0x870 < -3.0` (see 3.1) or the magazine is empty; this is what makes the AI "burst".
* **Ammo choice** (same function, ship-target shape only): for calibre key 15/20/25/30 pick `ITEM_AMMO_{100,130,180,230}MM` with `_AP` if (`+0xc7c` and `+0xc74` set and `dist < 1000`), else `_PROXY` if (`+0xc7d` and (`+0xc75` or `+0xc76`)), else plain. `FindAmmoIndex` result goes into gun `+0x850`. [dec]
* Missile special case unchanged: any loaded gun with calibre key 52 (`0x34`) and target `> 300` away uses `FUN_140233490(.., v0 = 0, accel = 500.0 (0x43fa0000), accel_time = 1.5 (0x3fc00000) ..)`. [dec immediates]

### 3.3 Target-speed clamp (guns s8), verified in the disassembly
`0x14007b251..0x14007b2ce`: with `x = |v| - 200`, if `|v| > 200` then `|v'| = (1 - sqrt(x)) * x + 200`, direction unchanged. The decompile is right and the code is as odd as it looks: `|v'| = 200 + x - x^1.5` peaks at 200.15 (x = 4/9), equals 200 at x = 1, 196 at x = 4, **crosses zero near |v| = 240 and is negative above that (about -700 at |v| = 300)**, so for a fast ship target the lead points the other way. (The old note said "about 205"; the zero crossing is at about 240.) [mem + disassembly]

### 3.4 Player fire path
* Keys: `Input_KeyDown` sets, `Input_KeyUp` clears, creature bytes **`+0xbbc` (button 1, "LMB"), `+0xbbd` (button 2, "RMB")**, plus `+0xbbe` (one-shot, see below) and `+0xbc0` (flare key); also written by `FUN_14018af40` (`0x14018b2e2`, `0x14018b2eb`). The header comment of `AiWeaponController` says the same: the AI never touches them.
* Consumption in `CreatureUpdate 0x14007eb50` (call sites `0x14007f7be`, `0x14007f7fe`, only callers of `FireGuns` besides the AI):
  `if +0xbbc: for each gun in list +0x13a8..+0x13b0 (stride 0x18, part at +8): if FireGuns(gun) returned true and DAT_147fc6fd4 == 0: stop the loop` and the same for `+0xbbd` with list `+0x13c0..+0x13c8`. So **by default one gun per button per tick fires** (the first whose gates pass: rate timer 0, loaded, powered); the next tick the next gun that is ready, so guns fire in turn at the rate-timer pace. When `DAT_147fc6fd4 != 0` (the same flag that shrinks the muzzle flash) every ready gun fires in the same tick.
  `+0xbbe`: loop over list `+0x1438..+0x1440`, first entry with a part calls `FUN_14002e7d0(part)` once (it is the missile/launcher list; the one-shot byte is cleared at `0x14007f84e`). `+0xbc0`: over list `+0x1408..+0x1410` calls `FireFlareLauncher 0x14002eed0` for every launcher (`0x14007f899`), `DIL` records whether any fired. [dec + disassembly, role of list `+0x1438` inferred]
* The player does not run `AiWeaponController`; the gun angle command (message 200) for the player comes from another sender, still not found (open). `FireGun` is also called from `creatureLogic` at `0x14003ae82` (the weapon-fire logic with a re-rolled timer, auto-firing turrets), not read.
* Player part: `Part_Tick` forces `+0x870 = 0` each tick (no burst/pause) and the player's reload countdown runs at 1.75x.

## 4. Open items

1. **Player gun-angle sender**: who turns the player's mouse aim into command 200 for each gun (the `Player_SendThrustCommands 0x1402a9...` function calls the dispatcher `0x1400533f0` at `0x1402a9694..0x1402a984e` and `UpdateShipsAndMapFrame` at `0x1402aa351/0x1402aa380`; these look like the engine/swivel sender and were not read for guns).
2. `FUN_14002e7d0` (list `+0x1438`, the `+0xbbe` one-shot key): not read.
3. `creatureLogic` call to `FireGun` at `0x14003ae82` (logic id not identified).
4. `DAT_147fc6fe0` (set in campaign mode? doubles the fire-check segment and relaxes the reload pause) and `DAT_147fc6fd4`: writers not found.
5. FireShell cases 51/52/54/55 (rockets), 60/70 (canister), 80 (EMP): spawn, speed and effect values are only partly tabulated (rocket size/density/ttl/hp are; rocket thrust and guidance by logic ids 130/132/135/137/140/160 are in `creatureLogic` blocks marked "not read" in [creature-logic-id-map.md](creature-logic-id-map.md)); the EMP effect is undocumented.
6. Armour gate detail in `Body_ApplyDamage` per part (guns s9 gives the threshold rule; the per-part `param_3` meaning is open).
7. Intercept solver `0x1402333c0`: the formula is in guns s9 [code]; not re-verified against a log.
8. Random fire/launch rolls in `AiShipTick` (`0x140065c6c`, `0x140065dea`) and the wall-clock toggle (determinism audit): they gate Zenith launch, not gun fire.
9. Zenith steering leftovers: see [zenith-steering.md](zenith-steering.md) s4.
10. The `Random_Float()` call in shape A: argument registers read (`XMM1 = -0.3`, `XMM2 = +0.3`), but the vtable `+0x110` function itself was not re-read to confirm (min, max) order; the audit note lists it as `Random_Float(min, max)`.

## 5. Projectile logic ids: rockets, proximity/guided shells, bomblets, debris (added 2026-10-23, for the simulator)

Method: `creatureLogic 0x140033b90` blocks for ids 130/132/140/160/190/550 were in undefined code; I disassembled them in Ghidra (now code, with a comment on each entry) and read the constants from the image. Tags **[V]** = read in the 1.163 image; **[guess]** = my reading of what a value means. Tick `dt = 0.02` (`0x1403c126c`). Fields: state `+0x3cc`, timer `+0x3d0`, burn time `+0x3d4`, mass `+0x1d8`, explosive `+0x2dc`, arming threshold `+0x38c`, ttl `+0x2c0`, collision mask `+0x1f0`. The whole block is skipped while the byte at `0x143a11909` is non-zero (a global pause/freeze flag [guess]).

### 5.1 Ammo index -> logic id -> what runs
| Ammo (index) | Logic id | Spawned by | Body set-up in `FireShell` | Behaviour |
|---|---|---|---|---|
| NAR122 (51), 220 mm rocket (52), NAR340 (55) | **130** | `FireShell` | ttl 10 s (51, 55) / 30 s (52); mask 7; `+0x3d4` = 1.5 | 5.2 |
| 300 mm rocket (54) | **132** | `FireShell` | ttl 30 s; mask 7; no `+0x3d4` store (set in state 0) | 5.3 |
| Harpoon (90) | **135** (projectile) | `FireShell` | `FireShell` also sets the *firing part's* logic to **137** (`0x89`, `+0x3c8 = 1`) | 135: arm only (creature-logic-id-map.md); 137 not read |
| Canister 60 | **110** | `FireShell` | ttl 12, explosive 200, `+0x3d4` = 0.6 | timed fuse: explode 0.6 s after launch |
| Canister 70 | **120** | `FireShell` | ttl 30, explosive 0, `+0x3d0` = 1.2, `+0x3d4` = 20, `+0x3d8` = 500 | delayed warhead (see creature-logic-id-map.md) |
| Plain shell, AP, INC | 100 | `BulletImpact__` | | shell-detonation-paths.md |
| `_LG` guided shell | **140** | `BulletImpact__` | | 5.4 |
| `_PROXY` shell | **160** | `BulletImpact__` | | 5.5 |
| bomblets of 130/132 rockets | **190** | `FUN_14001c890` | | 5.6 |
| bomblets of proximity shells / mines | 0 (no logic; `CreateShell_` bodies) | `FUN_140032fb0` = `Projectile_ExplodeAndCluster` | see cluster-bomblet-ttl.md | |
| debris of a dead part | **550** | `Body_DieExplode` | | 5.7 |
| tactical missile `MDL_MISSILE_01` (Zenith) | **1** (stats index 130; do not confuse) | ship part, detaches | | flares-and-missiles.md, zenith-steering.md |
(Ammo 130 caliber ids come from the live dump in ammo-1151-vs-1163.md: NAR122 / 220 mm / NAR340 = 130, 300 mm = 132.) Logic id 150 has no vanilla producer I could find (no `FireShell` or ammo entry stores it); 210 is still unread.

### 5.2 Logic 130: rocket with cluster burst
* **Thrust [V]:** while `+0x3d4 > 0` (decremented by dt, starts at 1.5 s), each tick a force `mass * 500.0` (`0x140352838`) is applied along the body's heading (the vector (0,-1) rotated by the body rotation at `+0x8fc`) through vtable `+0x178`. If that slot is `ApplyForce` the acceleration is 500 u/s^2 for 1.5 s (about +750 u/s on top of the launch speed); if it is an impulse call it would be 500 * mass * ... per tick: **not checked** [guess: force]. The tail flame effect field `+0x92c` is zeroed when the burn is over. No steering: the rocket keeps its launch heading (the ammo `speed` and spread are in `FireShell`).
* **States [V]:** 0 (first tick): `+0x3d0 = 0.3`, state 1. State 1: when the timer reaches 0 (0.3 s): `+0x38c = 25 * mass` (arming threshold, so `Projectile_DetonateOnImpulse` can trigger), `+0x3d0 = 0.5`, state 2. State 2: when the timer is exactly 0 (0.5 s later, 0.8 s after launch) **and `+0x3e4 == 2`** the burst test runs every tick. (What sets `+0x3e4 == 2` for rockets is not traced; the field is written by `bodySecondaryInit 0x140027495` and by several `creatureLogic` blocks.) **OPEN.**
* **Burst test [V]:** over the ship list `[0x143faa5d8, 0x143faa5e0)` (stride 0x18): skip entries whose side (`+0xad4`) times the owner's side is positive (same side); distance (`FUN_14020fc80(self, ship+0x1840)`) must be <= **500**; the angle between the rocket's velocity direction and the direction to the ship must be < **0.6283 rad (36 deg)** (`0x1403546f0`).
* **Burst effect [V]:** `n = (int) clamp(explosive / 50, 2, 15)` bomblets by `FUN_14001c890(self, speed = 100, mode = 1, n, per-bomblet explosive = explosive / n, ttl = 30.0)`, then the rocket's own explosive becomes `max(explosive / 20, 10)` and `Body_DieExplode` runs (vtable `+0x200`). Example: 220 mm rocket (explosive 180) gives 3 bomblets of 60 and a 10-unit blast; NAR340 and NAR122 values come from their ammo records.
* A rocket that hits something first detonates through `Projectile_DetonateOnImpulse` once armed (`+0x38c`), like any shell.

### 5.3 Logic 132: 300 mm rocket (explosive 500)
* **State 0 [V]:** the launch ref angle `+0x3d0 = fmod(owner +0xbb4, 2 pi)` when an owner link (`+0x4b0`) is present and passes `FUN_140049e00(owner, 0x2f)` (else 0), `+0x3d4 = 1.5` (burn), and the body is **detached from its master and added to the world** exactly like the Zenith ejection (vtable `+0x68`, then level node vtable `+0x50`); position is offset by rotated (0,-1) times the radius `+0x20c` (x2), velocity set to the master's velocity (`+0x130/+0x134`), plus smoke / rocket-glow particle bodies (`FUN_1401218f0` / `FUN_1402e30e0`). `+0x3d8 = 1.5` (guidance-free time), `+0x38c = 25 * mass`, state 1. So 132 is **a ship part launched like a Zenith** as well as a `FireShell` product; both paths reach this block.
* **Heading [V]:** each tick, if `+0x3d0 != 0`, `angle += (ref - angle) * dt * 5.0` (`0x140352810`): the rocket turns smoothly toward the launcher's aim angle (a first-order lag, rate 5/s, so it does not track a moving target).
* **Thrust [V]:** same as 130: `mass * 500` along the heading while `+0x3d4 > 0` (1.5 s).
* **Fuze [V]:** when `+0x3d8` (counted down by dt) reaches 0, i.e. 1.5 s after launch, and `+0x3e4 == 2`: scan the body array (`0x143a33c90`, count `0x143a51150`) for active bodies with mask != 0, `+0x948 == 0`, a different owner group (`+0xc0`), not flag 0xd, vtable `+0x1a8` false, **radius `+0x20c >= 20`**, and surface distance (`FUN_14020fb80`) <= 500; keep the nearest `d1` and the second nearest `d2`. It detonates when `d1 + d2` stops decreasing (`d1 + d2 > previous value in +0x3dc`): closest approach passed. [guess for the "closest approach" reading; the compare is certain.]
* **Burst [V]:** `n = (int) clamp(explosive / 20, 5, 50)` bomblets (500 / 20 = 25), `FUN_14001c890(self, speed = 400, mode = 2, n, explosive / n, ttl = 2.0)`, then own explosive `max(explosive / 20, 10)` (= 25) and `Body_DieExplode`.

### 5.4 Logic 140: laser-guided shell (`_LG`)
* State 0: the shell registers itself in its owner's list (`owner + 0xd40`, `FUN_140194de0`) and sets `+0x3d0 = 100 / |v|` (arming delay = 100 units of travel), state 1. State 1: timer counts down past 0, then `+0x38c = 25 * mass`, state 2.
* State 2 (guidance) needs the owner (`+0xb8`) and a target link (`+0x498`): the aim point is the owner's world aim position `owner + 0x1840` and aim angle `owner + 0xbb4`. Among enemy ships (list `0x143faa5d8`, skipping dead ships and same-side) it picks the one closest to the aim line, within **0.5236 rad (30 deg)** (`0x1403527a8`) of the aim direction (`0x1403546a8` = 0.2618 rad is a nearer-priority angle), then builds a lead point on the aim line at distance `clamp(dist_target - 200, 50, 400)` and turns the shell's **velocity direction toward it by at most 0.4 rad per tick** (`0x1403546cc`; 2 pi, i.e. unlimited, when the target is closer than 100), keeping the speed; the correction is applied through vtable `+0x178` as `(new_v - v) * mass`-style input [guess for the exact call]. Details of the lead construction are only skimmed; do not model it more finely than "the shell steers to the owner's aim line with a 0.4 rad/tick turn cap" without re-reading `0x140034470..0x14003482f`.

### 5.5 Logic 160: proximity shell (`_PROXY`)
* State 0: `+0x3d0 = 100 / |v|`; state 1: wait for the timer (it counts down below 0), then state 2 (armed at `+0x3cc == 2`; the shell is armed for contact only after `+0x38c = 25 * mass`? **not set in this block**, so contact detonation uses the shell's normal rule).
* State 2 [V]: for each body in the body array: active, mask != 0, `+0x948 == 0`, different owner group (`+0xc0`), not flag 0xd, distance (`FUN_14020fb80`) <= **150** (`0x140354870`), and the angle between the shell's velocity direction and the direction to the body's position is < **0.6283 rad**: trigger. Effect: `n = (int) clamp(explosive * 0.25, 5, 15)` fragments by `Projectile_ExplodeAndCluster 0x140032fb0(self, 1.0, n, explosive / n, 0, ttl = 0.3, angle 0, speed 1000)`, then own explosive `max(explosive / 5, 10)` and `Body_DieExplode`. The 0.3 s fragment ttl matches cluster-bomblet-ttl.md (first call site, literal 0.3).

### 5.6 Logic 190: bomblet of a rocket burst
Made by `FUN_14001c890` (sets logic 190, health 5, mask 7, drag `+0x1dc = 0.01`, `+0x2dc = per-bomblet explosive`, `+0x2c0` ttl `= rand(0.5, 1.0) * ttl_arg` (30 s for 130-rockets, 2 s for 132), `+0x38c = mass`). Scatter: mode 1 (logic 130 rockets) = parent velocity + a random direction times `rand(-1, 1) * 100`; mode 2 (logic 132) = a random direction times `rand(0.7, 1.0) * 400`, no parent velocity [from the decompile, the speed argument is read from XMM1 and is not shown by it; the 100 / 400 values are the XMM1 constants at the call sites, so [guess] for their role]. Own logic: state 0 `+0x3d0 = 50 / |v|` (arming by distance), then state 2 scans for the nearest active body that has stats flag `0x100` and is not on the owner's side (`+0x1804` list test), within **150**; when found it aims and spawns one directed burst through `0x140032fb0(.., count 1, explosive = +0x2dc, ttl 1.0, 2000)` and then `max(e / 5, 10)` + `Body_DieExplode`.

### 5.7 Logic 550: debris (what the simulator logs as N/X rows with hp 100, ttl ~2, owner -1)
* **Spawn [V]:** in `Body_DieExplode` (`0x140023ac0`), when the dying part's stats flags (`+0xb0` of the stats record) have bit 10 (0x400, aircraft part), bit 14 (0x4000, tactical missile) or bit 27 (0x8000000), it is **not** turned into a shell-like blast but into debris: `count = (int)(rand_int(2, 5) * k)` with `k = 1` (default), `2` (bit 10) or `3` (bit 27); each fragment is a new body (`New(0xa40)`, `CreateShell_` with the dead part's sprite index `+0x128`/`+0x12c`), logic **550**, `+0x2c0` ttl `= rand(1, 3) * k` s (matches "ttl about 2"), timer `+0x3d0 = rand(0.001, 0.006)`, velocity = `rand(0.1, 1.0) * parent velocity` rotated by `rand(-r, +r)` with r = 0.1 rad (1.0 for bit 27); the part itself also becomes logic 550 (explosive `+0x2dc` = 20, `+0x38c = mass`, an impulse of `-mass * v / 3`) when bit 10 is set. Also the part's own explosive `+0x2dc` or `+0x170` triggers the blast routine `FUN_140029b60` first.
* **Per-tick logic [V]:** the velocity direction is rotated by a small angle each tick: with `th` = the angle between the velocity direction and straight down (0, -1) wrapped to (-pi, pi] (`0x140352814` = 2 pi remainder), `|dth| = +0x3d0 * clamp(1 - |th| / pi, 0, 1)`, sign from `th`, applied through vtable `+0x190` (set linear velocity): the fragments curve slightly (0.001 to 0.006 rad per tick, at most) [rotation sign / direction (toward or away from straight down) **not verified**; call it a small random curve in a sim]. Speed is unchanged by this block; the shell drag (`+0x1dc`) applies as for any body.
* The same code also spawns a ground-destroyed variant for logic 11000 and the "debris" particle effect (`debris.psi`: speed 100..500, life 0.4..10 s, gravity 50); those are visuals.
* **910** is not set by any `MOV [+0x3c4], imm` in the image (searched all writers); ids 400 and 200 are known (`creature-logic-id-map.md`); 910 likely comes from the data (`Stats`/level file) [guess]. 0 means "no logic". Logic ids 3506 and 910 are in `ai/ai-telemetry.md` as constant bodies (props), not projectiles.
