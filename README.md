# Highfleet 1.163 reverse-engineering notes (with 1.151 comparison)

Short, topic-based notes behind the Highfleet mods (Steam 1.163 with a 1.151 comparison, image base `0x140000000`).

Tags (one legend for all docs):

- **[game]** -- verified in play, in logs or on the real game files.

- **[code]** -- read from the decompilation.

- **[guide]** -- community guide, unverified here.
- **[guess]** -- inferred.
- **[tool]** -- Ghidra fuzzy-match result (a similarity score, not proof).
- **[not read]** -- known gap.
- **[file]** -- read from game files. 
- **[agent]** -- a DeepSeek agent's reading of the code (reports in `hf_ml/out/ds2-*`), NOT re-read by Claude. Treat as a lead. Claims Claude re-read in the bytes or decompile are plain **[code]**.

`docs/version-differences.md` adds **[V]** / **[C]** / **[?]** for offset confidence (defined there). Paths in the docs are relative to the workspace root (`$HF_DEV`, e.g. `~/Development_Highfleet`) and the game folder is `<game dir>`.

Layout: 
- `docs/` reference docs;
- `docs/findings/` one note per question (`findings/ai/` for the AI);
- `docs/rendering/` how the game draws and how its screens and GUI work (start at its README);
- `docs/mods/` one page per mod and the debug tools;
- `docs/runs/` dated reports (evidence, not reference);
- `docs/data/` tables;
- `ref/` third-party material;
- `STATUS.md` is the only file with perishable state (installed versions, open pull requests, open items).

## Start here
| Read | For |
|---|---|
| [STATUS.md](STATUS.md) | what is installed, released, open upstream and open (the only file with perishable state) |
| [docs/setup.md](docs/setup.md) | tools, modloader, building, pitfalls, safe-edit rules, comparing with the 1.151 program |
| [docs/porting-1151-1163.md](docs/porting-1151-1163.md) | **porting a mod between 1.151 and 1.163**: what changed, how to guard builds, step-by-step site porting, anchor addresses, what each of our mods would need |
| [docs/open-questions.md](docs/open-questions.md) | what is unknown or undecided, and the list of Ghidra fixes to raise with logdot |
| [docs/roadmap.md](docs/roadmap.md) | long-term mod wish list (bugs, QoL, AI, mod scope) and wanted modder tooling; not scheduled, do not act on it unasked |
| [docs/mods/README.md](docs/mods/README.md) | every mod with its status, repo and page, plus the debug and experiment tools |

## Reference (how the game is built)
| Read | For |
|---|---|
| [docs/formats.md](docs/formats.md) | `.seria`, libraries, ships, saves, language packs, textures/`.res`, levels |
| [docs/structures.md](docs/structures.md) | class codes, Body / stats / fleet / map-missile / Creature layouts, `m_category` bits, projectile logic ids |
| [docs/version-differences.md](docs/version-differences.md) | 1.151 vs 1.163: Body and Profile offset remaps, stats record, Ghidra struct status, strings added/removed |
| [docs/sound.md](docs/sound.md) | **playing a game sound from a mod**: the `playSFXSound_` call (argument table, Rust type), the volume-pointer pitfall (0.0 = silent), sound names, the stock radio, what `hf_ally` plays |
| [docs/engine-hge.md](docs/engine-hge.md) | the HGE engine under the game: interface table, resource loading, stock formats, mod seams |
| [docs/hooks.md](docs/hooks.md) | hooking techniques, who owns which patch site, candidate sites |
| [docs/content.md](docs/content.md) | dialogue, characters, events, textures (study + experiment plan) |

## Rendering and GUI
How the game draws, how its screens and GUI elements are built, and the probe evidence behind them. Start at the README. (`docs/rendering/`)

