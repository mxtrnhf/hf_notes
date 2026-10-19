# highfleet-salvo  (repo `old_standalone/hf_salvo`)

> Standalone, not in QoL, postponed; repo `old_standalone/hf_salvo` (local only).

Two independent options for strategic missiles on the map (`salvo.ini`):

* `map_launch_delay` (vanilla 300): the cooldown the game starts after each map launch is the float immediate of `mov [rdi+0x50c], 300.0f` (`0x1400ed598`+6); a 4-byte data patch lets a whole
  volley leave together (3 worked). Applies to AI fleets too. No hook on the launch routine (that belongs to multicharge).
* `group_missiles` (experimental): when a missile threatens a fleet, **sum the counts of the salvo into the first map missile** (same part id, same side, same target, within `group_radius`,
  at most `group_max`), so `Missile.seria` spawns them all; the emptied extras are killed (`vtbl+0x48`) on the next `Map.seria` load. Hook: level loader `0x14025afd0`.
  Pushing extra list entries instead does nothing [game]. Map-level interception stays per object (the merge happens only when the fight is built); own interceptors are never merged.
  Applies to enemy salvos against you too.
* `log_levels`: writes every level load and the engagement lists to the log (research aid).
* Status: 3-4 missile fights verified [game]; cooldown patch verified at install (log `launch cooldown: 300 -> 3`), play test pending after the split.

## How the game launches strategic missiles on the map [game]
Moved from the retired `systems.md` (2026-10-19).

The Triumph (AA; needs a fire-control radar like the R-9 Sprint `MDL_MISSILE_03`) is **combat only**; the A-100 is a **map-only** strategic missile.
* Panel `FUN_140273640`: **4 switches** (`MAPMODE_MISSILE_SW`), each bound to a distinct, not-yet-queued missile part of the selected type. `MAPMODE_MISSILE_FIRE` is the fire button. A strategic missile (A-100 =
  `MDL_NUKE_03_CONV`) is a single body with two mount slots.
* Queue filler `FUN_140214c40`: one **0x38-byte entry** per switched-on missile in the fleet's vector (fleet +0x538/+0x540/+0x548): `{SmartRef part, SmartRef target, float x,y at +0x30}`.
  A missile with stats +0x168 > 100000 triggers `NUCLEAR_ESCALATION_1` [code]: only while the `ESCALTION_WARNING` trigger is set (the game's own spelling) and no other block applies; that press then shows the dialogue, clears the trigger and queues **nothing**, and the next press queues normally. The target of an entry (global `DAT_143a13c68`) may be a fleet (`0x147`), a Missile or a MapCraft (mask tests) [code].
* Consumer `FUN_1400eced0(fleet)`, called from the fleet update `FUN_140111ff0` whenever **fleet +0x50c == 0**: takes the LAST entry (a dead or null part is popped and skipped first [code]), creates the map missile (`FUN_140334094(0x308)` +
  `FUN_1400e48a0`), copies the part id into it, kills the part (`vtbl+0x48`), pops the entry, recomputes ship totals, and sets **`fleet+0x50c = 300.0`** (immediate at `0x1400ed598`+6).
  The timer is counted down per frame (~`0x140115cc8`) and also blocks the AI decision `FUN_1400f00c0`: this is why a queued volley goes out one by one.
* AI side (1.163): `FUN_1400f00c0(fleet, targetInfo)` decides to fire (cooldown, range 100..9000, per-target salvo caps 1/2/8 at targetInfo+0x84) and calls **`FUN_1400fc760`** (Ghidra name `showMissileInShop??`; 1.151 twin `0x1400f70a0`, same name) [code]. This does **not** fill the player queue and does not go through `FUN_1400eced0`: for each missile part of the fleet it creates the map missile itself (`New(0x308)` + `FUN_1400e48a0`), names it `"VAMPIRE"`, sets count `+0x248 = 1`, copies speed/range/type from the part's stats, pushes it on the Profile Missile vector (`+0x228/+0x230`), kills the part (`vtbl+0x48`), and sets the fleet cooldown `fleet+0x50c` to a random float times a constant (`0x14035483c`). It is also called from `rep_1400e9a00_MakeGlobal_` (1.163 `0x1400ef1d7`). The `300.0f` that `map_launch_delay` patches (`0x1400ed598`+6, 1.163) is written by `FUN_1400eced0`, the queue consumer; this AI path writes its own cooldown instead [code]. **Open:** the line above says the patch "applies to AI fleets too"; by this reading it would not change AI launches made through `FUN_1400fc760`. Re-check in game (log the cooldown after an AI launch) before relying on either statement. Corrected 2026-10-19 (earlier text said "fills the queue via `FUN_1400fc760`"; found while checking an external knowledge base, see [../findings/strategic-missile-target-assignment.md](../findings/strategic-missile-target-assignment.md)). Not yet read: the value of the random range / constant, and whether `FUN_1400f00c0` can launch more than one missile per call.
