# Tuning hf_ai: a plain-language guide (v0.9.0, archived)

> **Archived.** This page describes `hf_ai` v0.9.0 and is kept for history. The current guide (v0.10.13) is maintained in the public `mxtrnhf/highfleet-allies` repo (`docs/hf-ai-tuning-guide.md`), with the complete key list in `docs/hf-ai-config-reference.md`.
>
> What changed after v0.9.0: `twr_cutoff` replaced the per-tactic acceleration gates (0.10.4); `tactics.apply_to_allies` was renamed `tactics.allies` (0.10.5); strafe/band positioning was removed (0.10.6); curtain sheltering was retired (0.10.11); aim dodging became universal (enemies dodge player and ally aim, allies dodge enemy aim); early fire moved from fire-byte writes to a detour of the native group-0 range gate (0.10.12); dive/aim/panic boosts now dash (0.10.13). The public preset has 49 leaf settings. Telemetry keeps being developed locally, but it is not in public builds since v0.14.3; older `highfleet-allies` commits/releases still contain it.

Written 2026-10-24 for the person who tunes the AI, not for the person who reads the code. Every number below is a key in `Modloader/config/hf_ai.json`; the code defaults are in `highfleet-allies/ai/src/tactics_math.rs` (`TacticsParams::default`) and `flares_config.rs`. Where I only know something from reading the code and not from playing, it says so.

## 1. Is "state machine" the right word?

Yes, with two corrections.

* **Each AI ship has its own small state machine.** At any moment it is in exactly one state (`stock`, `far`, `band`, `close`, `dive`, `dive_skip`, `aim`, `panic`; the names are the `state` column of `hf_ai_steer_*.csv`). It moves between states on conditions (target in the dive cone for long enough, an aim window opens, a missile locks on) and on timers (dwell, cooldown, duration).
* **It is not the game's AI.** The game's own AI runs every tick and computes a *waypoint* (where to fly next). hf_ai sits on that one point: it reads the waypoint the game wanted and either leaves it (`stock`) or replaces it. It never touches guns, targets or missiles, except the optional early fire. So "the state machine" is a steering override on top of vanilla, not a replacement brain.
* **There are really two machines.** (a) The *steering* machine above (file `tactics_math.rs`, `tactics.rs`). (b) The *flare curtain* machine (`curtain_math.rs`, `ai_flares.rs`): wait, drop, cooldown, driven by missile launches. They share the ship and the panic, but have separate settings (`tactics` block vs `ai_flares` block).

## 2. What happens every tick

1. **Gates** (cheap checks first). hf_ai stays out (`stock`) unless: the ship is AI-flown (never the ship you fly), it is airborne (mode 1), it has a living target that is not itself, the arena bounds are readable, and the ship is on a side that is allowed (enemy always; your allies only with `tactics.allies`, renamed from `apply_to_allies` in v0.10.5).
2. **Thrust gate.** The ship's acceleration (thrust / mass, in m/s^2; Lightning ~128, Intrepid ~56, heavies like Gryphon ~22) must reach the top-level `twr_cutoff` (default 2.0 strategic TWR; the old `dive_min_accel` / `min_accel` keys were retired in v0.10.4). Heavy ships below the cutoff keep stock behaviour. If a big ship "never does anything", this is why.
3. **Priority order** (first match wins): **panic** > **aim** > **dive** > **strafe (far / band / close)** > stock.
4. The winning state produces a direction. It is mixed with the game's own direction as `stock_direction + weight * tactic_direction` and re-normalised, so a large weight means "mostly my direction", weight 0 means stock. Ground, arena edges and "never steer down when low" limits are applied after.
5. Some states ask for an engine boost (like holding Shift). In v0.9.0 the boost was applied by the `ai_flares` engine hook; since v0.10.11 `dive_boost` / `aim_boost` work independently of `ai_flares.enabled`, and since v0.10.13 values above 1.0 also dash along the dodge direction.

## 3. The states and what each knob does