| Read | For |
|---|---|
| [docs/rendering/README.md](docs/rendering/README.md) | plain-language overview: how a frame is drawn, what a seam is, recipe to draw text and sprites, best seam per screen, how to test a seam |
| [docs/rendering/render-pipeline.md](docs/rendering/render-pipeline.md) | how the game draws: frame tasks, scene dispatcher, stock `hgeFont` text path, fonts, hook seam |
| [docs/rendering/editor-frame.md](docs/rendering/editor-frame.md) | where an in-game editor hint could hook: `_FrameFunc` task order, game-thread input site, text path; history of the drawing question, the answer is [render-pipeline.md](docs/rendering/render-pipeline.md) |
| [docs/rendering/fonts.md](docs/rendering/fonts.md) | every game font: files, metrics, ASCII-only charsets, what the editor uses, live look of the sampled ones, how a mod draws text |
| [docs/rendering/images-and-sprites.md](docs/rendering/images-and-sprites.md) | every image is an `Animation` in `Media/Tex/*.res`, resource getters, sprite object layout, `Render` / `RenderEx` (drawing confirmed in game, run 2) |
| [docs/rendering/gui-elements.md](docs/rendering/gui-elements.md) | making a GUI element the game's own way: the creation recipe (12-argument initializer), element list and fields, coordinates, hiding instead of freeing, the `ClickFunc` swallow trampoline |
| [docs/rendering/click-func.md](docs/rendering/click-func.md) | the GUI click handler `ClickFunc` (1.151 `0x1401261d0`, 1.163 `0x14012f120`): size, caller, what the probe logs, live-test recipe; also the 252-name element catalog and four decompiled branches (BUY_BUY, FUEL_BUY_SLIDER, MAPMODE_MISSION_*) |
| [docs/rendering/precombat-screen.md](docs/rendering/precombat-screen.md) | the pre-combat screen: the two builders (`FUN_1402d73a0` is the live one), card order = squad order, the native ammo selector layout, the per-ship ALLY buttons `hf_ally` builds on it, how they follow a card shuffle, the slot-1 PLAYER text label and the roller covers |
| [docs/rendering/seam-test-run-1.md](docs/rendering/seam-test-run-1.md) | seam test runs 1 and 2 (probe v2.2): labels after every flush call of the map, battle and menu renderers; which seams fire and which are clean; map seam M11 chosen (evidence for the README above) |
| [docs/rendering/ui-events-and-screens.md](docs/rendering/ui-events-and-screens.md) | probe v2.0 run: log-only hooks for clicks, text keys, sounds and level loads, gold, location and fleet watchers, which dispatcher flag is which screen |

## Findings
One self-contained note per question; each ends with unknowns or a live-test recipe. (`docs/findings/`)

### AI
| Read | For |
|---|---|
| [docs/findings/ai/ai-hf-ai-design.md](docs/findings/ai/ai-hf-ai-design.md) | why a DLL is the way to change the AI, the `hf_ai` design (log-only steering hook, `decide()`), the `ai_flares` missile-panic algorithm, the overshoot-dodge idea, hook-ownership clash |
| [docs/findings/ai/ai-flares.md](docs/findings/ai/ai-flares.md) | why AI ships never use flares (missing trigger, not missing parts) and a mod design |
| [docs/findings/ai/ai-tick-patch-sites.md](docs/findings/ai/ai-tick-patch-sites.md) | the tactical AI in 1.163: close-range cutoff, stand-off retreat, ammo choice, launch limits, byte-exact patch sites |
| [docs/findings/ai/ai-telemetry.md](docs/findings/ai/ai-telemetry.md) | battle telemetry in `hf_ally` (feature `telemetry`): the three CSVs, part list and part health, ship name `+0xa90`, aim signal `vc2/vc3`, flying-body array and per-frame birth/death log, first captures, missile overshoot test |
| [docs/findings/ai/ai-aircraft-launch.md](docs/findings/ai/ai-aircraft-launch.md) | why the strategic AI launches all aircraft at once, launch conditions, patch sites |
| [docs/findings/ship-profiles.md](docs/findings/ship-profiles.md) | how the game computes mass, TWR and gun reach, validated profiles of 20 designs for the AI self-knowledge data |
| [docs/findings/battle-ally.md](docs/findings/battle-ally.md) | the AI ally in battle (`hf_ally`, running in game): what makes a Creature AI-run, how the vanilla deploy spawns the ally, the retreat point and extraction (why a promoted ship could not retreat), the ORDER role table in `+0xd70` (1 unset, 2 bombing, 3 support), prize ships and trade convoys, ally flares, the AI's ammo flags, checklist, AI plan |

