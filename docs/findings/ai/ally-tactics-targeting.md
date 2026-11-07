# Allied tactics targeting: own target vs player target (hf_ai v0.10.18, 2026-11-08)

Question: do allied AI ships use their own targets for `tactics.allies`, or do they inherit the player's target? In particular, do they react to enemy ships aiming at them and to enemies passing above/below?

Short answer: **no player-target inheritance was found.** Allies use their own `Creature+0xb00` target. Aim dodging scans hostile ships independently; dive avoidance only uses the ally's current target.

## Code path

- `ai/src/lib.rs` builds the tactics context from the acting creature:
  ```rust
  let info = rd(creature + OFF_TARGET).and_then(|node| target_info(node));
  ```
  `OFF_TARGET` is `Creature::target` + `Link::target`, i.e. `Creature+0xb00` (`ai/src/native_layout.rs`, compile-time assertion `CREATURE_TARGET == 0xb00`).
- `target_info()` resolves a target that points at a ship part to the owning ship. That is ownership resolution, not inheritance from the player.
- `ai/src/tactics.rs`, `decide()`:
  - rejects positive-side ships when `tactics.allies` is false;
  - requires AI-controlled, mode 1 (airborne combat), valid arena bounds and TWR clearance;
  - builds `target` only from the acting ship's own `Ctx.target` / `Ctx.target_creature`.
- `ai/src/tactics.rs`, `pick_hostile_aim()`:
  - scans `live_ships` for any ship with the opposite side sign;
  - uses the hostile shooter's own AI aim vector (`+0xbf8`) or the player aim vector when the shooter is player-controlled;
  - does **not** use the defender's target. An ally with no target can still dodge enemy aim.
- `ai/src/tactics.rs`, dive avoidance:
  - `dive_target` is `target` filtered to an airborne target;
  - `tactics_math::step` receives only that target position.
  - Therefore an unrelated enemy passing above/below does **not** trigger a dive unless it is the ally's current target.
- `ai/src/tactics.rs`, `early_fire_allowed()`:
  - rereads the acting ship's own `OFF_TARGET` and validates target identity; no player target is used.
- `ally/src/lib.rs`, `on_target_chosen()`:
  - runs after the native AI target choice for an ally;
  - may replace a prize-ship target with another enemy, or clear the target when only prizes remain;
  - writes the ally's own target link, not the player's.

## Behaviour table

| Behaviour | Uses ally's own target? | Reacts to any hostile? | Main gates |
|---|---|---|---|
| Aim dodge | No | Yes, closest hostile whose aim ray crosses the ally | `tactics.allies`, AI-controlled airborne mode 1, TWR cutoff, awareness window, `aim_require_fire`, `aim_range`/`aim_tolerance`, `aim_chance` |
| Dive avoidance | Yes | No, only the current target | target airborne, cone/range, `dive_dwell_s`, `dive_chance`, `dive_cooldown_s` |
| Early fire | Yes | No, permission applies to the current target | valid target identity, awareness window, range, chance, native firing checks |

## Live config at the time of the check

`Modloader/config/hf_ai.json`:

- `tactics.allies: true`
- `twr_cutoff: 2.0`
- `aim_range: 1500.0`, `aim_tolerance: 200.0`, `aim_chance: 0.75`, `aim_require_fire: true`
- `dive_chance: 0.5`, `dive_dwell_s: 0.1`, `dive_cooldown_s: 1.0`

## Why an ally may look passive

- Strategic/Shipworks TWR below `2.0` disables tactics entirely for that ship.
- Ship must be AI-controlled and in mode 1 (airborne combat).
- `aim_require_fire: true` means an enemy merely aiming is not enough; its guns must be firing.
- Aim detection is a ray check (`aim_range` along the aim ray plus cross-ray tolerance), not a circle around the ship.
- `aim_chance` and `dive_chance` can decline an opportunity.
- An active missile panic suppresses tactics.
- Dive avoidance only sees the ally's current target; native target selection may have chosen a different enemy.

## Possible future change

If allies should dodge **any** hostile passing above/below, dive avoidance would need a hostile-ship scan similar to `pick_hostile_aim`, rather than using only `ctx.target`. That is a behavioural change, not a bug fix: the current design deliberately relies on native target selection for dive and early fire.

No code change was made for this note.
