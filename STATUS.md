# Project status

The only file with perishable state: what is installed, released, open upstream or broken. Everything else in these notes is meant to stay true without edits. Last updated 2026-10-28, read from the game folder (`~/.local/share/Steam/steamapps/common/HighFleet/Modloader`), the repos' `git log` and `gh pr list`, not from older notes. Older versions of this file are in git history.

## Installed in the game folder
| Mod | File in `mods/` | Source commit | Config that matters |
|---|---|---|---|
| [hf_ai](docs/mods/hf-ai.md) | `hf_ai_v0.7.1.dll` | `ca7d678` (repo HEAD `7db1521` only changed the README; the DLL is byte-identical to the repo's release build) | `hf_ai.json`: `ai_flares` on, `log_panic`, curtain 0.6; `tactics` on, dive on, aim awareness on, strafe off |
| [hf_ally](docs/mods/hf-ally.md) | `hf_ally_v0.13.7.dll` (installed 2026-10-28; older builds in `Modloader/*.bak_pre-*` and `old_mod_backups/mods/`) | `6ff6a02` on `main` of `mxtrnhf/highfleet-allies` (v0.13.7: chosen loadouts carry only their parts, `extra_gunpod` vanilla T-7/LA-29 only; includes v0.13.6 gunpod, v0.13.5 refund, v0.13.4 label fix) | `ally.json`: `max_allies` 2, `auto_retreat`, `flagship_leaves` handover, `ally_ai_ammo` on, `extra_gunpod` true, `telemetry` off |
| [hf_probe](docs/mods/probe.md) | `hf_probe_v3.5.1.dll` (installed 2026-10-20; v3.5.0 and older in `old_mod_backups/mods/`) | `8d66564` (repo `hf_probe`, local only, master) | `probe.json`: blast / damage / ship-removal hooks on; v3.5.1 prints contact damage with 6 decimals so the impulse is `dmg/0.8` |
| [QoL fork](docs/mods/qol.md) | `highfleet_qol.dll` | `95e8bc7` (branch `ai-flares`; the file was written 1 minute after that commit) | `qol.json`: `ai_flares.enabled` false (hf_ai carries it), flare crash fix on, dump chance 0.7, delay 0.6 to 1.5, refuel player x10, speed `classic`, elevation on |

**2026-10-26 update (QoL row above is older):** the installed `highfleet_qol.dll` is the fork branch `allies-qol` at `e7ab6ab` (local only, includes branch `elevation-rules`, which is pushed to `mxtrnhf/highfleet-qol`), built with `--features 1_163`. `qol.json` has `"elevation_rules": "classic_kaz"` (details: [findings/elevation-rules-1151-vs-1163.md](docs/findings/elevation-rules-1151-vs-1163.md)). The first three patches were seen applied in the game log of 2026-10-26 18:58 (on the build before the truss detours); the truss detours (`classic_kaz`) have not run in the game yet. Backups next to the install: `Modloader/highfleet_qol.dll.bak_pre-*` and `Modloader/config/qol.json.bak_pre-*` (`pre-elevation-rules`, `pre-classic-kaz`, `pre-four-value`). Do not copy a DLL while the game runs (a build was replaced under a running game once, 19:13).

**2026-10-28 update (hf_ally):** installed `hf_ally_v0.13.7.dll` (commit `6ff6a02`, pushed to `mxtrnhf/highfleet-allies` `main`). v0.13.4 hides the PLAYER / plane labels once pre-combat is gone and under the Esc shade; v0.13.5 fixes the ammo refund; v0.13.6 adds `extra_gunpod` (vanilla T-7/LA-29 bomb/rocket planes give the 37 mm and stay for a strafing phase after the payload, `Combat.seria` only); v0.13.7 makes a chosen loadout carry exactly its parts (no vanilla class-3 stock top-up, which was adding NAR-122 to FAB planes) and limits the gunpod to vanilla crafts (custom SB-15 excluded). Gunpod seen working in campaign; the v0.13.7 no-draw/custom-craft gate still needs a Shipworks/SB-15 re-test. Backup: `Modloader/hf_ally_v0.13.6.dll.bak_pre-0.13.7`. Algorithm and addresses: [findings/gun-ammo-funding-and-refund.md](docs/findings/gun-ammo-funding-and-refund.md), [findings/plane-combat-modes-and-gunpods.md](docs/findings/plane-combat-modes-and-gunpods.md).

The `mods/` folder holds exactly these four DLLs (older builds and `.bak` files are in `old_mod_backups/mods/`). Not installed: `hf_voice`.

## Custom-aircraft test install (2026-10-25, game folder; not yet played)
* `mods/hf_ally_v0.13.1-custom-planes.dll` = the six-row column build from before the squash (commit `e5963fd`, now folded into `6c44bbf`); **released 2026-10-25 as `mxtrnhf/highfleet-allies` v0.13.6 = hf_ally 0.13.2** (commit `6c44bbf`, pack `hf_release_pack_v0.13.6.zip` in the workspace root, GitHub Release attached). The game folder still holds the pre-release build; install `hf_ally_v0.13.2.dll` from the pack to match. Previous DLLs: `Modloader/*.bak_pre-custom-planes`, `*.bak_pre-column`, `*.bak_pre-six`.
* `mods/ShipworksExtended.dll` (upstream v1.1.3) + `config/Shipworks.json` (`Crafts: [CRAFT_SB15]`) installed 22:25 so the plane shows in the Shipworks palette.
* Hara Vera's `CRAFT_SB15` merged into `Libraries/parts.seria`, `Libraries/OL.seria`, `Media/Tex_Extra/Extra.res` (+ `SB15.png`), both dialog packs and `qol.json` (`planes`, `enable_shop_parts` true, `shop_parts.CRAFT_SB15` at 100 %). Originals in `hf_game_backups/sb15_2026-10-25/`. Steam "verify files" undoes the data files. Recipe and open questions: `docs/findings/custom-aircraft.md`.

## Repos
| Repo | Remote | State |
|---|---|---|
| `hf_ai`, `hf_voice`, `hf_probe`, `hf_draw_test` | none (the only copies are on this machine) | clean; `hf_ally` is the exception in the next row |
| `hf_ally` | `origin` = `mxtrnhf/highfleet-allies` | `main` pushed at `20ec6bb` (v0.13.5); side branch `side/ignore-intercept-oids` (`09571bd`, v0.12.11-ignoreoid.1, `intercept_ignore_oids`, for a modder's Sprint; never merged; tester pack in `hf_side_patches/ignoreoid_pack/`, untested in play) |
| `hf_qol_fork` | `origin` = `mxtrnhf/highfleet-qol`, `upstream` = logdot | feature branches (`elevation`, `refuel-rate`, `pin-highfleet-rs`) are on origin; branch `ai-flares` (installed build, `95e8bc7`) is local only; local `main` is 4 commits ahead of `origin/main` |
| `hf_notes` | `mxtrnhf/hf_notes` | pushed (origin/master) as of 2026-10-19 |
| `old_standalone/*` | `hf_elevation` and `hf_speed` published, the rest local | the pre-merge standalone mods |

## Upstream (logdot/highfleet-qol)
| PR | State | What |
|---|---|---|
| #19 | merged 2026-10-14 (`f5423ca`) | refuel rate and speed curve |
| #20 | open | manual elevation (rebased 2026-10-16 as `aafbf6e`, 5 commits) |
| #18 | open | pin `highfleet-rs` to the last revision that builds |

* **`enabled` rule (logdot's review of #19):** only `elevation` and `ai_flares` may have an `enabled` flag; every other section defaults to vanilla. The flag crept back into refuel and speed once, from branches cut before the review.
* **Build break (found 2026-10-14):** `highfleet-qol` depends on `highfleet-rs` by git URL with no pinned revision and `Cargo.lock` is gitignored, so a fresh build resolves the newest `highfleet-rs`. Its commit `cfa6ae28` removed `Ammo::unknown_180h`, which `src/plane_guns.rs:271` still uses, so `cargo check --features 1_163` fails. Pinning `highfleet` to `3f6b54b3` in a local lockfile builds (copy `hf_qol_fork/Cargo.lock` into a fresh worktree). Fixed by PR #18; CI on PR #20 stays red until it merges.
* **Modloader quirk:** the modloader README says the release zip is `Artifacts.zip` and yields both `bass.dll` and `bass.dll_`. v4.1.0's `Modloader.zip` has only the loader `bass.dll`, so users must rename the original `bass.dll` to `bass.dll_` themselves.
* Standalone repos are the pre-merge versions. Salvo is postponed. `hf_probe` and `hf_draw_test` are debug-only and not released.

## Tester packs (workspace root)
Newest: `hf_release_pack_v0.12.2_debug.zip` (folder `hf_release_pack_v0.12.2_debug`); earlier: `v0.11.11_debug`, `v0.11.3_debug`, `v0.11.2_debug`, `v0.10.3`, `v0.9.3`. A pack holds the DLLs, a `qol.json` with every required key at stock values, an `ally.json` and a `README.txt` (settings, where the logs are, the tester plan: [docs/runs/tester-test-plan.md](docs/runs/tester-test-plan.md)). The pack's `qol.json` must keep the keys that have no serde default (list in [docs/mods/qol.md](docs/mods/qol.md)). The v0.10.3 pack carries one custom audio file, `Media/Snd/RADIO/radio_stall_01.wav`, which overwrites the vanilla file (testers are told to back it up).

## Open items
| Item | Notes |
|---|---|
| Analyse the hf_ai v0.7.1 run | sessions 1792342753/843/949/955; replay `tuning_telemetry/visualizer/replay_v071.html`; check ETA timing, shelter, strays, difficulty |
| Ghidra check-in | the 2026-10-18 annotations (AI fire gates, Zenith launch, fire bytes) are applied and saved; the shared-project check-in with the message "Annotate 1.163: AI fire gates, Zenith launch, fire bytes" is yours |
| Merge/engagement crash (testers) | scene state 2 of `SomethingWithLevelSerias` (`0x1402be084`) calls `FUN_1400f5b40` at `0x1402be0c8`; when the player-side vector `0x143a158e0` is empty the code passes a zero register and the callee dereferences it with no null check (`0x1400f5b4f`) [code, bytes read 2026-10-20]. **Fingerprint to look for in a tester's crash report: `Highfleet.exe+0xF5B4F`, access violation reading `0x100`** (other variants: `+0x2BEB4A` / `+0x2C108D` reading `0x8` [agent]). Seen in play: vector null after leaving a city, empty after a load. Needs: the crash address to confirm, the tester's save, the three-way test (no mods / QoL only / hf_ally only), land-after-merge and land-after-load repros. Details: [docs/runs/ally-runs.md](docs/runs/ally-runs.md), [docs/findings/battle-ally.md](docs/findings/battle-ally.md#fleets-landing-and-the-location-scene) |
| `Collect_dead` stock crash | 1 in about 60 kills; waiting for a `hf_ally_deadnode.log` capture: [docs/findings/collect-dead-crash.md](docs/findings/collect-dead-crash.md) |
| AI ammo flags | ANSWERED 2026-10-20: the battle spawner sets creature `+0xc7c` (AP) / `+0xc7d` (proximity) once per ship by dice from rating and the first group-0 gun's calibre; details in [docs/findings/ai/ai-tick-patch-sites.md](docs/findings/ai/ai-tick-patch-sites.md) section 3. `hf_ally_ammo_*.csv` (in the installed sim.16/17 build) confirms it. `Profile +0x164` is the easy-difficulty byte (`+0x165` hard), see [docs/rendering/click-func-analysis.md](docs/rendering/click-func-analysis.md). The refund side is fixed in hf_ally v0.13.5: [findings/gun-ammo-funding-and-refund.md](docs/findings/gun-ammo-funding-and-refund.md). Open: the big spawner's full condition chain |
| Ghidra 2026-10-29 sweep | eight waves over the unnamed functions: ~2,623 renames + 515 created functions, all with doc-style plate comments; the 0x140080000 block turned out to be the D3D11 shader layer (class map from RTTI); the `/EH` funclet tail was mapped through `.pdata`/`FuncInfo4` to 347 owners; the CRT C-initialiser table, the `.rdata` vtable slots and the Body slots were created/named. Program now 4,128 named / 142 `FUN_*` / 1,151 `rep_*` (76.15%). Verified against the live program. `rep_*` labels proved unreliable (not ICF replicas). Changes and remaining clusters: [docs/data/ghidra-changes-2026-10-29.md](docs/data/ghidra-changes-2026-10-29.md); per-agent tables in `docs/data/ghidra-sweep-2026-10-29-*agent*.md`. The shared-project check-in is yours |
| Ghidra 2026-10-26 | ds3 agent round reviewed and annotated (changes: [docs/data/ghidra-changes-2026-10-26.md](docs/data/ghidra-changes-2026-10-26.md)); the shared-project check-in is yours. Reports in `hf_ml/out/ds3-*/REPORT.md` (git-excluded). `ds3-target` finished: box = `sign_aim` at `playerShip+0xb00` (fixed 62 px), aim = relative offset `0x1403c0dc8/dcc`, target writer unconfirmed (runtime log of `ship+0xb28/+0xb00` would settle it): [docs/findings/battle-hud-callouts.md](docs/findings/battle-hud-callouts.md) section 9 |
| Missile dump | kills about 20% of some launchers' missiles at the old delay; delay 0.6 to 1.5 cut early deaths from 19% to 5%, still being tuned |
| Pre-combat ALLY buttons | `hf_ally_v0.11.8` cover gate untested; with `hf_voice` loaded (same hook) the buttons do not follow the cards: [docs/rendering/precombat-screen.md](docs/rendering/precombat-screen.md) |
| Ally untested paths | ally destroyed in battle, prize-safe targeting on a convoy, several allies with `handover` |
| Allied bombers | needs bomb telemetry first (inventory, release counter, altitude); see the AI ideas in [docs/roadmap.md](docs/roadmap.md) |
| Audio clipping | reported, cause unknown (game, or the flare curtain); parked |
| README follow-ups | troubleshooting, a worked "add a part" guide; optional move to the modloader's logging SDK |

## Data and working rules
* Combat telemetry is in `tuning_telemetry/`; the ledger `REVIEWED.tsv` lists analysed sessions, unlisted ones in `Modloader/logs` are new. The user labels ships (Shipworks designs are named `TestProject`).
* Install DLLs and change game configs only when asked; keep a `.bak`. Long open questions: [docs/open-questions.md](docs/open-questions.md).
