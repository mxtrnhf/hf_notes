# The end game: `spawnEndgameShips_` and what it sets (1.151 read, 1.163 located)

Status: **read from the 1.151 decompilation; 1.163 counterpart located (see [khiva-crash.md](khiva-crash.md)); not run in game.** Tags as in `../../README.md`: **[game]** verified on the real game files or in play · **[code]** read from the decompilation · **[tool]** produced by Ghidra's fuzzy matcher (a similarity score, not proof) · **[guess]** inferred · **[not read]** known gap.

Present in 1.151 as a named function; **not matched** by the fuzzy tool, **located by hand in 1.163 as `FUN_140261a20` (khiva-crash.md)**. It is the scripted collapse that begins the "nuclear war" and closes the campaign. Read from the
1.151 decompilation (very long: three-way list sorting plus spawns).

* **Cities used by name:** `KHIVA` (the capital) and `BASRA`. Everything is positioned relative to `KHIVA`'s position.
* **Phase 1, sort the garrisons:** it walks the profile's city list (the vector at Ghidra offset 456/464) and drops those that already have a hostile fleet with `side > 0` within `700.0`. The remaining cities (with
  `moid+0xc != 0`, i.e. an active flag) are split into **four lists by quadrant relative to Khiva** (x below/above, y below/above) and each list is sorted by distance (`MergeSortObjectListByScratchKeyDescending`,
  key at `+0xf8`). The first city of each list gets state `2` at `+0x19c`.
* **Phase 2, strike groups:** from the cities with state `2` it picks one at random and spawns `spawnEndgameStrikeGroups_(strength 100.0, -1.0, position, name, 1)` for each; every fleet gets type `6`, its
  target set to Khiva's position, and enters the profile fleet vector; their `moid+0xc` is set to `3`.
* **Phase 3, reinforcement search:** up to **100 tries** to find a city (`+0x2e8 > 1`, active, 2000 to 4000 units from Khiva, not already occupied by a hostile fleet) and spawn another strike group
  there with strength `200.0` (normal) or `300.0` (hard mode, `Profile.hardMode`). Fleets from this phase get ships `Tarantul` (66%) or `Tarantul ARM` (34%).
* **Phase 4, garrison ships:** for every city with garrison strength it spawns ships through `somethingSpawnShips` (divides the strength by `20.0` or `50.0` depending on the city kind) and copies up to 3 of
  the generated names into the city record.
* **Finale:** `BASRA`'s record is cleared; then, **"Start the nuclear war"** (logdot's comment): if `Profile.escalation == 0` it shows `THE_BEGINNING` / `NUCLEAR_WAR`, plays `dram_hit_01`, and sets
  `escalation = max(escalation, 1)`; finally **`Profile.endWar = true`**. This is what `GetPartPrice` (version-differences.md, stats record) checks, so after this function runs, part prices become 0.

* **Lead for the Khiva crash/loop bug: superseded.** The first write to each of the four quadrant lists is **unguarded**, in both versions; the 1.163 counterpart `FUN_140261a20` is located. Cause, patch recipe and confirmation: [khiva-crash.md](khiva-crash.md).

## Other differences between the 1.151 and 1.163 versions of the function [code]
The phase structure, the `100.0/200.0/300.0` strike strengths (`hardMode`), the `2000`-`4000` search ring, the `700` exclusion and the `Tarantul` split (66%) are unchanged. 1.163 adds `CopyEscadraName` calls with a state flag set through bit marks (`local_234 |= 1/2/4`, unused locals as far as seen). The Ghidra names `escalation`/`enigmaKey10` at offsets 660/744 come from the stale 1.151 `Profile` struct: at the shifted layout they line up with 1.151 `escalation`/`endWar`; the two names are not resolved.
