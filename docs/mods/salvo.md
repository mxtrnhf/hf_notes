# highfleet-salvo  (repo `hf_salvo`)

Two independent options for strategic missiles on the map (`salvo.ini`):

* `map_launch_delay` (vanilla 300): the cooldown the game starts after each map launch is the float immediate of `mov [rdi+0x50c], 300.0f` (`0x1400ed598`+6); a 4-byte data patch lets a whole
  volley leave together (3 worked). Applies to AI fleets too. No hook on the launch routine (that belongs to multicharge).
* `group_missiles` (experimental): when a missile threatens a fleet, **sum the counts of the salvo into the first map missile** (same part id, same side, same target, within `group_radius`,
  at most `group_max`), so `Missile.seria` spawns them all; the emptied extras are killed (`vtbl+0x48`) on the next `Map.seria` load. Hook: level loader `0x14025afd0`.
  Pushing extra list entries instead does nothing [game]. Map-level interception stays per object (the merge happens only when the fight is built); own interceptors are never merged.
  Applies to enemy salvos against you too.
* `log_levels`: writes every level load and the engagement lists to the log (research aid).
* Status: 3-4 missile fights verified [game]; cooldown patch verified at install (log `launch cooldown: 300 -> 3`), play test pending after the split.
