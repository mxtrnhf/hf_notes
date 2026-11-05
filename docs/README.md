# Detailed reference catalog

Short, topic-based notes behind the Highfleet mods (Steam 1.163 with a 1.151 comparison, image base `0x140000000`).

[Home](../README.md) · [Findings by topic](findings/README.md) · [Ghidra history](ghidra/README.md) · [Data](data/README.md)

This catalog preserves the detailed descriptions from the original repository index. For a complete topic inventory, use the folder indexes linked above.

## Evidence tags

- **[game]** -- verified in play, in logs or on the real game files.

- **[code]** -- read from the decompilation.

- **[guide]** -- community guide, unverified here.
- **[guess]** -- inferred.
- **[tool]** -- Ghidra fuzzy-match result (a similarity score, not proof).
- **[not read]** -- known gap.
- **[file]** -- read from game files.
- **[agent]** -- a DeepSeek agent's reading of the code (raw reports are kept outside this repo), NOT re-read by Claude. Treat as a lead. Claims Claude re-read in the bytes or decompile are plain **[code]**.

`docs/version-differences.md` adds **[V]** / **[C]** / **[?]** for offset confidence (defined there). Paths in the docs are relative to the notes repo; the game folder is `<game dir>`, and local-only working data is marked as such.

Layout:
- `docs/` core reference docs and this catalog;
- `docs/findings/` one note per question, grouped by game system (start at its README);
- `docs/rendering/` how the game draws and how its screens and GUI work (start at its README);
- `docs/mods/` one page per mod and the debug tools;
- `docs/runs/` dated reports (evidence, not reference);
- `docs/ghidra/YYYY-MM-DD/` dated change logs, sweeps and audit evidence;
- `docs/data/` reusable tables, captures and reference code, grouped by purpose;
- `docs/plans/` research plans;
- `ref/` third-party material;
- `STATUS.md` is the only file with perishable state (installed versions, open pull requests, open items).

## Start here
| Read | For |
|---|---|
| [STATUS.md](../STATUS.md) | what is installed, released, open upstream and open (the only file with perishable state) |
| [docs/setup.md](setup.md) | tools, modloader, building, pitfalls, safe-edit rules, comparing with the 1.151 program |
| [docs/porting-1151-1163.md](porting-1151-1163.md) | **porting a mod between 1.151 and 1.163**: what changed, how to guard builds, step-by-step site porting, anchor addresses, what each of our mods would need |
| [docs/open-questions.md](open-questions.md) | what is unknown or undecided, and the list of Ghidra fixes to raise with logdot |
| [docs/roadmap.md](roadmap.md) | long-term mod wish list (bugs, QoL, AI, mod scope) and wanted modder tooling; not scheduled, do not act on it unasked |
| [docs/mishaps.md](mishaps.md) | dated log of things that went wrong: what happened, why, and what was learned |
| [docs/mods/README.md](mods/README.md) | every mod with its status, repo and page, plus the debug and experiment tools |

## Reference (how the game is built)
| Read | For |
|---|---|
| [docs/formats.md](formats.md) | `.seria`, libraries, ships, saves, language packs, textures/`.res`, levels |
| [docs/structures.md](structures.md) | class codes, Body / stats / fleet / map-missile / Creature layouts, `m_category` bits, projectile logic ids |
| [docs/version-differences.md](version-differences.md) | 1.151 vs 1.163: Body and Profile offset remaps, stats record, Ghidra struct status, strings added/removed |
| [docs/sound.md](sound.md) | **playing a game sound from a mod**: the `playSFXSound_` call (argument table, Rust type), the volume-pointer pitfall (0.0 = silent), sound names, the stock radio, what `hf_ally` plays |
| [docs/engine-hge.md](engine-hge.md) | the HGE engine under the game: interface table, resource loading, stock formats, mod seams |
| [docs/hooks.md](hooks.md) | hooking techniques, who owns which patch site, candidate sites |
| [docs/content.md](content.md) | dialogue, characters, events, textures (study + experiment plan) |

## Rendering and GUI
How the game draws, how its screens and GUI elements are built, and the probe evidence behind them. Start at the README. (`docs/rendering/`)

