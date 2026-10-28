# Plane combat: modes, bomb/rocket → gun fallback, and tactical-only gunpods

Status: [code] read in Ghidra 2026-10-28; [game] seen in the Shipworks/campaign logs of 2026-10-28; [mod] the `hf_ally` v0.13.6/v0.13.7 behaviour. Addresses are 1.163 (image base `0x140000000`). Related: [carrier-plane-loadouts.md](carrier-plane-loadouts.md) (loadout tables, arming internals), [map-air-groups.md](map-air-groups.md) (strategic craft flows), [../mods/hf-ally.md](../mods/hf-ally.md).

## 1. The plane mode comes from one global

`AircraftLogic_InitAndPickMode` `0x14000ae90`, called at the end of `loadAmmoForAircraft` `0x14002e930`, reads `stateSelectorAircraft_` `0x1403bd008`:

| Selector | Mode | Condition |
|---|---|---|
| 0 | 0 (fighter), state 3 | no bombs `+0x128`/rockets `+0x138`, gun index `+0x1a4 != 0`, gun rounds `+0xb4 + +0xac > 0` |
| 0 | 1 (retirement), state 1 | otherwise |
| 1 | 2 (interceptor), state 3 | always |
| 2 | 3 (bomber), state 3 | bombs or rockets non-empty |
| 2 | 4, state 5 | no bombs and no rockets |
| 3 | 3 (bomber) | bombs or rockets non-empty |
| 3 | 4 / 5, state 3 | no payload; 5 if a gun with rounds exists, else 4 |
| 4 | 6 (default), state 0 | always |

Scene writers:

| Address | Setter | Value | Scene |
|---|---|---|---|
| `0x1402cf53b` | `FUN_1402cf4d0` | 0 | `CraftsVsCrafts.seria` |
| `0x1402d0d7f` | `0x1402d0d20` | 1 | `CraftsVsMissile.seria` |
| `0x1402d4618` | `0x1402d45c0` | 1 | `Missile.seria` |
| `0x1402ca80a` | `FUN_1402ca2b0` | 2 or 3 | scripted bomber / tutorial branch (`SCR_BOMBERS`/`TUTORIAL_AAM_CRAFTS`) |
| `0x1402cdb21` | `FUN_1402cdaf0` | 4 | `SCR_COMBAT` |
| `0x1402cdfba` | `FUN_1402cdfb0` | 4 | `SCR_COMBAT_SKIRMISH_PVP` |

So **normal campaign/tactical combat runs mode 6**, while the strategic bomber scene runs mode 3. The live 2026-10-28 logs agree (`mode 6` for carrier planes in campaign).

## 2. What each mode fires

| Mode | Handler | Weapons | Exit |
|---|---|---|---|
| 0 | `AircraftLogic_Mode0_Fighter` `0x14000b610` | gun `FireShell` `0x14000b9c5` + K-13 | state 5 when gun rounds and K-13 are gone |
| 2 | `AircraftLogic_Mode2_Interceptor` `0x14000ba70` | gun `FireShell` `0x14000bd02` + K-13 | **no exit in the handler** |
| 3 | `AircraftLogic_Mode3_Bomber` `0x14000bd50` | bombs (call site `0x14000c3cd`, entry `0x140009a80`) + rockets `FireShell` `0x14000c5be` | loops passes 2→3→4→1→2; with empty payload it circles and does not fire |
| 6 | `AircraftLogic_Mode6_Default` `0x14000ceb0` | state 3: rockets `FireShell` `0x14000d872`, then gun `FireShell` `0x14000d930` | state 0 circle → state 1 retire; no attack order in vanilla campaign |

Mode 3 has **no gun FireShell at all**: `+0xac` is only a guard in the rocket branch, and the handler never writes `+0xac/+0xb4`. Adding a 37 mm to a mode-3 plane does not make it shoot it. Mode 6 state 3 is the vanilla "rockets first, then the gun" path; mode 2 is the persistent interceptor path that also fires the gun. The bomb-drop entry is `0x140009a80`; `0x1400094a0` appears only in the stale 1.151-derived Ghidra label.

`FUN_14000fa30` (renamed `AircraftLogic_UpdateAmmoTimers` in the 2026-10-28 annotation round) skips the `+0xb4` reserve decrement when `logic+0x118 == 6`, so a mode-6 gun reloads for free (effectively unlimited 37 mm). Modes 0/2 consume the reserve; `configure_plane_gun` gives the 37 mm a 20-round magazine + 30 reserve.

## 3. FAB/NURS planes have no 37 mm in a normal battle

`loadAmmoForAircraft` `0x14002e930` adds `ITEM_GUN37` only if:

- `BOOL_147fc6f80` or `DAT_147fc6f81` (hot-seat / second-profile flags; 0/0 in a normal campaign battle), or
- the loadout's `has_gun37mm` byte `+0x9c` is set.

