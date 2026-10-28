# Ghidra changes, 2026-10-28 (ammo funding / refund round)

Program `Highfleet.exe.unpacked.exe` v1.163, saved. The check-in to the shared project is the user's. Finding documented in [../findings/gun-ammo-funding-and-refund.md](../findings/gun-ammo-funding-and-refund.md).

| kind | address | change |
|---|---|---|
| plate (extended) | 0x1402698c0 | `ReturnCreatureGunAmmoToInventory`: added that it is also called on every pre-combat ammo pick (`ClickFunc` 0x140137d17 / 0x140137e70) and inside `InitBattleGunAmmoReserves`, not only at battle end; a hook that empties pools here can discard paid stock |
| plate (extended) | 0x14025fa30 | `InitBattleGunAmmoReserves`: added the two pre-combat callers (`FUN_1402d9500` on 0x147fc75a8, `ammoSelectButtonPress_` on the reserve list 0x147fc73b0) and that each call refunds then re-splits the stock |
| plate (extended) | 0x14026f880 | `ammoSelectButtonPress?`: first `InitBattleGunAmmoReserves(0x147fc73b0)`, then rebuild `AMMO_SELECT`; fires on pre-combat entry and after every ammo click |
| plate | 0x1402d9500 | called by `buildSquadPrecombatScreen` 0x1402d74ff; rebuilds the lists 0x147fc73b0 (player fleet) and 0x147fc75a8 (second argument vector) and calls `InitBattleGunAmmoReserves(&DAT_147fc75a8)` |
| comment (pre) | 0x140137cde | `ClickFunc` `AMMO_SELECT` branch: refund card ship → match `FindAmmoIndex` to `gui+0xc00` → write `gui+0xc04/+0xc08` to `gun+0x850/+0x854` → call 0x14026f880 |
| comment (pre) | 0x140137e27 | `ClickFunc` `AMMO_SELECT2` branch: same path (refund 0x140137e70, call 0x140137f73) |
| plate (global, appended) | 0x147fc73b0 | player reserve list: also rebuilt by `FUN_1402d9500`, and `ammoSelectButtonPress_` refunds/re-splits its gun stock on every ammo click |
| plate (global, new) | 0x147fc75a8 | `std::list` rebuilt by `FUN_1402d9500`; `InitBattleGunAmmoReserves` is then called on it. Its pre-combat role was not read further; it is the wave list during the battle |

Re-read while annotating: `ReturnCreatureGunAmmoToInventory`, `InitBattleGunAmmoReserves`, `ammoSelectButtonPress_`, `FUN_1402d9500`, `ClickFunc` branches at 0x140137cde and 0x140137e27, `buildSquadPrecombatScreen`, and the two list globals. Not settled: the split byte in `FUN_1402d9500`; the other refund callers (extract / scene exits).

## Second batch: plane combat paths (2026-10-28, after the `extra_gunpod` work)

Program `Highfleet.exe.unpacked.exe` v1.163, saved. Finding: [../findings/plane-combat-modes-and-gunpods.md](../findings/plane-combat-modes-and-gunpods.md).

| kind | address | change |
|---|---|---|
| plate | 0x14000ae90 | `AircraftLogic_InitAndPickMode`: full `stateSelectorAircraft_` mapping (0/1/2/3/4), list offsets and writer table |
| plate (extended) | 0x14000bd50 | `AircraftLogic_Mode3_Bomber`: bomb call site 0x14000c3cd / entry 0x140009a80, rocket FireShell 0x14000c5be, no gun FireShell, no `+0xac/+0xb4` writes, pass loop and empty-payload behaviour |
| plate (extended) | 0x14000ceb0 | `AircraftLogic_Mode6_Default`: state-3 rocket/gun sites 0x14000d872/0x14000d930, field list, free magazine rule, class-3 stock-draw gate and max-part-count draw |
| rename + plate | 0x14000fa30 | `FUN_14000fa30` -> `AircraftLogic_UpdateAmmoTimers`; old name in plate. Documents `+0xb4` no-decrement when `+0x118 == 6` |
| plate (new) | 0x14000ea20 | `configure_plane_gun`: the six fields |
| plate (extended) | 0x14002e930 | `loadAmmoForAircraft`: `has_gun37mm` gate, live-dump evidence, class dispatch, unknown-loadout fallback, callers |
| plate (new) | 0x1402ca2b0 | `SCR_BOMBERS` role, `BOOL_147fc6fdb=1`, selector 2/3, spawn call, proven call chain, unproven links |
| plate (new) | 0x140267700 | group spawner: arms at 0x1402679c8 (owner 0), side via 0x14000e680, callers |
| EOL comments | 0x14000c3cd, 0x14000c5be, 0x14000d872, 0x14000d930, 0x14000d13c, 0x14000bd02, 0x14000b9c5 | bomb release, mode-3 rocket, mode-6 rocket/gun, class-3 draw gate, mode-2 and mode-0 gun |
| EOL comments | 0x1402c52ee, 0x1402c5540, 0x1402679c8, 0x1402ca326, 0x14013e02c | `SCR_BOMBERS` branch/call, arming call, `BOOL_147fc6fdb=1`, `EDC_TEST_FIGHT` sets `DAT_147fc6fb6=1` |
| global comments | 0x1403bd008, 0x147fc6fdb, 0x147fc6fb6 | mode selector, scripted-scene flag, Shipworks test flag |

Corrections from this pass: the 1.163 bomb-drop entry is `0x140009a80` (the Ghidra label `rep_1400094a0_Get_Profile?` keeps a stale 1.151 address); `FUN_1402cdaf0` = `SCR_COMBAT`, `FUN_1402cdfb0` = `SCR_COMBAT_SKIRMISH_PVP` (both selector 4); `DAT_147fc6fb6` has a second setter at `0x14013539d` besides `EDC_TEST_FIGHT`. The `SCR_BOMBERS -> FUN_1402ca2b0 -> 0x140267700 -> 0x14002e930` chain is proven at call level; what the output vectors hold and the bomber/escort split was not read.