### Combat, ships and the map
| Read | For |
|---|---|
| [docs/findings/combat-missile-launch.md](docs/findings/combat-missile-launch.md) | how enemy ships (and the player) launch Zenith in combat: `FUN_14002ff60` at `0x140065edb`, detach probe, what is not the launch path, burst mod |
| [docs/findings/strategic-missile-target-assignment.md](docs/findings/strategic-missile-target-assignment.md) | which ship a map missile attacks once the battle is built: 1.151 `0x140241680` / 1.163 `0x140263700`, `_CONV` test, Path A (highest combat value first) and Path B (random), hook sites, offset shifts, a table of addresses that mean different functions in the two versions |
| [docs/findings/firing-and-shells.md](docs/findings/firing-and-shells.md) | `FireShell` dispatch, shell HP and lifetime, where projectile constants live |
| [docs/findings/guns-aim-reload-fire.md](docs/findings/guns-aim-reload-fire.md) | gun aim servo, reload (one round at a time), fire gates, AI burst cycle, spread, recoil |
| [docs/findings/blast-and-penetration.md](docs/findings/blast-and-penetration.md) | shell blast formula, armour shadows (360-bucket table), penetration chain, flare rule |
| [docs/findings/ship-bodies-fixtures-and-breakup.md](docs/findings/ship-bodies-fixtures-and-breakup.md) | which parts get Box2D fixtures, vertex transform, centre of mass, tear-off, hull break-up |
| [docs/findings/ship-serializer.md](docs/findings/ship-serializer.md) | writing a ship to text with the game's own `SerializeToFile` |
| [docs/findings/landing-legs.md](docs/findings/landing-legs.md) | landing gear: leg parts, fold/deploy state machine, joints, collision and damage rules |
| [docs/findings/cluster-bomblet-ttl.md](docs/findings/cluster-bomblet-ttl.md) | cluster/mine bomblet spawn function, its two call sites, the TTL patch site (partial) |
| [docs/findings/ammo-1151-vs-1163.md](docs/findings/ammo-1151-vs-1163.md) | the ammo table (built in code), the `Ammo` record, every value change between versions, live ammo-table dump |
| [docs/findings/gun-ammo-funding-and-refund.md](docs/findings/gun-ammo-funding-and-refund.md) | how gun reserves are funded from the profile in the pre-combat screen and refunded at battle end; why a base pool must not be refunded as a priced type and why pre-combat clicks must not be hooked; the `hf_ally` v0.13.5 fix |
| [docs/findings/box2d-physics-setup.md](docs/findings/box2d-physics-setup.md) | Box2D setup: gravity 9.82 (x0.05 scale), body/fixture definitions, mass = min(w,h) x density x polygon area (checked on MDL_ENGINE_01), damping 0.05, the ShouldCollide filter |
| [docs/findings/box2d-struct-layouts.md](docs/findings/box2d-struct-layouts.md) | b2Body/b2Fixture/b2Joint/weld/revolute/distance/b2World/b2Contact field offsets, the 6.0 weld mass scale, the tiny-density dynamic antenna links |
| [docs/findings/player-attitude-stabiliser.md](docs/findings/player-attitude-stabiliser.md) | who reads Stats+0x100 / creature +0x180c, +0x1684, +0x1688; the AI attitude-hold is not run for the player ship by code (one open point) |
| [docs/findings/ai/ai-steering-and-avoidance.md](docs/findings/ai/ai-steering-and-avoidance.md) | AI steering: obstacle scan and weights, velocity force law, attitude hold, bank clamp and smoothing |
| [docs/findings/battle-terrain.md](docs/findings/battle-terrain.md) | how the ground is generated (height polyline, 150-unit steps, hill factor), queried (`FUN_1402ee0c0`), and collided with; what `+0xb84` really is; what is still unmapped |
| [docs/findings/landscape-generator-spec.md](docs/findings/landscape-generator-spec.md) | exact recipe to regenerate the battle ground from (seed, size, L1, hill, zero): HGE and CRT random generators, Perlin tables and evaluation, polyline steps, layer 7; reference code `docs/data/landscape_gen.py` (reproduces the logged grounds) |
| [docs/findings/flares-and-missiles.md](docs/findings/flares-and-missiles.md) | the flare body (mask 0, 5 s, 360-600 u/s), Stats category 0x80 is trusses not flares (correction), missile ejection, what is still open (seeker law) |
| [docs/findings/hull-stabiliser-coupling.md](docs/findings/hull-stabiliser-coupling.md) | the stabiliser torque, verified against logs (spin jump = sum T * 0.05^5 * invI_com exactly), the inertia in T (I about origin, R per design), which parts are separate b2 bodies and their joints (swivel engines / guns: revolute + motor, legs: revolute + soft distance, statics: Frame fixtures), 10/10 iterations |
| [docs/findings/player-thrust-keys-and-engine-heat.md](docs/findings/player-thrust-keys-and-engine-heat.md) | Q/E/S keys to command angles (exact atan2 and wrap rules, +-pi tie), swivel servo law, Shift strength, spool, every gate that zeroes an engine's force, engine overheat lockout (500 / 3 s) and why the Kormoran barely spins |
| [docs/findings/box2d-function-map.md](docs/findings/box2d-function-map.md) | Names applied in Ghidra for the embedded Box2D 2.3 (world, tree, broadphase, contacts, narrowphase, joints), what was verified, unit scaling 0.05, flight-input helpers, helper-agent claims that were wrong |
| [docs/findings/box2d-world-settings-for-sim.md](docs/findings/box2d-world-settings-for-sim.md) | One-page checklist of the Box2D combat settings (dt 0.02 fixed, 10/10, gravity (0,+0.491) acting on hulls, damping 0.05, constants all stock 2.3, force/torque scalings, joint setups, no velocity clamps) against a pybox2d sim |
| [docs/findings/engine-heat-sim-validation.md](docs/findings/engine-heat-sim-validation.md) | what the simulator's engine heat model was checked against (dose, conduction, extinguisher, trip times), the open swivel-heating gap after an extinguisher use, and the simdiff tool |
| [docs/findings/simulator-tooling.md](docs/findings/simulator-tooling.md) | how the simulator rebuilds the flown ship from the .hftm dumps (dump + extra + joint rows, leg and antenna fixes), design variants and their engine banks, key timing, truss conduction scale, the simdiff tool and what is still open |
| [docs/findings/shell-detonation-paths.md](docs/findings/shell-detonation-paths.md) | what calls the blast routine: contact (0 <= +0x38c < I), flak gun cone, hp death; arming rule of plain shells (20/|v| s, then threshold 25 x mass), probe evidence |
| [docs/findings/creature-logic-id-map.md](docs/findings/creature-logic-id-map.md) | logic id to code block map of creatureLogic (plain shell 100, timed fuse 110, stabiliser 200, missiles 1/3/4/135), dispatch tables |
| [docs/findings/static-engine-force-path.md](docs/findings/static-engine-force-path.md) | how a static engine force is applied (angle, point, body), the Frame air-drag torque in Body_PreStepUpdate (hull-angle dependent), who else writes torque / angular velocity |
| [docs/findings/hull-stabiliser-engine-logic.md](docs/findings/hull-stabiliser-engine-logic.md) | the hull stabiliser: creatureLogic case 200, per-engine Body_AddTorque (PD on spin and wrapped angle, cap +-m_at); the +-pi flip; +0xbc4 spool ramp |
| [docs/findings/ship-removal-and-battle-result.md](docs/findings/ship-removal-and-battle-result.md) | when a ship is judged lost (ShipStatusCheck), RemoveLostAIShip, battle result codes -1 / 1 / 2 |
| [docs/findings/ai/ai-behaviour-states.md](docs/findings/ai/ai-behaviour-states.md) | tactical AI states (+0xbdc 0..7), kinds (+0xbd8), roles, target choice and scoring (20000/distance, 3 s re-roll) |
| [docs/findings/hull-rotation-behaviour.md](docs/findings/hull-rotation-behaviour.md) | why ships spin the way they do (one-page overview at the top): the per-engine stabiliser torque (damping on spin, pull to level, 0.6 s tail), worked numbers, why swivel-only and static-only designs are smooth and swivel + static designs lurch once per turn, what was ruled out, what is open |
| [docs/findings/contact-damage-and-fire.md](docs/findings/contact-damage-and-fire.md) | contact damage (0.8 x solver impulse, armour threshold, x0.6 player scaling, tear-off above 4e6) and the heat-based fire model (only fuel tanks and engines burn) |
| [docs/findings/simulator-research.md](docs/findings/simulator-research.md) | combat-simulator research in one page: Box2D physics, cmass as moving mass, engine force/servo and the corrected engine names, fuel paths, AI force status, damage/kill pointers, corrections to earlier claims, what is still unknown |
| [docs/findings/explosion-damage-1151-vs-1163.md](docs/findings/explosion-damage-1151-vs-1163.md) | why 1.163 missile hits reach deeper into a ship: Zenith warhead 200 to 300, armor hit x2 to x4, part cost flat 5 to maxHP/20; 180mm shells unchanged; run-time evidence from both versions |
| [docs/findings/elevation-rules-1151-vs-1163.md](docs/findings/elevation-rules-1151-vs-1163.md) | why 1.163 blocks gun arcs and the KAZ more than 1.151: candidate floor +1 in `World_RaycastBodies`, KAZ cone 1.2 vs pi/4, KAZ covered gate type 3/0.5 vs 5/0.15; patch ideas (not applied); floor offsets 0x978/0x980 |
| [docs/findings/sensors-and-crew.md](docs/findings/sensors-and-crew.md) | how sensors combine (max vs sum), crew capacity vs fuel capacity |
| [docs/findings/map-air-groups.md](docs/findings/map-air-groups.md) | map aircraft groups, intercept probabilities, which code starts which engagement |
| [docs/findings/plane-combat-modes-and-gunpods.md](docs/findings/plane-combat-modes-and-gunpods.md) | real-time plane modes (0/2/3/6), which mode fires bombs/rockets/gun, why FAB/NURS planes have no 37 mm in vanilla, the class-3 stock auto-draw leak, and the tactical-only `extra_gunpod` design |
| [docs/findings/end-game.md](docs/findings/end-game.md) | the scripted end game: phases, `endWar`, escalation; the Khiva crash (unguarded list writes) and its patch recipe |
| [docs/findings/level-seria-dispatcher.md](docs/findings/level-seria-dispatcher.md) | `SomethingWithLevelSerias`: the SCR_* scenario dispatcher in 1.151 and 1.163, label addresses, string refs (names only, body unread) |

