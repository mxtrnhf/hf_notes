# Ship removal and battle result rules (1.163), ghidra-miner, 2026-10-21
Work-list item 7 ([data/ghidra-miner-worklist-2026-10-20.md](../data/ghidra-miner-worklist-2026-10-20.md)). Tags: [code] read in Ghidra this session, [prior] from earlier notes/comments, [open].

## When a ship counts as lost: `ShipStatusCheck` 0x14006ab70 (name in Ghidra; decompile read today) [code]
Run for every AI tick (`aiShipDriver`) and for the strategic fleet; skipped when the ship's state `+0xbdc == 6`. Variables: `bVar7` = side flag `+0xad4 < 0` (enemy side), `bVar8` = campaign/mode condition (`IS_IN_CAMPAIGN_` or `BOOL_147fc6fd2` with a profile link `+0xa70` whose `+0x168 != 0`, else neither `DAT_147fc6fd4` nor `DAT_147fc6fc8`). The checks apply when `bVar7 || bVar8`. The ship is flagged lost (`bVar9`) when:
1. battle TWR `+0x1604 == 0` (an engine bank sum `+0x1664`/`+0x1668` is 0), unless the design name is exactly `"Titan"`;
2. bank thrust `+0x1664 + +0x1668 < mass +0x15b8 * 9.82` (x0.25 under debug flag `DAT_147fc6f82`): shows `LOW_THRUST_MSG`; also skipped for `"Titan"`;
3. fuel `+0x1638 == 0` in a campaign / arcade battle;
4. power total `+0x1628 == 0`;
5. enemy side only: (state `+0x48 == 0` or combat rating `+0x15f8 <= 40` or an unset local) and `+0x16a0 / original part count < 0.65` -> `CRITICAL_MSG`;
6. enemy side only: no gun in the list `+0x1360` has part `+0x820 != 0`.
Messages `LOST_CTRL_MSG`, `NO_POWER_MSG`, `NO_FUEL_MSG`, `FUEL_MSG`, `POWER_MSG`, `DYNAMIC_MSG` are shown when the TWR, fuel or power fraction drops (thresholds 0.1 / 0.25).

## Removal: `RemoveLostAIShip` 0x14006bc10 [code]
Called from the end of `ShipStatusCheck` only **if the ship is AI-controlled (`+0xbd4 != 0`) and `bVar9`**. It stamps `+0x17c*8 = GameClock`, shows the player-ship hit effect if the lost ship is the player's (`FUN_140079790`), moves the ship's stored per-part counters (`+0x804`, cap 30) to its other parts, in arcade battles bumps the profile counter `enigmaKey12` when the ship was damaged within 15 s, then calls the creature's vtable `+0x48` (kill) and sets `+0x640 = -1`. **A player-controlled ship (`+0xbd4 == 0`) is never removed by this path; it only gets the messages.**

## How the battle ends: `battleManagerTick` 0x1402cc260 (end of the function, decompile read today) [code]
```
rebuild lists:  roster (own ships)  DAT_147fc7590..98   enemy ships  DAT_147fc73d8..e0
if (controlled ship missing or state 6/7) and roster non-empty: promote roster[0] (+0xd70 = 1), link it
result = DAT_147fc7004 = 0
if roster empty and wave timer DAT_147fc7020 == 0:
        result = enemies empty ? 2 : -1 ; battle over (returns 0)
elif enemies empty:                      # roster still has ships
        result = 1 ; battle over (returns 0)
else:   battle continues (returns 1)
```
* **-1 = all own ships gone while enemies remain (defeat); 1 = enemies gone while own ships remain (victory); 2 = both sides empty at once.** Reserve ships (`0x147fc73b0`) and the wave timer `0x147fc7020` (30 s between enemy waves) keep the battle alive: with an empty roster the end is only declared once the timer is 0 [prior: battle-ally.md].
* Retreat = every roster ship extracted alive (`0x14020ef30`), see [battle-ally.md](battle-ally.md).

## Open
* What puts a ship on / removes it from the roster and enemy vectors (the list-rebuild call `rep_1402a8540_..._free(&0x147fc75a8, &0x147fc73d8, &0x147fc7590)` resolves to an unrelated function in Ghidra at that address, so its criteria were not read); how a destroyed player ship leaves the roster (state 6/7 vs hull destroyed).
* Differences between campaign and arcade end screens (`RETRY_CASUALTIES_*`), the meaning of `+0x48`, and the `enigmaKey12` counter.
