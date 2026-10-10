# highfleet-speed  (repo `hf_speed`, published)

Configurable **map cruise speed**. Vanilla 1.163: `speed = 50 * sqrt(TWR - 1)` m/s; 1.151: `25 * TWR`.

* Config `speed.ini`: `preset` = `vanilla` | `classic` | `custom`; custom: `speed = coefficient * max(TWR - subtract, 0) ^ exponent`; `max_kmh` cap. Reloads within ~1 s; reopen the ship (speed is cached).
* Mechanism: the `call powf` at `0x140080699` inside `FUN_14007fcf0` is redirected to `SpeedCurve()` through a stub in the `0xCC` cave at `0x140073330`; 24 bytes around the call and the stub site are verified first.
* Status: works [game], also on Windows. Runs alongside highfleet-qol.
