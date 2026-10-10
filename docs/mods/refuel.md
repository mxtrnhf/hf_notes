# highfleet-refuel  (repo `hf_refuel`)

Multiplies the station refuel rate (rule in `../systems.md`, "Refueling"). Settings `refuel.ini`: `player_rate_multiplier`, `ai_rate_multiplier`, `log_calls`.

* Mechanism: the rate is a float constant read by three `MULSS xmm0,[rip+disp]`; the constants (pooled `100.0f`/`200.0f`) are shared by hundreds of places, so only those three instructions
  are repointed (disp32 at +4) at private floats `base * multiplier`, placed just above the image. Bytes and targets are verified first; nothing changes on other builds.
* A huge multiplier means "fill at once": the amount is still capped by free tank space and station stock.
* `log_calls=1` hooks `FUN_1400ea980` and logs every delivery (amount, caller RVA, fleet timer fields); about 100,000 lines per minute, research only.
* Status: x5 for the player felt five times faster [game]; AI fleets unaffected at 1.