| Read | For |
|---|---|
| [docs/rendering/README.md](rendering/README.md) | plain-language overview: how a frame is drawn, what a seam is, recipe to draw text and sprites, best seam per screen, how to test a seam |
| [docs/rendering/render-pipeline.md](rendering/render-pipeline.md) | how the game draws: frame tasks, scene dispatcher, stock `hgeFont` text path, fonts, hook seam |
| [docs/rendering/editor-frame.md](rendering/editor-frame.md) | where an in-game editor hint could hook: `_FrameFunc` task order, game-thread input site, text path; history of the drawing question, the answer is [render-pipeline.md](rendering/render-pipeline.md) |
| [docs/rendering/fonts.md](rendering/fonts.md) | every game font: files, metrics, ASCII-only charsets, what the editor uses, live look of the sampled ones, how a mod draws text |
| [docs/rendering/images-and-sprites.md](rendering/images-and-sprites.md) | every image is an `Animation` in `Media/Tex/*.res`, resource getters, sprite object layout, `Render` / `RenderEx` (drawing confirmed in game, run 2) |
| [docs/rendering/gui-elements.md](rendering/gui-elements.md) | making a GUI element the game's own way: the creation recipe (12-argument initializer), element list and fields, coordinates, hiding instead of freeing, the `ClickFunc` swallow trampoline |
| [docs/rendering/click-func.md](rendering/click-func.md) | the GUI click handler `ClickFunc` (1.151 `0x1401261d0`, 1.163 `0x14012f120`): size, caller, what the probe logs, live-test recipe; also the 252-name element catalog and four decompiled branches (BUY_BUY, FUEL_BUY_SLIDER, MAPMODE_MISSION_*) |
| [docs/rendering/precombat-screen.md](rendering/precombat-screen.md) | the pre-combat screen: the two builders (`FUN_1402d73a0` is the live one), card order = squad order, the native ammo selector layout, the per-ship ALLY buttons `hf_ally` builds on it, how they follow a card shuffle, the slot-1 PLAYER text label and the roller covers |
| [docs/rendering/seam-test-run-1.md](rendering/seam-test-run-1.md) | seam test runs 1 and 2 (probe v2.2): labels after every flush call of the map, battle and menu renderers; which seams fire and which are clean; map seam M11 chosen (evidence for the README above) |
| [docs/rendering/ui-events-and-screens.md](rendering/ui-events-and-screens.md) | probe v2.0 run: log-only hooks for clicks, text keys, sounds and level loads, gold, location and fleet watchers, which dispatcher flag is which screen |

## Findings
One self-contained note per question; each ends with unknowns or a live-test recipe. The [topic index](findings/README.md) is the complete inventory, including notes not described in the tables below.

### AI
| Read | For |
|---|---|
| [docs/findings/ai/ai-hf-ai-design.md](findings/ai/ai-hf-ai-design.md) | why a DLL is the way to change the AI, the `hf_ai` design (log-only steering hook, `decide()`), the `ai_flares` missile-panic algorithm, the overshoot-dodge idea, hook-ownership clash |
| [docs/findings/ai/ai-flares.md](findings/ai/ai-flares.md) | why AI ships never use flares (missing trigger, not missing parts) and a mod design |
| [docs/findings/strategy/mercenary-ships.md](findings/strategy/mercenary-ships.md) | where the mercenary/reinforcement ships offered for money come from: hard-coded tier pools in `addReinforceingShips` 0x14021b8c0, tier chosen by the `ASK_REINFORCE` dialog, not by the city; also why `m_npcs` is Tarkhans, not ships |
| [docs/findings/ai/ai-tick-patch-sites.md](findings/ai/ai-tick-patch-sites.md) | the tactical AI in 1.163: close-range cutoff, stand-off retreat, ammo choice, launch limits, byte-exact patch sites |
| [docs/findings/ai/ai-telemetry.md](findings/ai/ai-telemetry.md) | battle telemetry in `hf_ally` (local development build; feature `telemetry`; not in public packs since v0.14.3, still in older `highfleet-allies` commits/releases): the CSVs, part list and part health, ship name `+0xa90`, aim signal `vc2/vc3`, flying-body array and per-frame birth/death log, first captures, missile overshoot test |
| [docs/findings/ai/ai-aircraft-launch.md](findings/ai/ai-aircraft-launch.md) | why the strategic AI launches all aircraft at once, launch conditions, patch sites |
| [docs/findings/ships/ship-profiles.md](findings/ships/ship-profiles.md) | how the game computes mass, TWR and gun reach, validated profiles of 20 designs for the AI self-knowledge data |
| [docs/findings/ships/battle-ally.md](findings/ships/battle-ally.md) | the AI ally in battle (`hf_ally`, running in game): what makes a Creature AI-run, how the vanilla deploy spawns the ally, the retreat point and extraction (why a promoted ship could not retreat), the ORDER role table in `+0xd70` (1 unset, 2 bombing, 3 support), prize ships and trade convoys, ally flares, the AI's ammo flags, checklist, AI plan |
| [docs/findings/ai/ai-obstacle-hook-sites.md](findings/ai/ai-obstacle-hook-sites.md) | byte-exact AI obstacle-scan and steering hook sites for `hf_ai`: stolen-byte counts, scan call, list layout, weight loop |
| [docs/findings/ai/tactical-carrier-launch-groups.md](findings/ai/tactical-carrier-launch-groups.md) | tactical carrier launch groups (hf_ai v0.10.3, still present in 0.10.15): stock flow, group-size and clearance keys, partial launches, build/install record |
| [docs/findings/ai/hf-ai-hot-config-reload.md](findings/ai/hf-ai-hot-config-reload.md) | source study of hot-reloading `hf_ai.json`/`ally.json` without restarting; current state, blockers, design and conflicts |

