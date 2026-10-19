# highfleet-refuel  (repo `old_standalone/hf_refuel`)

> **Status (2026-10-19):** merged upstream into highfleet-qol (PR #19); installed with `player_rate_multiplier` 10. Standalone repo `old_standalone/hf_refuel` (local only) is the pre-merge version. See [qol.md](qol.md).

Multiplies the station refuel rate (the game's rule: section "How the game refuels" below). Settings `refuel.ini`: `player_rate_multiplier`, `ai_rate_multiplier`, `log_calls`.

* Mechanism: the rate is a float constant read by three `MULSS xmm0,[rip+disp]`; the constants (pooled `100.0f`/`200.0f`) are shared by hundreds of places, so only those three instructions
  are repointed (disp32 at +4) at private floats `base * multiplier`, placed just above the image. Bytes and targets are verified first; nothing changes on other builds.
* A huge multiplier means "fill at once": the amount is still capped by free tank space and station stock.
* `log_calls=1` hooks `FUN_1400ea980` and logs every delivery (amount, caller RVA, fleet timer fields); about 100,000 lines per minute, research only.
* Status: x5 for the player felt five times faster [game]; AI fleets unaffected at 1.
* **QoL port (merged into logdot/highfleet-qol as PR #19, `f5423ca`; pull request state: [../../STATUS.md](../../STATUS.md)):** same three sites, section `refuel` of `qol.json` (`player_rate_multiplier`, `ai_rate_multiplier`; no `enabled` flag and no clamp, any finite value is accepted including 0 and negatives, both default to `1.0` = the game's own rate). 1.163 only (not compiled into the 1.151 build; skipped at runtime unless the loader reports Steam 1.163). Config is read at startup only; `log_calls` was not ported. Log lines `Refuel rate patch prepared at 0x14011521f (200 -> 2000)` [game: seen in the 11:50 log on the Steam install]. The user reported x10 (200 -> 2000, 100 -> 1000) visibly works [game] (docked samples at 1 Hz: +102,000 fuel/s for several seconds, then +1,192,000 in one second); no clean A/B timing yet. Remove the standalone `refuel.dll` when using it.

## How the game refuels [game]
Moved from the retired `systems.md` (2026-10-19).

Per frame, inside the fleet update, for a docked fleet (`RSI`), station (`R15`), frame time (`XMM15`):
`amount = min(fleet.capacity(+0x4a0) - fleet.fuel(+0x498), dt * RATE, station.stock(+0x274))`, `added = FUN_1400ea980(fleet, amount)`, `station.stock -= added`.
`RATE` = **200** at a type-4 station (`station+0x258 != 0 && station+0x25c == 4`), **100** otherwise, read by `MULSS` at `0x14011521f` / `0x140115240`; AI fleets use 100 at `0x14011529c`
(no stock accounting). Observed `dt` ~ 11.43 per frame step, so ~1143 fuel per call, 7 calls per ~19.5 ms.
* `FUN_1400ea980(Escadra*, double)` = add fuel to a fleet: spreads the amount over ships in proportion to free tank space (ship +0x1638 current, +0x1640 capacity, doubles; per-ship fill
  `FUN_140060d80`), adds the total to `fleet+0x498` (snaps to an integer within 0.1), returns it. Other callers: fuel from absorbed ships (`FUN_1400f9460`), scenario setup (5,000,000 once),
  shipworks exit (`FUN_1400d2260`), `FUN_1400a6230`, `FUN_1402017a0`, `FUN_140261a20`, `FUN_140290210`.
* `fleet+0x420 m_refuel_timer` / `+0x424 m_refuel_amount` are a delayed delivery (counted down in the fleet update, then delivered); they stayed 0 while refueling at a station.
  `+0x468` = refuel animation flag (`FUN_1400fe8b0`, sounds `refueling_start/loop/stop`); save/load `FUN_1400feb90`. The buy-fuel slider (`FUEL_BUY_SLIDER`) and the `MAPMODE_MISSION_FULLTANK` / `HALFTANK` branches are traced in [rendering/click-func.md](../rendering/click-func.md#decompiled-branches-v1163); `REFUEL_TIME` is untraced.