### Crashes, input and the executable
| Read | For |
|---|---|
| [docs/findings/flare-crash-hunt.md](docs/findings/flare-crash-hunt.md) | the flare/proximity-fuse crash: fixed upstream by highfleet-qol (site and null pointer), plus the flare release path and flare body layout |
| [docs/findings/collect-dead-crash.md](docs/findings/collect-dead-crash.md) | stock fatal assertion "Collect_dead node with m_master" (one crash, cause open), the collector and the hf_ally v0.12.10 diagnostic |
| [docs/findings/mouse-sensitivity.md](docs/findings/mouse-sensitivity.md) | mouse sensitivity path; A220 slowdown not yet located (partial) |
| [docs/findings/source-file-names.md](docs/findings/source-file-names.md) | the 15 original source-file paths embedded in the exe (`HYBRID FLEET 2013EX`) and what they say about the code layout |

## Mods
Status, repo and page for every mod: [docs/mods/README.md](docs/mods/README.md).

| Read | For |
|---|---|
| [docs/mods/hf-ai.md](docs/mods/hf-ai.md) | `hf_ai`: the tactical AI layer, config, versions, measured results |
| [docs/mods/hf-ally.md](docs/mods/hf-ally.md) | `hf_ally`: AI allies from the reserve, pre-combat buttons, telemetry |
| [docs/mods/qol.md](docs/mods/qol.md) | the QoL fork: which features are upstream, which are local, the `enabled` rule |
| [docs/mods/elevation.md](docs/mods/elevation.md) | set the elevation (`m_floor`) of the held shipworks part; keys, config, mechanism |
| [docs/mods/speed.md](docs/mods/speed.md) | configurable map cruise speed: `vanilla` / `classic` / `custom` presets and the QoL port |
| [docs/mods/refuel.md](docs/mods/refuel.md) | multiplier for the station refuel rate (player and AI) |
| [docs/mods/multicharge.md](docs/mods/multicharge.md) | parts that launch several times before they are used up (charge level = part id) |
| [docs/mods/salvo.md](docs/mods/salvo.md) | map missile launch delay and grouping a salvo into one map missile |
| [docs/mods/voice.md](docs/mods/voice.md) | `hf_voice`: key-bound sounds from loose `.wav` files (no `.res` edit), the player package |
| [docs/mods/probe.md](docs/mods/probe.md) | `hf_probe`, the debug-only logging DLL: install, config, what it logs |

