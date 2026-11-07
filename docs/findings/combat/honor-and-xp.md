# Battle honor and XP

Steam 1.163. `Creature + 0x1a24` (f32) is the honor/XP earned in the current battle. `Creature + 0x1a28`
is the persistent `m_xp` property (`Creature_RegisterProperties` 0x1400744b0, registered at 0x1400774af).
`+0x1a24` is not a registered property; it sits 4 bytes before `m_xp`.

## Award during battle [code]

`battleManagerTick` 0x1402cc260 sums the enemy ships' `m_tele_hp` (`+0x168c`, property name at
0x1403557f8) and computes the decrease since the previous tick. With the player creature from
`Profile_GetFirstPlayerCreature` it adds

```
fVar10 / max(player+0x15fc, 8.0)
```

to `player+0x1a24` at 0x1402cc4f7 (`ADDSS XMM1, [RAX+0x1a24]`) / 0x1402cc4ff
(`MOVSS [RAX+0x1a24], XMM1`). `+0x15fc` is set from the integer `+0x15f8` (`m_tele_combatvalue`) at
spawn/deploy. `afterBattleStars` 0x14029e7e6 reads `+0x1a24` for the battle star/honor display and its
green/yellow thresholds.

## Return to the map [code]

`SCR_COMBAT_ReturnToMap` 0x1402ce060 iterates the player's fleet list
(`[0x143a158e0] -> [+8] -> [+0x100]`). For each creature it adds `+0x1a24` to `+0x1a28`, adds
`floor(+0x1a24 / 500.0)` to the promotion/star counter at `0x143a11948`, and zeroes `+0x1a24`
(0x1402ce682..0x1402ce6b4). The loop covers every ship in the player's fleet, so a value left on an
ally is applied to that ally's `m_xp` after the battle.

## hf_ally v0.14.27

`ally_honor_share` (default 0.5) adds `earned * share` to every live deployed ally's `+0x1a24` at the
player's store site (0x1402cc4ff), before the native store is replayed. The player's award is left
unchanged. Not yet validated in play.
