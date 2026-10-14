# Highfleet 1.163 reverse-engineering notes

Short, topic-based notes behind the Highfleet mods (Steam 1.163, image base `0x140000000`).
Tags (one legend for all docs): **[game]** verified in play or on the real game files · **[code]** read from the decompilation · **[guide]** community guide, unverified here · **[guess]** inferred.

## Start here
| Read | For |
|---|---|
| [docs/install.md](docs/install.md) | **installing the mods on a clean game**: order, per-mod steps, test settings, pass/fail log lines, troubleshooting |
| [docs/setup.md](docs/setup.md) | tools, modloader, building, pitfalls, safe-edit rules, comparing with the 1.151 program |
| [docs/porting-1151-1163.md](docs/porting-1151-1163.md) | **porting a mod between 1.151 and 1.163**: what changed, how to guard builds, step-by-step site porting, anchor addresses, what each of our mods would need |
| [docs/open-questions.md](docs/open-questions.md) | what is unknown or undecided, and the list of Ghidra fixes to raise with logdot |
| [docs/roadmap.md](docs/roadmap.md) | long-term mod wish list (bugs, QoL, AI, mod scope) and wanted modder tooling; not scheduled, do not act on it unasked |

## Reference (how the game is built)
| Read | For |
|---|---|
| [docs/formats.md](docs/formats.md) | `.seria`, libraries, ships, saves, language packs, textures/`.res`, levels |
| [docs/structures.md](docs/structures.md) | class codes, Body / stats / fleet / map-missile / Creature layouts, `m_category` bits, projectile logic ids |
| [docs/version-differences.md](docs/version-differences.md) | 1.151 vs 1.163: Body and Profile offset remaps, stats record, Ghidra struct status, strings added/removed |
| [docs/systems.md](docs/systems.md) | how launching, engagements, refueling, elevation/arcs, strategic AI, firing and point defence work |
| [docs/engine-hge.md](docs/engine-hge.md) | the HGE engine under the game: interface table, resource loading, stock formats, mod seams |
| [docs/hooks.md](docs/hooks.md) | hooking techniques, who owns which patch site, candidate sites |
| [docs/content.md](docs/content.md) | dialogue, characters, events, textures (study + experiment plan) |
| [docs/total-conversion-hara-vera.md](docs/total-conversion-hara-vera.md) | study of the "Flight to Hara Vera" total conversion |
| [docs/mods/](docs/mods/) | one short page per mod: elevation, speed, multicharge, salvo, refuel |
| [ref/](ref/) | Config.ini reference, summaries of community guides and prior art |

