# highfleet-speed  (repo `old_standalone/hf_speed`, published)

> Merged upstream into highfleet-qol (PR #19). Standalone repo `old_standalone/hf_speed` (published as `highfleet-speed`) is the pre-merge version. See [qol.md](qol.md).

Configurable **map cruise speed**. Vanilla 1.163: `speed = 50 * sqrt(TWR - 1)` m/s; 1.151: `25 * TWR`.

* Config `speed.ini`: `preset` = `vanilla` | `classic` | `custom`; custom: `speed = coefficient * max(TWR - subtract, 0) ^ exponent`; `max_kmh` cap. Reloads within ~1 s; reopen the ship (speed is cached).
* Mechanism: the `call powf` at `0x140080699` inside `FUN_14007fcf0` is redirected to `SpeedCurve()` through a stub in the `0xCC` cave at `0x140073330`; 24 bytes around the call and the stub site are verified first.
* Status: works [game], also on Windows. Runs alongside highfleet-qol.
* **QoL port (merged into logdot/highfleet-qol as PR #19, `f5423ca`; pull request state: [../../STATUS.md](../../STATUS.md)):** section `speed` of `qol.json` (`preset` = `vanilla`|`classic`|`modern`|`custom`, `coefficient`, `subtract`, `exponent`, `max_kmh`); there is no `enabled` flag (logdot's PR #19 review): the default preset `vanilla` (= `modern` on 1.163, `50*(TWR-1)^0.5`) leaves the game untouched, `classic` is the 1.151 curve `25*TWR`. Patches the `call powf` at `0x140080699` through patchy (no code cave) after verifying the 24-byte window and the `50.0f` constant. 1.163 only, config read at startup only (the 1 s hot reload of `speed.ini` was dropped). Log line `Speed curve patch prepared at 0x140080699` [game: seen in the 11:49/11:50 logs]. The user reported custom speed 50*TWR visibly works [game]; editor km/h values are not yet compared numerically. Remove the standalone `speed.dll` when using it.

## How the game computes map cruise speed [game]
Moved from the retired `systems.md` (2026-10-19).

The ship stats routine `FUN_14007fcf0` computes `powf(TWR - 1, 0.5)` at `0x140080699`: speed = `50 * sqrt(TWR - 1)` m/s in 1.163 (internal unit; the UI and `speed.log` show km/h = m/s x 3.6) (1.151 used `25 * TWR`). The game caches each ship's speed.


## Engine names and mount types (2026-10-20)
`MDL_ENGINE_01` = RD-59 (swivels), `02` = RD-59S (static), `03` = D-30 (swivels), `04` = NK-25 (swivels), `05` = D-30S (static; "S" means static), `06` has no placeable prototype. Whether an engine swivels follows its mount type `m_slot_type` in `Libraries/parts.seria` (before `m_oid`): 162 (01) and 146 (03, 04; the same as every cannon) rotate, 1121 (02) and 1105 (05; the type of rigid blocks) do not [file]; details and the joint serializer in [structures.md](../structures.md) ("Engines: names, mount types and which ones swivel"). Burn stats exist only on fuel tanks and engines: [findings/contact-damage-and-fire.md](../findings/contact-damage-and-fire.md).