### Combat, ships and the map
| Read | For |
|---|---|
| [docs/findings/combat/combat-missile-launch.md](findings/combat/combat-missile-launch.md) | how enemy ships (and the player) launch Zenith in combat: `FUN_14002ff60` at `0x140065edb`, detach probe, what is not the launch path, burst mod |
| [docs/findings/strategy/strategic-missile-target-assignment.md](findings/strategy/strategic-missile-target-assignment.md) | which ship a map missile attacks once the battle is built: 1.151 `0x140241680` / 1.163 `0x140263700`, `_CONV` test, Path A (highest combat value first) and Path B (random), hook sites, offset shifts, a table of addresses that mean different functions in the two versions |
| [docs/findings/combat/firing-and-shells.md](findings/combat/firing-and-shells.md) | `FireShell` dispatch, shell HP and lifetime, where projectile constants live |
| [docs/findings/combat/guns-aim-reload-fire.md](findings/combat/guns-aim-reload-fire.md) | gun aim servo, reload (one round at a time), fire gates, AI burst cycle, spread, recoil |
| [docs/findings/combat/blast-and-penetration.md](findings/combat/blast-and-penetration.md) | shell blast formula, armour shadows (360-bucket table), penetration chain, flare rule |
| [docs/findings/physics/ship-bodies-fixtures-and-breakup.md](findings/physics/ship-bodies-fixtures-and-breakup.md) | which parts get Box2D fixtures, vertex transform, centre of mass, tear-off, hull break-up |
| [docs/findings/ships/ship-serializer.md](findings/ships/ship-serializer.md) | writing a ship to text with the game's own `SerializeToFile` |
| [docs/findings/physics/landing-legs.md](findings/physics/landing-legs.md) | landing gear: leg parts, fold/deploy state machine, joints, collision and damage rules |
| [docs/findings/combat/cluster-bomblet-ttl.md](findings/combat/cluster-bomblet-ttl.md) | cluster/mine bomblet spawn function, its two call sites, the TTL patch site (partial) |
| [docs/findings/combat/ammo-1151-vs-1163.md](findings/combat/ammo-1151-vs-1163.md) | the ammo table (built in code), the `Ammo` record, every value change between versions, live ammo-table dump |
| [docs/findings/combat/gun-ammo-funding-and-refund.md](findings/combat/gun-ammo-funding-and-refund.md) | how gun reserves are funded from the profile in the pre-combat screen and refunded at battle end; why a base pool must not be refunded as a priced type and why pre-combat clicks must not be hooked; the `hf_ally` v0.13.5 fix |
| [docs/findings/physics/box2d-physics-setup.md](findings/physics/box2d-physics-setup.md) | Box2D setup: gravity 9.82 (x0.05 scale), body/fixture definitions, mass = min(w,h) x density x polygon area (checked on MDL_ENGINE_01), damping 0.05, the ShouldCollide filter |
| [docs/findings/physics/box2d-struct-layouts.md](findings/physics/box2d-struct-layouts.md) | b2Body/b2Fixture/b2Joint/weld/revolute/distance/b2World/b2Contact field offsets, the 6.0 weld mass scale, the tiny-density dynamic antenna links |
| [docs/findings/physics/player-attitude-stabiliser.md](findings/physics/player-attitude-stabiliser.md) | who reads Stats+0x100 / creature +0x180c, +0x1684, +0x1688; the AI attitude-hold is not run for the player ship by code (one open point) |
| [docs/findings/ai/ai-steering-and-avoidance.md](findings/ai/ai-steering-and-avoidance.md) | AI steering: obstacle scan and weights, velocity force law, attitude hold, bank clamp and smoothing |
| [docs/findings/strategy/battle-terrain.md](findings/strategy/battle-terrain.md) | how the ground is generated (height polyline, 150-unit steps, hill factor), queried (`FUN_1402ee0c0`), and collided with; what `+0xb84` really is; what is still unmapped |
| [docs/findings/strategy/landscape-generator-spec.md](findings/strategy/landscape-generator-spec.md) | exact recipe to regenerate the battle ground from (seed, size, L1, hill, zero): HGE and CRT random generators, Perlin tables and evaluation, polyline steps, layer 7; reference code `docs/data/terrain/landscape_gen.py` (reproduces the logged grounds) |
| [docs/findings/combat/flares-and-missiles.md](findings/combat/flares-and-missiles.md) | the flare body (mask 0, 5 s, 360-600 u/s), Stats category 0x80 is trusses not flares (correction), missile ejection, and the seeker/proximity law |
| [docs/findings/physics/hull-stabiliser-coupling.md](findings/physics/hull-stabiliser-coupling.md) | the stabiliser torque, verified against logs (spin jump = sum T * 0.05^5 * invI_com exactly), the inertia in T (I about origin, R per design), which parts are separate b2 bodies and their joints (swivel engines / guns: revolute + motor, legs: revolute + soft distance, statics: Frame fixtures), 10/10 iterations |
| [docs/findings/physics/player-thrust-keys-and-engine-heat.md](findings/physics/player-thrust-keys-and-engine-heat.md) | Q/E/S keys to command angles (exact atan2 and wrap rules, +-pi tie), swivel servo law, Shift strength, spool, every gate that zeroes an engine's force, engine overheat lockout (500 / 3 s) and why the Kormoran barely spins |
| [docs/findings/physics/box2d-function-map.md](findings/physics/box2d-function-map.md) | Names applied in Ghidra for the embedded Box2D 2.3 (world, tree, broadphase, contacts, narrowphase, joints), what was verified, unit scaling 0.05, flight-input helpers, helper-agent claims that were wrong |
| [docs/findings/simulator/box2d-world-settings-for-sim.md](findings/simulator/box2d-world-settings-for-sim.md) | One-page checklist of the Box2D combat settings (dt 0.02 fixed, 10/10, gravity (0,+0.491) acting on hulls, damping 0.05, constants all stock 2.3, force/torque scalings, joint setups, no velocity clamps) against a pybox2d sim |
| [docs/findings/simulator/engine-heat-sim-validation.md](findings/simulator/engine-heat-sim-validation.md) | what the simulator's engine heat model was checked against (dose, conduction, extinguisher, trip times), the open swivel-heating gap after an extinguisher use, and the simdiff tool |
| [docs/findings/simulator/simulator-tooling.md](findings/simulator/simulator-tooling.md) | how the simulator rebuilds the flown ship from the .hftm dumps (dump + extra + joint rows, leg and antenna fixes), design variants and their engine banks, key timing, truss conduction scale, the simdiff tool and what is still open |
| [docs/findings/combat/shell-detonation-paths.md](findings/combat/shell-detonation-paths.md) | what calls the blast routine: contact (0 <= +0x38c < I), flak gun cone, hp death; arming rule of plain shells (20/|v| s, then threshold 25 x mass), probe evidence |
| [docs/findings/engine/creature-logic-id-map.md](findings/engine/creature-logic-id-map.md) | logic id to code block map of creatureLogic (plain shell 100, timed fuse 110, stabiliser 200, missiles 1/3/4/135), dispatch tables |
| [docs/findings/physics/static-engine-force-path.md](findings/physics/static-engine-force-path.md) | how a static engine force is applied (angle, point, body), the Frame air-drag torque in Body_PreStepUpdate (hull-angle dependent), who else writes torque / angular velocity |
| [docs/findings/physics/hull-stabiliser-engine-logic.md](findings/physics/hull-stabiliser-engine-logic.md) | the hull stabiliser: creatureLogic case 200, per-engine Body_AddTorque (PD on spin and wrapped angle, cap +-m_at); the +-pi flip; +0xbc4 spool ramp |
| [docs/findings/ships/ship-removal-and-battle-result.md](findings/ships/ship-removal-and-battle-result.md) | when a ship is judged lost (ShipStatusCheck), RemoveLostAIShip, battle result codes -1 / 1 / 2 |
| [docs/findings/ai/ai-behaviour-states.md](findings/ai/ai-behaviour-states.md) | tactical AI states (+0xbdc 0..7), kinds (+0xbd8), roles, target choice and scoring (20000/distance, 3 s re-roll) |
| [docs/findings/physics/hull-rotation-behaviour.md](findings/physics/hull-rotation-behaviour.md) | why ships spin the way they do (one-page overview at the top): the per-engine stabiliser torque (damping on spin, pull to level, 0.6 s tail), worked numbers, why swivel-only and static-only designs are smooth and swivel + static designs lurch once per turn, what was ruled out, what is open |
| [docs/findings/combat/contact-damage-and-fire.md](findings/combat/contact-damage-and-fire.md) | contact damage (0.8 x solver impulse, armour threshold, x0.6 player scaling, tear-off above 4e6) and the heat-based fire model (only fuel tanks and engines burn) |
| [docs/findings/simulator/simulator-research.md](findings/simulator/simulator-research.md) | combat-simulator research in one page: Box2D physics, cmass as moving mass, engine force/servo and the corrected engine names, fuel paths, AI force status, damage/kill pointers, corrections to earlier claims, what is still unknown |
| [docs/findings/combat/explosion-damage-1151-vs-1163.md](findings/combat/explosion-damage-1151-vs-1163.md) | why 1.163 missile hits reach deeper into a ship: Zenith warhead 200 to 300, armor hit x2 to x4, part cost flat 5 to maxHP/20; 180mm shells unchanged; run-time evidence from both versions |
| [docs/findings/combat/elevation-rules-1151-vs-1163.md](findings/combat/elevation-rules-1151-vs-1163.md) | why 1.163 blocks gun arcs and the KAZ more than 1.151: candidate floor +1 in `World_RaycastBodies`, KAZ cone 1.2 vs pi/4, KAZ covered gate type 3/0.5 vs 5/0.15; patch ideas (not applied); floor offsets 0x978/0x980 |
| [docs/findings/ships/sensors-and-crew.md](findings/ships/sensors-and-crew.md) | how sensors combine (max vs sum), crew capacity vs fuel capacity |
| [docs/findings/aircraft/map-air-groups.md](findings/aircraft/map-air-groups.md) | map aircraft groups, intercept probabilities, which code starts which engagement |
| [docs/findings/aircraft/plane-combat-modes-and-gunpods.md](findings/aircraft/plane-combat-modes-and-gunpods.md) | real-time plane modes (0/2/3/6), which mode fires bombs/rockets/gun, why FAB/NURS planes have no 37 mm in vanilla, the class-3 stock auto-draw leak, and the tactical-only `extra_gunpod` design |
| [docs/findings/strategy/end-game.md](findings/strategy/end-game.md) | the scripted end game: phases, `endWar`, escalation; the Khiva crash (unguarded list writes) and its patch recipe |
| [docs/findings/strategy/level-seria-dispatcher.md](findings/strategy/level-seria-dispatcher.md) | `SomethingWithLevelSerias`: the SCR_* scenario dispatcher in 1.151 and 1.163, label addresses, string refs (names only, body unread) |
| [docs/findings/physics/antitilt-stabiliser-formula-report.md](findings/physics/antitilt-stabiliser-formula-report.md) | archived derived report: closed-form stabiliser formula, per-tick algebra, parameter sensitivity; current references are the hull-stabiliser pages |
| [docs/findings/simulator/combat-hit-log-formats.md](findings/simulator/combat-hit-log-formats.md) | `hf_ally_hit_<id>.csv` row formats (sim.49/50): common body fields and per-kind field lists; produced by telemetry builds |
| [docs/findings/combat/logic-120-delayed-airbrake-warhead.md](findings/combat/logic-120-delayed-airbrake-warhead.md) | creatureLogic id 120: two-stage air-braked warhead spawned by `FireShell` case 70, not plane code |
| [docs/findings/aircraft/plane-flight-speed-vs-maneuverability.md](findings/aircraft/plane-flight-speed-vs-maneuverability.md) | plane speed vs turn rate: maneuverability hardcoded in `Aircraft_ApplyFlightForces`; hook design |

