# Highfleet 1.163 reverse-engineering notes (with 1.151 comparison)

Short, topic-based notes behind the Highfleet mods (Steam 1.163 with a 1.151 comparison, image base `0x140000000`).
Tags (one legend for all docs): **[game]** verified in play, in logs or on the real game files · **[code]** read from the decompilation · **[guide]** community guide, unverified here · **[guess]** inferred · **[tool]** Ghidra fuzzy-match result (a similarity score, not proof) · **[not read]** known gap · **[file]** read from game files. `docs/version-differences.md` adds **[V]** / **[C]** / **[?]** for offset confidence (defined there). Paths in the docs are relative to the workspace root (`$HF_DEV`, e.g. `~/Development_Highfleet`) and the game folder is `<game dir>`.

Layout: `docs/` reference docs; `docs/findings/` one note per question; `docs/rendering/` how the game draws (start at its README); `docs/runs/` dated probe and seam-test reports (evidence, not reference); `docs/data/` tables; `STATUS.md` perishable state.

## Start here
| Read | For |
|---|---|
| [docs/install.md](docs/install.md) | **installing the mods on a clean game**: order, per-mod steps, test settings, pass/fail log lines, troubleshooting |
| [docs/setup.md](docs/setup.md) | tools, modloader, building, pitfalls, safe-edit rules, comparing with the 1.151 program |
| [docs/porting-1151-1163.md](docs/porting-1151-1163.md) | **porting a mod between 1.151 and 1.163**: what changed, how to guard builds, step-by-step site porting, anchor addresses, what each of our mods would need |
| [docs/open-questions.md](docs/open-questions.md) | what is unknown or undecided, and the list of Ghidra fixes to raise with logdot |
| [STATUS.md](STATUS.md) | release plan, open pull requests, known build breaks (the only file with perishable state) |
| [docs/roadmap.md](docs/roadmap.md) | long-term mod wish list (bugs, QoL, AI, mod scope) and wanted modder tooling; not scheduled, do not act on it unasked |

## Reference (how the game is built)
| Read | For |
|---|---|
| [docs/formats.md](docs/formats.md) | `.seria`, libraries, ships, saves, language packs, textures/`.res`, levels |
| [docs/structures.md](docs/structures.md) | class codes, Body / stats / fleet / map-missile / Creature layouts, `m_category` bits, projectile logic ids |
| [docs/version-differences.md](docs/version-differences.md) | 1.151 vs 1.163: Body and Profile offset remaps, stats record, Ghidra struct status, strings added/removed |
| [docs/systems.md](docs/systems.md) | how launching, engagements, refueling, elevation/arcs, strategic AI, firing and point defence work |
| [docs/sound.md](docs/sound.md) | **playing a game sound from a mod**: the `playSFXSound_` call (argument table, Rust type), the volume-pointer pitfall (0.0 = silent), sound names, the stock radio, what `hf_ally` plays |
| [docs/engine-hge.md](docs/engine-hge.md) | the HGE engine under the game: interface table, resource loading, stock formats, mod seams |
| [docs/hooks.md](docs/hooks.md) | hooking techniques, who owns which patch site, candidate sites |
| [docs/content.md](docs/content.md) | dialogue, characters, events, textures (study + experiment plan) |
| [docs/total-conversion-hara-vera.md](docs/total-conversion-hara-vera.md) | study of the "Flight to Hara Vera" total conversion |

## Findings
One self-contained note per question; each ends with unknowns or a live-test recipe. (`docs/findings/`)

