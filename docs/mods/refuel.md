# highfleet-refuel  (repo `old_standalone/hf_refuel`)

Multiplies the station refuel rate (rule in `../systems.md`, "Refueling"). Settings `refuel.ini`: `player_rate_multiplier`, `ai_rate_multiplier`, `log_calls`.

* Mechanism: the rate is a float constant read by three `MULSS xmm0,[rip+disp]`; the constants (pooled `100.0f`/`200.0f`) are shared by hundreds of places, so only those three instructions
  are repointed (disp32 at +4) at private floats `base * multiplier`, placed just above the image. Bytes and targets are verified first; nothing changes on other builds.
* A huge multiplier means "fill at once": the amount is still capped by free tank space and station stock.
* `log_calls=1` hooks `FUN_1400ea980` and logs every delivery (amount, caller RVA, fleet timer fields); about 100,000 lines per minute, research only.
* Status: x5 for the player felt five times faster [game]; AI fleets unaffected at 1.
* **QoL port (merged into logdot/highfleet-qol as PR #19, `f5423ca`; pull request state: [../../STATUS.md](../../STATUS.md)):** same three sites, section `refuel` of `qol.json` (`player_rate_multiplier`, `ai_rate_multiplier`; no `enabled` flag and no clamp, any finite value is accepted including 0 and negatives, both default to `1.0` = the game's own rate). 1.163 only (not compiled into the 1.151 build; skipped at runtime unless the loader reports Steam 1.163). Config is read at startup only; `log_calls` was not ported. Log lines `Refuel rate patch prepared at 0x14011521f (200 -> 2000)` [game: seen in the 11:50 log on the Steam install]. The user reported x10 (200 -> 2000, 100 -> 1000) visibly works [game] (docked samples at 1 Hz: +102,000 fuel/s for several seconds, then +1,192,000 in one second); no clean A/B timing yet. Remove the standalone `refuel.dll` when using it.