### Crashes, input and the executable
| Read | For |
|---|---|
| [docs/findings/crashes/flare-crash-hunt.md](findings/crashes/flare-crash-hunt.md) | the flare/proximity-fuse crash: fixed upstream by highfleet-qol (site and null pointer), plus the flare release path and flare body layout |
| [docs/findings/crashes/collect-dead-crash.md](findings/crashes/collect-dead-crash.md) | stock fatal assertion "Collect_dead node with m_master" (one crash, cause open), the collector and the hf_ally v0.12.10 diagnostic |
| [docs/findings/engine/mouse-sensitivity.md](findings/engine/mouse-sensitivity.md) | mouse sensitivity path; A220 slowdown not yet located (partial) |
| [docs/findings/engine/source-file-names.md](findings/engine/source-file-names.md) | the 15 original source-file paths embedded in the exe (`HYBRID FLEET 2013EX`) and what they say about the code layout |

## Mods
Status, repo and page for every mod: [docs/mods/README.md](mods/README.md).

| Read | For |
|---|---|
| [docs/mods/hf-ai.md](mods/hf-ai.md) | `hf_ai`: the tactical AI layer, config, versions, measured results |
| [docs/mods/hf-ai-tuning-guide.md](mods/hf-ai-tuning-guide.md) | plain-language `hf_ai` tuning guide (archived at v0.9.0; the current guide is in the public repo) |
| [docs/mods/hf-ally.md](mods/hf-ally.md) | `hf_ally`: AI allies from the reserve, pre-combat buttons, ship panels and switching; telemetry is a local development build |
| [docs/mods/qol.md](mods/qol.md) | the QoL fork: which features are upstream, which are local, the `enabled` rule |
| [docs/mods/elevation.md](mods/elevation.md) | set the elevation (`m_floor`) of the held shipworks part; keys, config, mechanism |
| [docs/mods/speed.md](mods/speed.md) | configurable map cruise speed: `vanilla` / `classic` / `custom` presets and the QoL port |
| [docs/mods/refuel.md](mods/refuel.md) | multiplier for the station refuel rate (player and AI) |
| [docs/mods/multicharge.md](mods/multicharge.md) | parts that launch several times before they are used up (charge level = part id) |
| [docs/mods/salvo.md](mods/salvo.md) | map missile launch delay and grouping a salvo into one map missile |
| [docs/mods/voice.md](mods/voice.md) | `hf_voice`: key-bound sounds from loose `.wav` files (no `.res` edit), the player package |
| [docs/mods/probe.md](mods/probe.md) | `hf_probe`, the debug-only logging DLL: install, config, what it logs |