| Read | For |
|---|---|
| [docs/findings/ai-aircraft-launch.md](docs/findings/ai-aircraft-launch.md) | why the strategic AI launches all aircraft at once, launch conditions, patch sites |
| [docs/findings/ai-flares.md](docs/findings/ai-flares.md) | why AI ships never use flares (missing trigger, not missing parts) and a mod design |
| [docs/findings/combat-missile-launch.md](docs/findings/combat-missile-launch.md) | how enemy ships (and the player) launch Zenith in combat: `FUN_14002ff60` at `0x140065edb`, detach probe, what is not the launch path, burst mod |
| [docs/findings/ai-tick-patch-sites.md](docs/findings/ai-tick-patch-sites.md) | the tactical AI in 1.163: close-range cutoff, stand-off retreat, ammo choice, launch limits, byte-exact patch sites |
| [docs/findings/ammo-1151-vs-1163.md](docs/findings/ammo-1151-vs-1163.md) | the ammo table (built in code), the `Ammo` record, every value change between versions, live ammo-table dump |
| [docs/findings/explosion-damage-1151-vs-1163.md](docs/findings/explosion-damage-1151-vs-1163.md) | why 1.163 missile hits reach deeper into a ship: Zenith warhead 200 to 300, armor hit x2 to x4, part cost flat 5 to maxHP/20; 180mm shells unchanged; run-time evidence from both versions |
| [docs/findings/firing-and-shells.md](docs/findings/firing-and-shells.md) | `FireShell` dispatch, shell HP and lifetime, where projectile constants live |
| [docs/findings/cluster-bomblet-ttl.md](docs/findings/cluster-bomblet-ttl.md) | cluster/mine bomblet spawn function, its two call sites, the TTL patch site (partial) |
| [docs/findings/map-air-groups.md](docs/findings/map-air-groups.md) | map aircraft groups, intercept probabilities, which code starts which engagement |
| [docs/findings/sensors-and-crew.md](docs/findings/sensors-and-crew.md) | how sensors combine (max vs sum), crew capacity vs fuel capacity |
| [docs/findings/end-game.md](docs/findings/end-game.md) | the scripted end game: phases, `endWar`, escalation |
| [docs/findings/khiva-crash.md](docs/findings/khiva-crash.md) | probable cause of the Khiva end-game crash (unguarded list writes), patch recipe |
| [docs/findings/flare-crash-hunt.md](docs/findings/flare-crash-hunt.md) | the flare/proximity-fuse crash: fixed upstream by highfleet-qol (site and null pointer), plus the flare release path and flare body layout |
| [docs/findings/mouse-sensitivity.md](docs/findings/mouse-sensitivity.md) | mouse sensitivity path; A220 slowdown not yet located (partial) |
| [docs/findings/level-seria-dispatcher.md](docs/findings/level-seria-dispatcher.md) | `SomethingWithLevelSerias`: the SCR_* scenario dispatcher in 1.151 and 1.163, label addresses, string refs (names only, body unread) |
| [docs/findings/click-func.md](docs/findings/click-func.md) | the GUI click handler `ClickFunc` (1.151 `0x1401261d0`, 1.163 `0x14012f120`): size, caller, what the probe logs, live-test recipe; also the 252-name element catalog and four decompiled branches (BUY_BUY, FUEL_BUY_SLIDER, MAPMODE_MISSION_*) |
| [docs/findings/source-file-names.md](docs/findings/source-file-names.md) | the 15 original source-file paths embedded in the exe (`HYBRID FLEET 2013EX`) and what they say about the code layout |
| [docs/findings/battle-ally.md](docs/findings/battle-ally.md) | the AI ally in battle (`hf_ally`, running in game): what makes a Creature AI-run, how the vanilla deploy spawns the ally, the retreat point and extraction (why a promoted ship could not retreat), the ORDER role table in `+0xd70` (1 unset, 2 bombing, 3 support), prize ships and trade convoys, ally flares, the AI's ammo flags, checklist, AI plan |
| [docs/findings/precombat-screen.md](docs/findings/precombat-screen.md) | the pre-combat screen: the two builders (`FUN_1402d73a0` is the live one), card order = squad order, the native ammo selector layout, the per-ship ALLY buttons `hf_ally` builds on it, how they follow a card shuffle, the slot-1 PLAYER text label and the roller covers |
| [docs/rendering/gui-elements.md](docs/rendering/gui-elements.md) | making a GUI element the game's own way: the creation recipe (12-argument initializer), element list and fields, coordinates, hiding instead of freeing, the `ClickFunc` swallow trampoline |

## Rendering
How the game draws; start at the README. (`docs/rendering/`)