## Runs
Dated reports: evidence, not reference. (`docs/runs/`; probe and seam-test runs about the screens are in `docs/rendering/`)

| Read | For |
|---|---|
| [docs/runs/probe-run-1.md](docs/runs/probe-run-1.md) | runs 1-3 of the `hf_probe` debug DLL (v1.0 to v2.0): input and memory diff in every screen, pinned cursor, mode and state bytes, clicks, gold, location and fleet |
| [docs/runs/ally-probe-run-1.md](docs/runs/ally-probe-run-1.md) | `hf_ally` v0.3.1 probe: ally against nearest enemy over three campaign battles (speed, ammo spent, targets); the ally is not slower than the enemy |
| [docs/runs/ally-runs.md](docs/runs/ally-runs.md) | dated `hf_ally` run reports v0.1 to v0.4: spawn, strike run, mode 0, retreat key, auto-retreat, handover |
| [docs/runs/hf-ai-first-run.md](docs/runs/hf-ai-first-run.md) | first in-game run of hf_ai v0.3.0: what works (close retreat, panic flares), what does not show (strafe) |
| [docs/runs/ai-intrepid-benchmark.md](docs/runs/ai-intrepid-benchmark.md) | measured expert-pilot and enemy behaviour from 15 stock-INTREPID battles, 11 Lightning sessions and 7 Navarin campaign sessions, missile-dump collision rate, suggested numbers for the tactics |
| [docs/runs/ai-underside.md](docs/runs/ai-underside.md) | measured under/over-the-ship advantage (38 sessions): hit rate, lower-third damage, what enemies do, "deny the dive" proposal |
| [docs/runs/tester-test-plan.md](docs/runs/tester-test-plan.md) | the list of tests shipped in the tester pack README; which items still have no evidence in play |