## Runs
Dated reports: evidence, not reference. (`docs/runs/`; probe and seam-test runs about the screens are in `docs/rendering/`)

| Read | For |
|---|---|
| [docs/runs/probe-run-1.md](runs/probe-run-1.md) | runs 1-3 of the `hf_probe` debug DLL (v1.0 to v2.0): input and memory diff in every screen, pinned cursor, mode and state bytes, clicks, gold, location and fleet |
| [docs/runs/ally-probe-run-1.md](runs/ally-probe-run-1.md) | `hf_ally` v0.3.1 probe: ally against nearest enemy over three campaign battles (speed, ammo spent, targets); the ally is not slower than the enemy |
| [docs/runs/ally-runs.md](runs/ally-runs.md) | dated `hf_ally` run reports v0.1 to v0.4: spawn, strike run, mode 0, retreat key, auto-retreat, handover |
| [docs/runs/hf-ai-first-run.md](runs/hf-ai-first-run.md) | first in-game run of hf_ai v0.3.0: what works (close retreat, panic flares), what does not show (strafe) |
| [docs/runs/ai-intrepid-benchmark.md](runs/ai-intrepid-benchmark.md) | measured expert-pilot and enemy behaviour from 15 stock-INTREPID battles, 11 Lightning sessions and 7 Navarin campaign sessions, missile-dump collision rate, suggested numbers for the tactics |
| [docs/runs/ai-underside.md](runs/ai-underside.md) | measured under/over-the-ship advantage (38 sessions): hit rate, lower-third damage, what enemies do, "deny the dive" proposal |
| [docs/runs/tester-test-plan.md](runs/tester-test-plan.md) | the list of tests shipped in the tester pack README; which items still have no evidence in play |
| [docs/runs/sim-fidelity-audit-2026-10-22.md](runs/sim-fidelity-audit-2026-10-22.md) | dated simulator fidelity audit against nine logged battles: error budget, flagged windows, ruled-out causes, tool fixes |
| [docs/runs/sim-enemy-ai-and-combat-validation-2026-10-23.md](runs/sim-enemy-ai-and-combat-validation-2026-10-23.md) | dated simulator-session validation: AI command pipeline, obstacle scan, shells, contacts and blasts |

