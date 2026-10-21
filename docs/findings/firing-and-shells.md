# Firing: `FireGun`, `FireShell` and how a cannon shell is set up (1.151 read, 1.163 mapped)

Status: **read from both decompilations; nothing run in game.** Tags: legend in `../../README.md`.
The ammo table itself and the 1.151 to 1.163 value changes are in [ammo-1151-vs-1163.md](ammo-1151-vs-1163.md). Weapon fields of the Body (`+0x850`..`+0x874`) are in [../version-differences.md](../version-differences.md).

## `FireShell`, the projectile factory (1.151 `0x1400307f0`, 1.163 `0x1400300d0`) [code]
Both versions carry logdot's header comment: *"Spawns a projectile based on ammo type index ... Dispatches on `ammo->index` ... Always spawns a muzzle flash body at the end regardless of ammo type."*
`FireGun` calls it (see the weapon fields in version-differences.md). 1.163 has one more argument (`param_8`) and `Body` allocations of `0xa40` (1.151: `0xa08`).

* **Dispatch is on `ammo->index`** (the `AmmoDefList` entry; stride `0x168` in 1.151 and `0x188` in 1.163; ammo definitions are built in `DefineAmmos`, see ammo-1151-vs-1163.md). Cases in **both** versions:
  `5, 10 (0xa), 15 (0xf), 20 (0x14), 25 (0x19), 30 (0x1e), 40 (0x28)` = the plain cannon shells (logdot's comments tag `10` as "57mm; can kill in one volley", `0xf` "180mm high explosive" (by the ammo table in ammo-1151-vs-1163.md, `0xf` is the **100mm** shell and `0x19` is the 180mm, so that comment is off by one calibre), `0x14` "130mm",
  `0x1e` "203mm normal shell"), `51 (0x33), 52 (0x34), 55 (0x37)` = rockets/missiles (sprite `missile_01`, particles `rocket_glow.psi`/`smoke_FIRE.psi`, sounds `missile_launch`/`missile_launch_far`),
  `60 (0x3c)` = a 3-pellet canister, `70 (0x46)` = a 6-pellet canister, `80 (0x50)` = EMP (`emp_01`). **1.163 adds `54 (0x36)` (another rocket variant) and `90 (0x5a)`** (a heavy shell that also
  changes the firing body's `logic` to `0x89` and sets projectile flags `0x10015`).
* **Where projectile hit points and lifetimes are set (roadmap: "HP modification for missiles, aircraft, rockets and cannon shells"):** rockets get `health = maxHealth = 10.0` and `timeToLive` `10.0` (cases 51/55) or
  `30.0` (cases 52/54) in this function; canister pellets get `health` 30.0 (case 60, explosive 200, TTL 12) or 10.0 (case 70, TTL 30, `explosive` 0); cluster bomblets are in [cluster-bomblet-ttl.md](cluster-bomblet-ttl.md). These are literal constants
  here, so an HP/TTL config means patching these stores (or reading ammo-definition fields if the game exposes them). Cannon shells go through `Body::BulletImpact__` (next section) instead.
* **Rocket logic:** the projectile's `logic` field is set to `ammo->caliber` and `isLogicActive = 1` (the missile guidance branch in `creatureLogic` keys on that id), `logicF2 = 1.5` is a guidance parameter, and
  `explosive = ammo->explosivePower`. So rocket speed and acceleration live partly in the ammo definition and partly in that logic branch (not in `FireShell`).
* **1.151 only: the "special behaviour" roll:** for enemy shooters, `behavior = 1.0` is scaled to `0.5` (difficulty 0) or `0.75` (difficulty 1), and each shell gets `field218_0x3b0 = (rand < behavior * p)` with
  `p = 0.5` for most shells, `0.8` for the 57mm and `0.2` for rockets. 1.163 no longer has the difficulty scaling; it computes a time value with `FUN_1401af7b0(n)` (n = 1, 3, 5, 6 or 8 depending on whether the owner is the
  player and on `Profile.field_0x164`) and stores it in the projectile (`+0x3c0`, the "launch timer" field of the Body table). That is the changed AI/difficulty rule; the 1.151 flag `+0x3b0` is gone.
* **Recoil and flash:** `apply_recoil_` applies an opposite impulse to the root body for the canister cases; the muzzle flash is a separate short-lived body (`timeToLive 5.0`, sprites `flash` / `flash_fire`).
* **1.163 extra:** `DAT_147fc6fd4` (the second flag besides `BOOL_147eed9ae` in 1.151) divides the flash size by 1.5, and the first branch (case 5) also calls `Random_Int(1,4)` when `param_8 == 0`.

## How a cannon shell is set up (`Body::BulletImpact__`, 1.151 `0x140050300`, 1.163 `0x140052a80`) [code]
Called by `FireShell` for every plain shell (cases 5 to 40) right after `CreateShell_`. Parameters (logdot's names where given): the shell body, the `Ammo` entry, the owner creature, the owner tag, the firing
body, the root body, the fire direction, a speed factor (1.0), `is_local_player`, `flash_power`, **`health`**, `shake_power`, a spread (`param_13`) and the fire power. What it sets:

* **Lifetime in 1.151:** `timeToLive = desowningTime = 10.0`, but `1.0` if the ammo has `penetrativePower` (AP shells fly for one second), `3.0` for index 10 (57mm) and `2.0` for index 5 (37mm).
  (`FireShell` passes the constants `1.25`/`0.25`/... for size and the mass per calibre; see the previous section.)
* **Damage fields copied from the ammo definition (ammo-1151-vs-1163.md):** `explosive = explosivePower`, `isArmorPiercing` (a float) `= penetrativePower`, `explosiveTemperature = incendiaryPower`,
  `dragLinear = apDrag`, and **`logic = ammo->caliber`** with `isLogicActive = 1`. So `caliber` in the ammo table is not a size but a **projectile logic id** (100 plain shell, 130 rocket, 140 laser guided,
  160 proximity fuze); the per-frame projectile code in `creatureLogic` branches on it. This is why `LG`/`PROXY` variants behave differently although they share the base calibre's `FireShell` case.
* **Launch impulse:** speed `= Random_Float(0.98, 1.2) * ammo->speed * speedFactor`, deflected by a random angle within `+-spread`, applied as an impulse scaled by the shell's mass; if the shooter is the
  local player the opposite impulse is applied to the firing body (recoil).
* **Hit points:** `maxHealth = health = <health parameter>`. Every `FireShell` call passes `1.0`, so **all cannon shells have 1 HP**. That single constant (the 9th/10th argument in each `BulletImpact__` call)
  is the "HP of cannon shells" in the roadmap item; the 300 mm and heavier shells do not get more.
* Effects: screen shake `shake_power` (the last float in each call: 5.0 for 37mm, 10.0 for 57mm, 15.0 for 100mm, 20.0 for 130mm, 30.0 for 180mm, 40.0 for 203mm, 60.0 for 305mm), muzzle `scaleY = gfxFlash * flash_power`, sounds from the ammo
  (`shellOutSound` for the local player at close zoom, `shellFarSound` otherwise). Enemy shooters on some difficulties halve the volume (`0.5`).
* **1.163 change:** the lifetime now comes from the per-ammo `ttl` field (`+0x16c` of the `Ammo` record), see ammo-1151-vs-1163.md.

## Live-test recipe
* Breakpoint at the `FireShell` dispatch (1.163 `0x1400300d0`): read the ammo `index` from the `Ammo` entry and check it against the case list above.
* Breakpoint after `BulletImpact__` returns: read the new shell's `+0x2c0` (time to live) and `+0x2c8` (health, expected 1.0).

## Firing chain, active protection (KAZ) and bomblets [code]
Moved from the retired `systems.md` (2026-10-19).

* **Firing chain:** AI weapon controller `FUN_14007a8d0` (and the player's input path) -> `FireGuns` `0x1400559e0` -> `FireGun` `0x140032e60` -> `FireShell` `0x1400300d0` (dispatch on the `Ammo` entry's `index`) -> `Body::BulletImpact__` (cannon shells, all with 1 HP). [findings/firing-and-shells.md](firing-and-shells.md); ammo table: [findings/ammo-1151-vs-1163.md](ammo-1151-vs-1163.md). Weapon fields of the Body: `+0x858` reserve rounds (int), `+0x860` loaded rounds (float) [structures.md](../structures.md).
* **Active protection (KAZ):** `FUN_14002f480` is the close-in burst of the "strides" sprites: it picks an incoming projectile within 60/120 units and 45 degrees, spends one count and damages it with the target's own explosive power; stats categories `0x4000`, `0x8000000`, `0x200000` are excluded. Called from `FUN_14007eb50`. Matches the KAZ category (bit 25) [guess] and `ITEM_KAZ_AMMO` (1.163).
* **Shell detonation (added 2026-10-21 from the simulator session):** a plain shell (logic id 100) arms after `20/|v|` s and then explodes at the first processed contact with `160000 * raw impulse > 25 * mass` (thresholds 24 / 90 / 397 / 793 / 2140 / 2850 for 37 / 57 / 100 / 130 / 180-305 / 203 mm); contact damage does not matter. `FUN_14002f480` above is `Weapon_FlakInterceptScan`, which detonates every explosive body within 120 units and 45 degrees of the gun. Details, probe evidence (64/64 chains) and the other detonation paths: [shell-detonation-paths.md](shell-detonation-paths.md); logic id table: [creature-logic-id-map.md](creature-logic-id-map.md). Sim status: not implemented yet (shells currently use the old contact model); implement the rule above.
* **Bomblets:** cluster and mine bomblets are spawned by `FUN_140032fb0` (TTL is its sixth argument): [findings/cluster-bomblet-ttl.md](cluster-bomblet-ttl.md).
