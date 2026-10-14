# highfleet-speed  (repo `hf_speed`, published)

Configurable **map cruise speed**. Vanilla 1.163: `speed = 50 * sqrt(TWR - 1)` m/s; 1.151: `25 * TWR`.

* Config `speed.ini`: `preset` = `vanilla` | `classic` | `custom`; custom: `speed = coefficient * max(TWR - subtract, 0) ^ exponent`; `max_kmh` cap. Reloads within ~1 s; reopen the ship (speed is cached).
* Mechanism: the `call powf` at `0x140080699` inside `FUN_14007fcf0` is redirected to `SpeedCurve()` through a stub in the `0xCC` cave at `0x140073330`; 24 bytes around the call and the stub site are verified first.
* Status: works [game], also on Windows. Runs alongside highfleet-qol.
* **QoL port (2026-10-14, fork branch `refuel-rate`, not merged upstream):** section `speed` of `qol.json` (`enabled`, `preset` = `classic`|`custom`, `coefficient`, `subtract`, `exponent`, `max_kmh`); vanilla is `enabled: false`. Patches the `call powf` at `0x140080699` through patchy (no code cave) after verifying the 24-byte window and the `50.0f` constant. 1.163 only, config read at startup only (the 1 s hot reload of `speed.ini` was dropped). Log line `Speed curve patch prepared at 0x140080699` [game: seen in the 11:49/11:50 logs; editor km/h values still to be compared]. Remove the standalone `speed.dll` when using it.