| Read | For |
|---|---|
| [docs/rendering/README.md](docs/rendering/README.md) | plain-language overview: how a frame is drawn, what a seam is, recipe to draw text and sprites, best seam per screen, how to test a seam |
| [docs/rendering/editor-frame.md](docs/rendering/editor-frame.md) | where an in-game editor hint could hook: `_FrameFunc` task order, game-thread input site, text path; history of the drawing question, the answer is [render-pipeline.md](docs/rendering/render-pipeline.md) |
| [docs/rendering/render-pipeline.md](docs/rendering/render-pipeline.md) | how the game draws: frame tasks, scene dispatcher, stock `hgeFont` text path, fonts, hook seam |
| [docs/rendering/fonts.md](docs/rendering/fonts.md) | every game font: files, metrics, ASCII-only charsets, what the editor uses, live look of the sampled ones, how a mod draws text |
| [docs/rendering/images-and-sprites.md](docs/rendering/images-and-sprites.md) | every image is an `Animation` in `Media/Tex/*.res`, resource getters, sprite object layout, `Render` / `RenderEx` (drawing confirmed in game, run 2) |

## Runs
Dated probe and seam-test reports: evidence, not reference. (`docs/runs/`)

| Read | For |
|---|---|
| [docs/runs/probe-run-1.md](docs/runs/probe-run-1.md) | runs 1-3 of the `hf_probe` debug DLL (v1.0 to v2.0): input and memory diff in every screen, pinned cursor, mode and state bytes, clicks, gold, location and fleet |
| [docs/runs/ui-events-and-screens.md](docs/runs/ui-events-and-screens.md) | probe v2.0 run: log-only hooks for clicks, text keys, sounds and level loads, gold, location and fleet watchers, which dispatcher flag is which screen |
| [docs/runs/seam-test-run-1.md](docs/runs/seam-test-run-1.md) | seam test runs 1 and 2 (probe v2.2): labels after every flush call of the map, battle and menu renderers, which seams fire and which are clean; map seam M11 chosen |
| [docs/runs/ally-probe-run-1.md](docs/runs/ally-probe-run-1.md) | `hf_ally` v0.3.1 probe: ally against nearest enemy over three campaign battles (speed, ammo spent, targets); the ally is not slower than the enemy |
| [docs/runs/ally-runs.md](docs/runs/ally-runs.md) | dated `hf_ally` run reports v0.1 to v0.4: spawn, strike run, mode 0, retreat key, auto-retreat, handover |

## Mods
One short page per mod, and the debug-only `hf_probe`. (`docs/mods/`)

| Read | For |
|---|---|
| [docs/mods/voice.md](docs/mods/voice.md) | `hf_voice`: key-bound sounds from loose `.wav` files (no `.res` edit), the player package |
| [docs/mods/elevation.md](docs/mods/elevation.md) | set the elevation (`m_floor`) of the held shipworks part; keys, config, mechanism |
| [docs/mods/speed.md](docs/mods/speed.md) | configurable map cruise speed: `vanilla` / `classic` / `custom` presets and the QoL port |
| [docs/mods/multicharge.md](docs/mods/multicharge.md) | parts that launch several times before they are used up (charge level = part id) |
| [docs/mods/salvo.md](docs/mods/salvo.md) | map missile launch delay and grouping a salvo into one map missile |
| [docs/mods/refuel.md](docs/mods/refuel.md) | multiplier for the station refuel rate (player and AI) |
| [docs/mods/probe.md](docs/mods/probe.md) | `hf_probe`, the debug-only logging DLL: install, config, what it logs |

## Data
Tables. (`docs/data/`)

| Read | For |
|---|---|
| [docs/data/clickfunc-elements.tsv](docs/data/clickfunc-elements.tsv) | the `ClickFunc` element catalog as a table: group, first-test address, name, times seen, mod idea (companion to [click-func.md](docs/findings/click-func.md)) |
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

## Reference material
Config.ini reference, summaries of community guides and prior art. (`ref/`)

| Read | For |
|---|---|
| [ref/config-ini.md](ref/config-ini.md) | `Config.ini` keys (unverified, from a community document) |
| [ref/community-guides.md](ref/community-guides.md) | summaries of community guides and prior art (the Steam guide PDF is kept locally, not committed) |

Mods (all on [Highfleet-Modloader](https://github.com/logdot/Highfleet-Modloader)):
[highfleet-elevation](https://github.com/mxtrnhf/highfleet-elevation), [highfleet-speed](https://github.com/mxtrnhf/highfleet-speed),
highfleet-multicharge, highfleet-salvo, highfleet-refuel.
The QoL fork of logdot's highfleet-qol carries the refuel, speed and elevation ports (open pull requests: [STATUS.md](STATUS.md)). `hf_probe` is a debug-only DLL, not a QoL mod: [docs/mods/probe.md](docs/mods/probe.md).