## Data and Ghidra evidence
Reusable tables are grouped under [data](data/README.md). Dated change/sweep reports and audit tables are grouped under [Ghidra history](ghidra/README.md); change logs are the entry point, and per-agent reports are supporting evidence.

| Read | For |
|---|---|
| [docs/ghidra/2026-10-30/ghidra-changes-2026-10-30.md](ghidra/2026-10-30/ghidra-changes-2026-10-30.md) | post-sweep phases 0–2: classification of all 928 unnamed functions, the `__CxxFrameHandler4` funclet walk (20 closed), and five family-naming agents (+137 named → 4,639 / 85.40%). Includes the `ConstantBuffer<…>` RTTI correction, the vector/list/RB-tree stride conventions, the P2e field blockers, and the runaway-`EhWalk` incident |
| [docs/ghidra/2026-10-29/ghidra-changes-2026-10-29.md](ghidra/2026-10-29/ghidra-changes-2026-10-29.md) | unnamed-function sweep: ~2,988 renames + 524 created functions with doc-style plate comments in ten waves (per-agent tables in `docs/ghidra/2026-10-29/ghidra-sweep-2026-10-29-*agent*.md`). Includes the shader-layer class map (RTTI-derived), full `/EH` funclet ownership from the unwind tables (926 funclets → 347 owners), the `rep_*`-labels-are-unreliable correction, the CRT C-initialiser table, the `.rdata`/HGE/Body slot creation pass, and the remaining clusters with addresses |
| [docs/ghidra/2026-10-28/ghidra-changes-2026-10-28.md](ghidra/2026-10-28/ghidra-changes-2026-10-28.md) | ammo funding/refund round and plane combat paths (plate/rename log) |
| [docs/data/rendering/clickfunc-elements.tsv](data/rendering/clickfunc-elements.tsv) | the `ClickFunc` element catalog as a table: group, first-test address, name, times seen, mod idea (companion to [click-func.md](rendering/click-func.md)) |
| [docs/data/porting-1151-1163/port-1151-1163-functions.tsv](data/porting-1151-1163/port-1151-1163-functions.tsv) | the 1.151 to 1.163 function names ported in Ghidra: new name, both addresses, evidence tier, old 1.163 name (includes the skipped `prop-skip` rows) |
| [docs/data/porting-1151-1163/port-1151-1163-matches.json](data/porting-1151-1163/port-1151-1163-matches.json) | the 1.151 to 1.163 function address map used for the port (before the fuzzy tier) |
| [docs/data/porting-1151-1163/port-1151-1163-signatures.tsv](data/porting-1151-1163/port-1151-1163-signatures.tsv) | the 345 function signatures ported (22 of them later reverted, see the reverts table; calling convention, return and parameter types as applied, and the type 1.151 had where a stale struct was replaced by `void *`: `intended_type`) |
| [docs/data/porting-1151-1163/port-1151-1163-signatures-v17-fixes.tsv](data/porting-1151-1163/port-1151-1163-signatures-v17-fixes.tsv) | the 16 signature corrections of version 17 (types reverted to `void *`, return sizes) |
| [docs/data/porting-1151-1163/port-1151-1163-thiscall.tsv](data/porting-1151-1163/port-1151-1163-thiscall.tsv) | the 16 `__thiscall` signatures ported (function, class, return, parameters) |
| [docs/data/porting-1151-1163/port-1151-1163-callsite.tsv](data/porting-1151-1163/port-1151-1163-callsite.tsv) | the 9 function names ported by call position (tag `PORTED_1151_CALLSITE`) |
| [docs/data/porting-1151-1163/port-1151-1163-signature-measure.tsv](data/porting-1151-1163/port-1151-1163-signature-measure.tsv) | per function: decompiler placeholder counts at Ghidra v15 (before the signature port), v18 and final |
| [docs/data/porting-1151-1163/port-1151-1163-signature-reverts.tsv](data/porting-1151-1163/port-1151-1163-signature-reverts.tsv) | the 22 signatures made automatic again, with the prototype they had |
| [docs/data/porting-1151-1163/port-1151-1163-writestring-fix.tsv](data/porting-1151-1163/port-1151-1163-writestring-fix.tsv) | the `WriteString` unused-parameter fix: placeholder counts of its 30 callers before and after the fix (old prototype: see `docs/setup.md`) |
| [docs/data/porting-1151-1163/port-1151-1163-variables.tsv](data/porting-1151-1163/port-1151-1163-variables.tsv) | the 28 parameter and local-variable names ported (function, storage, old and new name) |
| [docs/data/porting-1151-1163/port-1151-1163-labels.tsv](data/porting-1151-1163/port-1151-1163-labels.tsv) | the 40 data labels ported, with reference votes |
| [docs/data/porting-1151-1163/port-1151-1163-labels-review.tsv](data/porting-1151-1163/port-1151-1163-labels-review.tsv) | data labels not ported: already named the same, conflicting, or no reference |
| [docs/data/rendering/gui-dump-precombat-ammo-2026-10-16.txt](data/rendering/gui-dump-precombat-ammo-2026-10-16.txt) | `hf_ally` `gui_inspect` dump of the pre-combat screen with the native ammo selector (evidence for [precombat-screen.md](rendering/precombat-screen.md)) |
| [ref/mail-trade-convoy-2026-10-16.txt](../ref/mail-trade-convoy-2026-10-16.txt) | a HighFleet Knowledge Base answer on how trade convoys are spawned (`spawnTradeConvoy_`); an outside source, unverified here (context in [battle-ally.md](findings/ships/battle-ally.md)) |
| [docs/ghidra/2026-10-27/ghidra-changes-2026-10-27.md](ghidra/2026-10-27/ghidra-changes-2026-10-27.md) | hot-reload study renames: `Config.ini` read/write, default key bindings, exit, time-freeze/exit globals (historical change log) |
| [docs/ghidra/2026-10-26/ghidra-changes-2026-10-26.md](ghidra/2026-10-26/ghidra-changes-2026-10-26.md) | 2026-10-26 agent round: battle ship panels, bomblet call sites/TTL, two crash sites, end-game gate, ClickFunc review, target cursor/aim (historical change log) |
| [docs/ghidra/2026-10-21/ghidra-changes-2026-10-21.md](ghidra/2026-10-21/ghidra-changes-2026-10-21.md) | earliest change log: Box2D 2.3 and Creature naming pass (historical) |
| [docs/ghidra/2026-10-30/ghidra-sweep-2026-10-30-p1a.md](ghidra/2026-10-30/ghidra-sweep-2026-10-30-p1a.md) | Phase 0–2 per-agent reports (`p1a`/`p1b` funclets, `p2a`–`p2e` family naming, `parent` incident/hardening); `p2e` §3 is the structures-blocker list (dated evidence) |
| [docs/ghidra/2026-10-29/ghidra-sweep-2026-10-29-agent1.md](ghidra/2026-10-29/ghidra-sweep-2026-10-29-agent1.md) | 75 per-agent sweep reports (first wave and batches 3–10): scope, counts, per-address evidence and remaining clusters (dated evidence) |
| [docs/ghidra/2026-10-29/funclet-ownership-2026-10-29.tsv](ghidra/2026-10-29/funclet-ownership-2026-10-29.tsv) | `/EH` funclet owner map: 934 rows; funclet, owner, member offset, family, evidence, status (20 closed, 3 closed in Phase 1b, 17 open) |
| [docs/ghidra/2026-10-29/rep-audit-2026-10-29.md](ghidra/2026-10-29/rep-audit-2026-10-29.md) | how the consolidated `rep_*` audit was built/rebuilt (q1→q4, de-duplication, counts); format and provenance |
| [docs/ghidra/2026-10-29/rep-audit-2026-10-29.tsv](ghidra/2026-10-29/rep-audit-2026-10-29.tsv) | consolidated `rep_*` audit: 1,496 unique addresses, 685 renamed / 811 stale label, one row each |
| [docs/ghidra/2026-10-29/rep-audit-2026-10-29-q1.tsv](ghidra/2026-10-29/rep-audit-2026-10-29-q1.tsv) | the four raw per-agent audit inputs (q1–q4; q2 has no header); kept for provenance and superseded by the consolidated TSV |
| [docs/ghidra/2026-10-30/unnamed-classification-2026-10-30.tsv](ghidra/2026-10-30/unnamed-classification-2026-10-30.tsv) | Phase 0 classification of all 928 unnamed functions: region, callers/callees, strings, stride, family, verdict, note |
| [docs/ghidra/2026-10-30/unnamed-classification-2026-10-30.md](ghidra/2026-10-30/unnamed-classification-2026-10-30.md) | prose report for the same Phase 0 classification: method, family rules, counts and open rows |
| [docs/ghidra/2026-10-29/unnamed-2026-10-29.tsv](ghidra/2026-10-29/unnamed-2026-10-29.tsv) | archived pre-sweep snapshot: address, old label, body size; superseded by the 2026-10-30 classification |
| [docs/data/terrain/landscape_gen.py](data/terrain/landscape_gen.py) | reference Python rebuild of `generateCityLandscape` (main polyline and layer 7); used by `landscape-generator-spec.md` |
| [docs/ghidra/2026-10-20/ghidra-miner-worklist-2026-10-20.md](ghidra/2026-10-20/ghidra-miner-worklist-2026-10-20.md) | dated eight-item work list with 2026-10-21 statuses (archived, mostly completed) |