### 3.1 Panic (the `ai_flares` block): incoming missile
Triggers when a missile that has locked on to the ship (or, with `stray_missiles`, a loose one whose straight-line path passes close) comes within `trigger_range` (400). Each check (about 10 per second) rolls `reaction_probability` (0.6): a failed roll means no reaction yet, so lower values make the AI slower and sloppier.
* It drops flares for `burst_seconds` (1.5 s, about 10 flares per launcher), then waits `min_interval_seconds` before the next panic.
* `evade` true: it also steers sideways (perpendicular to the missile's line of approach) for `evasion_seconds`, `evasion_strength` 0..1 = how much of its course is taken over. Extended by 1 s each time a locked missile is still inside the range.
* With `panic_evasion_probability` (rolled once per panic) it instead commits to one escape direction at `panic_boost` x thrust for `panic_evasion_seconds` (extended 2.5 s at a time). It prefers the higher sidestep and never dives toward the ground when low.
* `barrel_roll_probability`: the "panic spin" (engines on one side up, other side down). Spectacular, rarely useful; keep near 0 to 0.02.
* `stray_missile_*`: radius / ETA / range for loose missiles. Raise the radius for a more nervous AI.

*Tuning feel:* difficulty goes up with `reaction_probability`, down with `min_interval_seconds` and up with `trigger_range`. The measured fact behind the defaults: enemy missiles hit only 2 to 5 percent of the time, so do not make panic perfect or missiles become useless.

### 3.2 Flare curtain (preventive flares)
When the **other camp** launches a missile, an AI ship rolls once whether to start dropping flares at random intervals *before* any lock. For enemy ships the trigger is your missile; **for allies (v0.9.0) it is an enemy missile aimed at you or at an ally.** Allies need `ai_flares.allies` true.
* `launch_flares_probability` (release: 0.6) for ships near the target; `launch_flares_target_probability` (1.0) for the ship the missile is aimed at. `launch_flares_targeted_only` true: only the targeted ship and ships within `launch_flares_neighbor_range` (600) join; false: every ship rolls.
* **Timing.** Flares live exactly 5 s. The first drop is timed from the missile's ETA (distance / `launch_flares_missile_speed` 230) minus `launch_flares_eta_lead` (4 s), clamped to `launch_flares_delay_min` (1) .. `launch_flares_eta_max_wait` (8). If the cloud is dropped too early it is gone when the missile arrives (this was the main v0.7.0 defect: 48 percent of drops were wasted). Keep the lead near 4.
* **Budget.** `launch_flares_max_drops` (6) per curtain, `launch_flares_interval_min/max` (0.5..1.0) between drops, `launch_flares_min_rack` (0.5): the ship stops dropping when the racks are below that share, so some flares stay for a real panic. `launch_flares_cooldown` (6) between curtains.
* **Movement.** While the curtain runs the ship moves away from the missile (`launch_flares_evade` 0.9, `launch_flares_boost` 2.0, within `launch_flares_evade_range` 400 in current builds). A ship with no flare launcher evades the missile directly: curtain sheltering (`launch_flares_shelter`) was retired in v0.10.11.

*Tuning feel:* to make missiles more dangerous, lower the probabilities or raise `launch_flares_eta_lead` away from 4 (mis-timed flares). To make the AI feel smart, raise `launch_flares_target_probability`.

### 3.3 Dive ("deny the dive")
If the target hangs within `dive_cone_deg` (45) of straight below ("under") or above ("over") the ship, closer than `dive_range` (600), for the dwell time, the ship rolls once per time the target enters the cone. On success it sidesteps horizontally for `dive_min_s..dive_max_s` (1.5..3), then pauses `dive_cooldown_s` (2). On a failed roll it is `dive_skip` and stays stock until the target leaves the cone.
* Why it exists: a target straight below you is the one that can hit your keel. Sidestepping and pulling to its altitude (`dive_level_weight` 0.7, full strength from 150 u of height difference) takes that shot away.
* Under vs over have separate odds: `dive_under_chance` (1.0) and `dive_under_dwell_s` (0.5) for a target below; `dive_chance` (0.8) and `dive_dwell_s` (1.0) for one above. `dive_under` / `dive_over` switch either off.
* `dive_wrongfoot_speed` (40 u/s): if the target is moving sideways faster than this, the ship dodges the *other* way, so you must reverse your momentum to follow. 0 means a random side. A near arena wall always wins over the choice.
* Strength: `dive_weight` (8) and `dive_boost` (2.5, needs ai_flares on).

*Tuning feel:* "too passive / still gets shot from below": `dive_under_chance` is already 1.0, so lower `dive_under_dwell_s`, raise `dive_weight` / `dive_boost`, widen `dive_cone_deg`. "Looks like it is dancing": lengthen `dive_cooldown_s`, lower the chances.

### 3.4 Aim awareness (enemies only so far)
Every `aim_gap_min_s..aim_gap_max_s` (2.5..3.5 s) an *awareness window* of `aim_window_s` (1.5 s) opens for all ships at once. During it, enemies that target **you** look at the line your guns point along. A ship whose position is within `aim_tolerance` (200 u) of that ray, closer than `aim_range` (1800 u), slips off the line sideways (`aim_weight` 12, `aim_boost` 2.5).
* `aim_require_fire` true: only while you are actually pressing fire (either gun group). This was added because 24 percent of on-line time you were not shooting.
* **Early fire:** `aim_fire_probability` (release 0.5): once per window a ship that is on the line rolls this chance and opens fire with its main guns for `aim_fire_s` (1 s) if you are within `aim_fire_range` (1.6) x its gun reach. Bypasses the stock range, angle and friendly-fire tests, so allies near the line of fire can be hit. Set 0 to turn it off.
* **Allies get aim awareness too since v0.10.11.** Each ship checks all hostile shooters (player and AI); only the player's own ship is never steered. Early fire since v0.10.12 uses the native group-0 range gate and keeps the native alignment/friendly-fire checks, unlike the v0.9.0 fire-byte path described above.

*Tuning feel:* "too hard to hit": raise `aim_gap_*` (longer pauses between windows) or lower `aim_weight`/`aim_boost`; narrow `aim_tolerance`. The effect is small by design: the measured displacement was only about 17 u/s before the weights were raised.

### 3.5 Strafe (far / band / close): removed in v0.10.6
Strafe and band positioning were removed. The keys (`strafe_enabled`, `blend_weight`, `k_center`, `band_min`/`band_max`, `half_width`, `outrange_extra`, `strafe_min_s`/`max_s`, `retreat_tangent`) are ignored; the stock AI positions the ship.

## 4. Ally differences (v0.9.0)

| Feature | Allies |
|---|---|
| Panic and flares, stray missiles | yes (`ai_flares.allies` true) |
| Flare curtain | yes, triggered by **enemy** launches at the player's side |
| Dive | yes (`tactics.allies` true; old name `apply_to_allies`), against the ally’s own target |
| Strafe | only if strafe is on |
| Aim awareness / early fire | no |
| The ship you fly | never touched |

Unconfirmed in play: whether allies really dodge as intended. The ally curtain and dive are new and were checked only by unit tests (80 pass), not in a battle. Look for `CURTAIN_START` lines whose ship pointer is an ally in `hf_ai_panic_*.log`.

## 5. How to tune without guessing

1. **Change one thing at a time**, keep a `.bak` of `hf_ai.json`, and change `enabled` (master) or one block's `enabled` to A/B. A fight against the same enemy design (say Intrepid) is the comparison unit.
2. **Turn logging on for the test only:** `logging.log_panic` true (panic and curtain events with timestamps). The old `log_steering` / `log_scan` CSV hooks belonged to the telemetry build and are gone from public builds; telemetry is still developed locally and older `highfleet-allies` commits/releases still contain it.
3. **Look at the replay**, not only the CSV: `build_viz.py` builds an HTML replay from the telemetry (the local `visualizer/` folder).
4. **Measure, then judge.** Useful numbers: share of enemy missiles that hit; share of curtain drops still in the air when the missile arrives (target: most); how often each `state` appears; time under your keel before the ship moves (dive); damage taken per minute. Do not judge from one fight: dice are rolled per ship.
5. **Safe order for a "harder" AI:** raise `reaction_probability`, then the dive weights, then the aim window frequency, last the early fire. For an "easier" one reverse it. Early fire is the one that makes the AI visibly dangerous, so move it in steps of 0.1.
6. **Pitfalls.** (a) Since v0.10.11 boosts work independently of `ai_flares.enabled`. (b) Qol's own `ai_flares` must be false while hf_ai's is true: both patch the same sites. (c) A ship below `twr_cutoff` never does anything, so heavies feel "stock". (d) Settings are read at game start (no hot reload; restart the game after editing). (e) Wrong key names are silently ignored (every key is optional), so check the `hf_ai: tactics ON (...)` log line shows your numbers.

## 6. Release defaults (current: pack v0.14.15, hf_ai 0.10.11-0.10.13)

`enabled` true; `twr_cutoff` 2.0; `ai_flares`: enabled, allies, evade, `panic_evasion_probability` 0.1 (installed config 0.4), `launch_flares_probability` 0.6, `log_panic` false, `launch_flares_evade_range` 400, everything else at the code defaults; `tactics`: enabled, allies, dive and aim enabled, `dive_dwell_s` 0.5, `dive_cooldown_s` 2.0, `aim_chance` 0.75, `aim_fire_probability` 0.5; `ai_missile_dump_chance` 0.4. The v0.9.0 keys `apply_to_allies`, `strafe_enabled`, `dive_min_accel`, `min_accel` and `launch_flares_shelter` no longer exist.

## 7. Recipes: "I see X, so I change Y"

All keys live in `Modloader/config/hf_ai.json`. Keep a `.bak`, change one line, restart the game, fight the same enemy again. Unlisted keys keep the defaults in sections 3.1 to 3.4.

| What you see in battle | What to change |
|---|---|
| Too many flares around the targeted ship; neighbours dump for nothing | `ai_flares.launch_flares_neighbor_range` to `0`: only the ship the missile is aimed at joins the curtain. Lower `launch_flares_probability` (0.6) to thin it out further. |
| Enemies dump flares every time I (or my allies) fire anything | They react to any missile launched by your side. Lower `launch_flares_probability`, or set `launch_flares_targeted_only` true (it is the default) so only the target reacts. |
| Flares are gone before the missile arrives | `launch_flares_eta_lead` is the head start in seconds (4). Flares last 5 s, so keep it near 4. |
| My allies dump flares too often | `ai_flares.allies` false turns allies' flares off completely. Otherwise lower `launch_flares_probability` (it applies to everyone). |
| Ships with no flare launchers just sit there when a Zenith comes | They evade/retreat from the missile directly (curtain sheltering was retired in v0.10.11). Make them braver or more nervous with `launch_flares_evade` (0.9), `launch_flares_boost` (2.0) and `launch_flares_evade_range` (400). |
| The AI is too good at dodging missiles | Lower `reaction_probability` (0.6) and `panic_evasion_probability` (0.3); raise `min_interval_seconds`. |
| The AI is too easy to hit with missiles | The opposite: raise `reaction_probability`, `trigger_range` (400) and `stray_missile_*` radius. |
| Ships keep shooting at me from below | Section 3.3: lower `dive_under_dwell_s`, raise `dive_weight` / `dive_boost`. |
| Enemies hit me too early or from far away | `aim_fire_probability` to `0` turns off early fire. |
| Heavy ships never dodge | Not a bug: below the top-level `twr_cutoff` (2.0) they keep stock behaviour. Lowering it makes slow ships twitch. |

## 8. Why flares start at "wrong" times (what the code does)

* **Missile locked on a ship** (panic, section 3.1): flares start only when the missile is closer than `trigger_range` (400 units) and the reaction roll passed. This is the "late" flare burst.
* **Missile launched by the other camp** (curtain, section 3.2): flares start before any lock, a few seconds before the missile's estimated arrival. This is the "early" one, and it is the reason a ship can dump flares when nothing is yet aimed at *it*: it is the target or stands within `launch_flares_neighbor_range` of the target. The trigger is the launch, not the danger to that particular ship.
* **Allies** run the same logic mirrored: they dump on an **enemy** launch aimed at you or at an ally.
* **K-13 (carrier planes' air-to-air missile):** checked in the 2026-10-25 test logs (6 K-13 launches with hf_ai loaded): no launch was detected and no curtain started, so the K-13 does not set off flare dumps. Not checked: enemy planes firing K-13 at your allies.
* **Shells:** nothing in hf_ai dodges shells. Only the dive and aim tactics (3.3, 3.4) affect where ships fly relative to your guns.
* **Zeniths and ships without flares:** they use the panic evasion and the curtain's shelter / run-away. How good that is has not been measured separately; enemy missiles hit only 2 to 5 percent overall.

## 9. A one-battle test routine

1. Set `"log_panic": true` inside `ai_flares`.
2. Fight, then open the newest `Modloader/logs/hf_ai_panic_*.log`. `CURTAIN_START` is a preventive dump (the line says which launch triggered it), `START` is a panic, `CURTAIN_DROP` is each flare drop.
3. Count: how many `CURTAIN_START` lines happened without you or an ally launching anything? If zero, nothing is "wrong", you are seeing the design. If not zero, send the log.
4. Change one value from section 7 and repeat.