Live loadout dump: `LOADOUT_*_FAB100`, `_FAB250`, `_NURS122`, `_NURS340` all have `has_gun37mm = false`; `LOADOUT_*_GUN37` and `_K13` have it true. So in a normal battle a bomb/rocket plane has no gun index (`+0x1a4 == 0`) until a mod gives it one. `configure_plane_gun` `0x14000ea20` writes `+0x1a4` (ammo index), `+0xa0 = 2.0`, `+0xa8 = ammo+0x17c` (fire delay), `+0xb0 = +0xac = ammo+0x180` (magazine), `+0xb4 = max(0, 50 - magazine)`.

## 4. The vanilla class-3 stock auto-draw (the "free NAR-122" leak)

In `AircraftLogic_Mode6_Default` `0x14000ceb0`, the class-3 stock draw is gated at `0x14000d13c` (`movss xmm0,[rdi+0x98]`), skips to `0x14000d335` when it runs, and for player-side planes (`logic+0xc8 > 0`) with an empty rocket list scans `AMMO_LIST` for class-3 records that appear in **any loadout of the craft** (`PLANE_TLL[plane+0x190]`). It removes up to the largest part count from the profile and pushes that many entries into `+0x130/+0x138`.

Consequence seen in the 2026-10-28 23:11 Shipworks log: a `LOADOUT_LA29_FAB100` plane started with `bombs=2, rockets=6` — the six `ITEM_NAR122` of `LOADOUT_LA29_NURS122` — and mode 3 fired them before the new gun phase.

## 5. `hf_ally` v0.13.6 / v0.13.7

- `extra_gunpod` (default on) gives a chosen FAB/NURS plane the 37 mm **only in the normal tactical battle** (`Combat.seria`: `stateSelectorAircraft_ == 4` and `BOOL_147fc6fdb == 0`).
- Once **both** bombs and rockets are empty, the plane is switched to mode 2 / state 3 and keeps using the 37 mm until it is dry or its `+0x158` target dies, instead of state 5.
- The gunpod is added only to **`CRAFT_T7` / `CRAFT_LA29`**. Custom crafts such as `CRAFT_SB15` keep their own loadout and vanilla leave-after-payload behaviour; an SB-15 must not get a gunpod invented for it.
- If the loadout already has a gun (class-4 item / QoL `gun_ammo`, including custom ammo), it is kept. If `ITEM_GUN37` is missing, the gunpod falls back to the first class-4 ammo record and uses its live magazine/fire-delay.
- The no-draw gate is registered for **every** chosen loadout (bombs, rockets, K-13, guns-only), so a chosen loadout carries exactly its listed parts; the class-3 top-up no longer adds NAR-122.
- Custom ammo is handled by the live ammo record's class (2 bombs, 3 rockets, 4 gun, 5 K-13), not by item name.

## 6. Why the strategic bomber scene must be excluded

The `SCR_BOMBERS` branch is at `0x1402c52ee` (string `SCR_BOMBERS` at `0x140375a78`). Its state machine calls `FUN_1402ca2b0` at `0x1402c5540`; that function sets `stateSelectorAircraft_` to 2/3 at `0x1402ca80a` and spawns the strike planes through `rep_140245ab0_New` `0x140267700`, which calls the normal arming function `0x14002e930` at `0x1402679c8`. So a global `has_gun37mm` flip or an unconditional "give every FAB plane a gun" would reach the strategic bombers too. The `Combat.seria` selector check plus the vanilla-craft list keeps the gunpod in tactical carrier combat.

## 7. Custom plane / custom ammo example in this install

`Modloader/config/qol.json` defines `CRAFT_SB15` with `LOADOUT_SB15_FAB100` (8x `ITEM_FAB100`), `_FAB250` (4x), `_NURS122` (24x `ITEM_NAR122`) and `_ROCKET` (1x `ITEM_AMMO_300MM_INC`). None has `gun_ammo`, so the mod does not add a gunpod to it. The custom SB-15 part is embedded in `Objects/Designs/Slingshot.seria` (not `Libraries/parts.seria`); qol registers the craft/loadouts, and the live table read sees `CRAFT_SB15`. `ITEM_AMMO_300MM_INC` is a class-3 ammo record, so `LOADOUT_SB15_ROCKET` is classified as Rockets and the no-draw gate prevents the 24 NAR-122 from being added to it.

## Verification / open

- A 2026-10-28 Ghidra subagent re-read the mode selector, both weapon handlers, the loadout arming, the class-3 draw and the `SCR_BOMBERS` chain and annotated them. It corrected the bomb-drop entry to `0x140009a80` (call site `0x14000c3cd`) and labelled `FUN_1402cdaf0` = `SCR_COMBAT`, `FUN_1402cdfb0` = `SCR_COMBAT_SKIRMISH_PVP`; `FUN_14000fa30` was renamed `AircraftLogic_UpdateAmmoTimers`. The Ghidra changes are in [../data/ghidra-changes-2026-10-28.md](../data/ghidra-changes-2026-10-28.md).
- The 23:11 Shipworks log is in the game folder (`Modloader/logs/Highfleet_2026-10-28_23-11-12.log`), not in this notes repo; the static auto-draw mechanism is verified, the specific observation is [game].
- `extra_gunpod` gunnery/strafing was seen in campaign; the v0.13.7 no-draw/custom-craft gate still needs a Shipworks/SB-15 re-test.