## Findings (one self-contained note per question; each ends with unknowns or a live-test recipe)
| Read | For |
|---|---|
| [docs/findings/ai-aircraft-launch.md](docs/findings/ai-aircraft-launch.md) | why the strategic AI launches all aircraft at once, launch conditions, patch sites |
| [docs/findings/ai-flares.md](docs/findings/ai-flares.md) | why AI ships never use flares (missing trigger, not missing parts) and a mod design |
| [docs/findings/ai-tick-patch-sites.md](docs/findings/ai-tick-patch-sites.md) | the tactical AI in 1.163: close-range cutoff, stand-off retreat, ammo choice, launch limits, byte-exact patch sites |
| [docs/findings/ammo-1151-vs-1163.md](docs/findings/ammo-1151-vs-1163.md) | the ammo table (built in code), the `Ammo` record, every value change between versions |
| [docs/findings/explosion-damage-1151-vs-1163.md](docs/findings/explosion-damage-1151-vs-1163.md) | why 1.163 missile hits reach deeper into a ship: Zenith warhead 200 to 300, armor hit x2 to x4, part cost flat 5 to maxHP/20; 180mm shells unchanged; run-time evidence from both versions |
| [docs/findings/firing-and-shells.md](docs/findings/firing-and-shells.md) | `FireShell` dispatch, shell HP and lifetime, where projectile constants live |
| [docs/findings/cluster-bomblet-ttl.md](docs/findings/cluster-bomblet-ttl.md) | cluster/mine bomblet spawn function, its two call sites, the TTL patch site (partial) |
| [docs/findings/map-air-groups.md](docs/findings/map-air-groups.md) | map aircraft groups, intercept probabilities, which code starts which engagement |
| [docs/findings/sensors-and-crew.md](docs/findings/sensors-and-crew.md) | how sensors combine (max vs sum), crew capacity vs fuel capacity |
| [docs/findings/end-game.md](docs/findings/end-game.md) | the scripted end game: phases, `endWar`, escalation |
| [docs/findings/khiva-crash.md](docs/findings/khiva-crash.md) | probable cause of the Khiva end-game crash (unguarded list writes), patch recipe |
| [docs/findings/flare-crash-hunt.md](docs/findings/flare-crash-hunt.md) | the flare/proximity-fuse crash hunt (site not found) |
| [docs/findings/mouse-sensitivity.md](docs/findings/mouse-sensitivity.md) | mouse sensitivity path; A220 slowdown not yet located (partial) |
| [docs/findings/editor-hints.md](docs/findings/editor-hints.md) | where an in-game editor hint could hook: `_FrameFunc` task order, game-thread input site, text path (partial) |
| [docs/findings/render-pipeline.md](docs/findings/render-pipeline.md) | how the game draws: frame tasks, scene dispatcher, stock `hgeFont` text path, fonts, hook seam |
| [docs/findings/fonts.md](docs/findings/fonts.md) | every game font: files, metrics, ASCII-only charsets, what the editor uses, live look of the sampled ones, how a mod draws text |
| [docs/findings/probe-run-1.md](docs/findings/probe-run-1.md) | first run of the `hf_probe` debug DLL: input and memory diff in every screen, pinned cursor, mode and state bytes, v1.1 plan |
| [docs/findings/images-and-sprites.md](docs/findings/images-and-sprites.md) | every image is an `Animation` in `Media/Tex/*.res`, resource getters, sprite object layout, `Render` / `RenderEx` (drawing unconfirmed) |
| [docs/findings/ui-events-and-screens.md](docs/findings/ui-events-and-screens.md) | probe v2.0 run: log-only hooks for clicks, text keys, sounds and level loads, gold, location and fleet watchers, which dispatcher flag is which screen |
| [docs/findings/seam-test-run-1.md](docs/findings/seam-test-run-1.md) | probe v2.2 seam test: labels after every flush call of the map, battle and menu renderers, which seams fire and which are clean |
| [docs/findings/level-seria-dispatcher.md](docs/findings/level-seria-dispatcher.md) | `SomethingWithLevelSerias`: the SCR_* scenario dispatcher in 1.151 and 1.163, label addresses, string refs (names only, body unread) |
| [docs/findings/how-the-game-draws.md](docs/findings/how-the-game-draws.md) | plain-language overview: how a frame is drawn, what a seam is, recipe to draw text and sprites, best seam per screen, how to test a seam |
| [docs/findings/click-func.md](docs/findings/click-func.md) | the GUI click handler `ClickFunc` (1.151 `0x1401261d0`, 1.163 `0x14012f120`): size, caller, what the probe logs, live-test recipe |
| [docs/findings/click-func-elements.md](docs/findings/click-func-elements.md) | catalog of the 252 GUI element names `ClickFunc` (1.163) compares against, with first test address and whether the probe has seen them; lower bound, 209 never seen |
| [docs/findings/click-func-branches.md](docs/findings/click-func-branches.md) | four decompiled `ClickFunc` (1.163) branches, cleaned: BUY_BUY (slider = target total, delta buy/sell), FUEL_BUY_SLIDER (compares Location `+0x274`), MAPMODE_MISSION_FULLTANK/HALFTANK |
| [docs/findings/source-file-names.md](docs/findings/source-file-names.md) | the 15 original source-file paths embedded in the exe (`HYBRID FLEET 2013EX`) and what they say about the code layout |

Mods (all on [Highfleet-Modloader](https://github.com/logdot/Highfleet-Modloader)):
[highfleet-elevation](https://github.com/mxtrnhf/highfleet-elevation), [highfleet-speed](https://github.com/mxtrnhf/highfleet-speed),
highfleet-multicharge, highfleet-salvo, highfleet-refuel.
