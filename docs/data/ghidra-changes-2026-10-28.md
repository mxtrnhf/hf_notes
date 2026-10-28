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
