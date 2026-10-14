# highfleet-refuel  (repo `hf_refuel`)

Multiplies the station refuel rate (rule in `../systems.md`, "Refueling"). Settings `refuel.ini`: `player_rate_multiplier`, `ai_rate_multiplier`, `log_calls`.

* Mechanism: the rate is a float constant read by three `MULSS xmm0,[rip+disp]`; the constants (pooled `100.0f`/`200.0f`) are shared by hundreds of places, so only those three instructions
  are repointed (disp32 at +4) at private floats `base * multiplier`, placed just above the image. Bytes and targets are verified first; nothing changes on other builds.
* A huge multiplier means "fill at once": the amount is still capped by free tank space and station stock.
* `log_calls=1` hooks `FUN_1400ea980` and logs every delivery (amount, caller RVA, fleet timer fields); about 100,000 lines per minute, research only.
* Status: x5 for the player felt five times faster [game]; AI fleets unaffected at 1.
* **QoL port (2026-10-14, fork branch `refuel-rate`; upstream PR #19 open, CI red until #18 merges):** same three sites, section `refuel` of `qol.json` (`enabled`, `player_rate_multiplier`, `ai_rate_multiplier`, clamped 0.01 to 10000). 1.163 only (not compiled into the 1.151 build; skipped at runtime unless the loader reports Steam 1.163). Config is read at startup only; `log_calls` was not ported. Log lines `Refuel rate patch prepared at 0x14011521f (200 -> 2000)` [game: seen in the 11:50 log on the Steam install]. The user reported x10 (200 -> 2000, 100 -> 1000) visibly works [game] ([../findings/seam-test-run-1.md](../findings/seam-test-run-1.md)); no clean A/B timing yet.. Remove the standalone `refuel.dll` when using it.
