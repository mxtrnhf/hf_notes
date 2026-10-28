# Gun ammo reserves: funding in the pre-combat screen and the refund (1.163)

Status: the algorithms are [code], read in Ghidra 2026-10-28; the two bugs below are [game], seen in the `hf_ally` v0.13.3/0.13.4 runs. Addresses are 1.163 (image base `0x140000000`). Related: [ammo-1151-vs-1163.md](ammo-1151-vs-1163.md) (the ammo table, prices and logic ids), [../rendering/precombat-screen.md](../rendering/precombat-screen.md) (the screen), [battle-ally.md](battle-ally.md) (the ally).

## The two functions

### `ReturnCreatureGunAmmoToInventory` `0x1402698c0` (RCX = creature)
Refunds every gun of the creature to the player PROFILE (item list `Profile+0x2d0`, `AddItem` `0x140293bb0`). Gun lists: `+0x13a8` (group 0) and `+0x13c0` (group 1), `Link` stride `0x18`, gun at `+8`.

Per gun:
* **primary**: `idx = gun+0x850`; count = `gun+0x858` (int reserve) + `gun+0x860` (float loaded) + `gun+0x868` (int stepping in reload). Credited only if count > 0 **and** `AMMO_LIST[idx]+0x170` (shop price) != 0.
* **secondary**: `idx = gun+0x854`; count = `gun+0x85c`; same price test.
* then `+0x858/+0x860/+0x868/+0x85c` are zeroed.

The credit goes to the gun's **current index**, not the type the rounds were bought as. Base shells (price 0) are never credited; priced variants (`_AP`/`_PROXY`/`_INC`/`_LG`, rockets, bombs, K-13) are.

### `InitBattleGunAmmoReserves` `0x14025fa30` (RCX = `std::list` of creatures)
* First pass: refund every creature in the list (calls the function above).
* Per gun: if `+0x850`/`+0x854` is priced and the profile stock is 0, the index is cleared; an empty index is then filled with the first `AMMO_LIST` entry whose `+0x154` key equals `stats+0x144` (the gun's calibre key), and `+0x858`/`+0x85c` = 9999.
* Second pass: counts guns per ammo index across the list. Price 0 -> share `-1` -> every gun gets `+9999` free. Price > 0 -> share = `ceil(profile stock / gun count)`, taken per gun through `0x140270d60` (returns what was actually removed) and added to `+0x858`/`+0x85c`.

## When they run (the surprising part)
Despite the name, the reserves are funded while the **pre-combat screen** is up, twice:

* `FUN_1402d9500` (called by `buildSquadPrecombatScreen` `0x1402d74ff`) rebuilds the lists `0x147fc73b0` (player ships from the fleet property list) and `0x147fc75a8` (from the second argument vector), then calls `InitBattleGunAmmoReserves(&DAT_147fc75a8)`.
* `ammoSelectButtonPress_` `0x14026f880` first calls `InitBattleGunAmmoReserves(&DAT_147fc73b0)` (the reserve list), then rebuilds `AMMO_SELECT` for each card. It runs on screen entry **and after every ammo click**.

The click path (`ClickFunc`):
* `AMMO_SELECT` branch at `0x140137cde`: refund the card's ship (`0x1402698c0` at `0x140137d17`), then for each gun whose `FindAmmoIndex` (`0x14015f9a0`) equals the clicked entry (`gui+0xc00`) write `gui+0xc04 -> gun+0x850` and `gui+0xc08 -> gun+0x854`, then call `0x14026f880`.
* `AMMO_SELECT2` branch at `0x140137e27`: same (refund `0x140137e70`, call `0x140137f73`).

So every click refunds the ship's current pool to the profile and then re-splits the profile stock over the guns of the affected list.

## Consequences
* Only priced ammo is drawn from the profile; base shells are minted 9999 per gun for free. A base-shell gun must therefore never be refunded as a priced variant.
* The AI weapon controller rewrites `gun+0x850` every tick from the creature bytes `+0xc7c`/`+0xc7d` ([ai/ai-tick-patch-sites.md](ai/ai-tick-patch-sites.md) section 3). If it switches a base-shell gun to `_AP`/`_PROXY`, the refund credits the free 9999 pool as priced ammo: the "player gets ~20000 shells" bug.
* The refund also runs on every pre-combat ammo pick. A hook that empties or rewrites pools at this entry during the pre-combat screen discards the share the player just allocated: **ammo vanishes**. Seen with `hf_ally` v0.13.3/0.13.4 when the same type was picked for the player and the ally (log `Highfleet_2026-10-28_20-38-27.log`: refund lines at 20:50:31/32 while the cards were up, for the ship that had been an ally in the previous battle).
* A reserve ship keeps its creature pointer across battles, so mod bookkeeping keyed on the pointer must be cleared before the next pre-combat screen, not at the next battle start.

## The `hf_ally` fix (v0.13.5, commit `20ec6bb`)
* The refund hook does nothing while the pre-combat screen is up (`PRECOMBAT_LIVE` or a live `PRECOMBAT_A` card).
* At ally deploy, before the AI starts rewriting the index, it records `(creature, gun, +0x850, +0x854)` in `AMMO_FUNDING`. At a real refund it restores those indices first, so paid rounds go back under the type they were bought as while a free base pool is still not credited. Guns without a record keep the old empty-the-pool safeguard.
* Tested in game 2026-10-28: same ammo on player and ally, inventory holds before/after the battle.

## Open
* The split byte in `FUN_1402d9500` and the exact role of `0x147fc75a8` at pre-combat build time (it is the wave list during the battle per [battle-ally.md](battle-ally.md)).
* Other refund callers (extract `0x1401f3c10`, scene exits `0x1402ce060` / `0x1402ce8f0` / `0x1402ceee0`) were not re-read for this note.