## Data
Tables. (`docs/data/`)

| Read | For |
|---|---|
| [docs/data/ghidra-changes-2026-10-29.md](docs/data/ghidra-changes-2026-10-29.md) | unnamed-function sweep: 1,325 renames + 8 created functions with doc-style plate comments in four waves (166 single-agent; 221 + 575 + 372 from three rounds of five parallel agents; per-agent tables in `docs/data/ghidra-sweep-2026-10-29-agent1..5.md`, `...-b3-agent1..5.md`, `...-b4-agent1..5.md`). Includes the shader-layer class map (RTTI-derived), `!FrameFunc`, the Box2D joint-enum warning, and the remaining clusters with counts |
| [docs/data/ghidra-changes-2026-10-28.md](docs/data/ghidra-changes-2026-10-28.md) | ammo funding/refund round and plane combat paths (plate/rename log) |
| [docs/data/clickfunc-elements.tsv](docs/data/clickfunc-elements.tsv) | the `ClickFunc` element catalog as a table: group, first-test address, name, times seen, mod idea (companion to [click-func.md](docs/rendering/click-func.md)) |
| [docs/data/port-1151-1163-functions.tsv](docs/data/port-1151-1163-functions.tsv) | the 1.151 to 1.163 function names ported in Ghidra: new name, both addresses, evidence tier, old 1.163 name (includes the skipped `prop-skip` rows) |
| [docs/data/port-1151-1163-matches.json](docs/data/port-1151-1163-matches.json) | the 1.151 to 1.163 function address map used for the port (before the fuzzy tier) |
| [docs/data/port-1151-1163-signatures.tsv](docs/data/port-1151-1163-signatures.tsv) | the 345 function signatures ported (22 of them later reverted, see the reverts table; calling convention, return and parameter types as applied, and the type 1.151 had where a stale struct was replaced by `void *`: `intended_type`) |
| [docs/data/port-1151-1163-signatures-v17-fixes.tsv](docs/data/port-1151-1163-signatures-v17-fixes.tsv) | the 16 signature corrections of version 17 (types reverted to `void *`, return sizes) |
| [docs/data/port-1151-1163-thiscall.tsv](docs/data/port-1151-1163-thiscall.tsv) | the 16 `__thiscall` signatures ported (function, class, return, parameters) |
| [docs/data/port-1151-1163-callsite.tsv](docs/data/port-1151-1163-callsite.tsv) | the 9 function names ported by call position (tag `PORTED_1151_CALLSITE`) |
| [docs/data/port-1151-1163-signature-measure.tsv](docs/data/port-1151-1163-signature-measure.tsv) | per function: decompiler placeholder counts at Ghidra v15 (before the signature port), v18 and final |
| [docs/data/port-1151-1163-signature-reverts.tsv](docs/data/port-1151-1163-signature-reverts.tsv) | the 22 signatures made automatic again, with the prototype they had |
| [docs/data/port-1151-1163-writestring-fix.tsv](docs/data/port-1151-1163-writestring-fix.tsv) | the `WriteString` unused-parameter fix: placeholder counts of its 30 callers before and after the fix (old prototype: see `docs/setup.md`) |
| [docs/data/port-1151-1163-variables.tsv](docs/data/port-1151-1163-variables.tsv) | the 28 parameter and local-variable names ported (function, storage, old and new name) |
| [docs/data/port-1151-1163-labels.tsv](docs/data/port-1151-1163-labels.tsv) | the 40 data labels ported, with reference votes |
| [docs/data/port-1151-1163-labels-review.tsv](docs/data/port-1151-1163-labels-review.tsv) | data labels not ported: already named the same, conflicting, or no reference |
| [docs/data/gui-dump-precombat-ammo-2026-10-16.txt](docs/data/gui-dump-precombat-ammo-2026-10-16.txt) | `hf_ally` `gui_inspect` dump of the pre-combat screen with the native ammo selector (evidence for [precombat-screen.md](docs/rendering/precombat-screen.md)) |
| [docs/data/mail-trade-convoy-2026-10-16.txt](docs/data/mail-trade-convoy-2026-10-16.txt) | a HighFleet Knowledge Base answer on how trade convoys are spawned (`spawnTradeConvoy_`); an outside source, unverified here (context in [battle-ally.md](docs/findings/battle-ally.md)) |

## Third-party reference
Config.ini reference, summaries of community guides and prior art. (`ref/`)

| Read | For |
|---|---|
| [ref/config-ini.md](ref/config-ini.md) | `Config.ini` keys (unverified, from a community document) |
| [ref/community-guides.md](ref/community-guides.md) | summaries of community guides and prior art (the Steam guide PDF is kept locally, not committed) |
| [ref/total-conversion-hara-vera.md](ref/total-conversion-hara-vera.md) | study of the "Flight to Hara Vera" total conversion |

Mods run on [Highfleet-Modloader](https://github.com/logdot/Highfleet-Modloader). Public repos: [highfleet-elevation](https://github.com/mxtrnhf/highfleet-elevation), [highfleet-speed](https://github.com/mxtrnhf/highfleet-speed); the rest, and the open pull requests to logdot's `highfleet-qol`: [docs/mods/README.md](docs/mods/README.md), [STATUS.md](STATUS.md).