## Third-party reference
Config.ini reference, summaries of community guides and prior art. (`ref/`)

| Read | For |
|---|---|
| [ref/config-ini.md](../ref/config-ini.md) | `Config.ini` keys (unverified, from a community document) |
| [ref/community-guides.md](../ref/community-guides.md) | summaries of community guides and prior art (the Steam guide PDF is kept locally, not committed) |
| [ref/total-conversion-hara-vera.md](../ref/total-conversion-hara-vera.md) | study of the "Flight to Hara Vera" total conversion |
| [ref/hot-reload-ds4-reports/README.md](../ref/hot-reload-ds4-reports/README.md) | index and caveats for the five raw 2026-10-27 agent reports behind the hot-reload study (unverified except where cited) |

Mods run on [Highfleet-Modloader](https://github.com/logdot/Highfleet-Modloader). Public repos: [highfleet-allies](https://github.com/mxtrnhf/highfleet-allies) (`hf_ai`, `hf_ally` and the bundled QoL build), [highfleet-elevation](https://github.com/mxtrnhf/highfleet-elevation), [highfleet-speed](https://github.com/mxtrnhf/highfleet-speed); the rest, and the open pull requests to logdot's `highfleet-qol`: [docs/mods/README.md](mods/README.md), [STATUS.md](../STATUS.md).
