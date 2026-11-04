# Mods: status and where each one lives

One row per mod. Installed versions and open pull requests are perishable and live only in [../../STATUS.md](../../STATUS.md).

## Mods we ship or build on
| Mod | Status | Repo | Page |
|---|---|---|---|
| `hf_ai` | active | `mxtrnhf/highfleet-allies` (`ai/`) | [hf-ai.md](hf-ai.md) |
| `hf_ally` | active | `mxtrnhf/highfleet-allies` (`ally/`) | [hf-ally.md](hf-ally.md) |
| QoL build (`highfleet_qol`) | refuel and speed merged upstream, elevation PR #20 draft, `elevation_rules` ported into the bundled build | `qol/` in `mxtrnhf/highfleet-allies`; older fork `hf_qol_fork` had `origin` = `mxtrnhf/highfleet-qol`, `upstream` = logdot | [qol.md](qol.md) |
| refuel, speed, elevation | refuel and speed merged upstream; elevation in PR #20 (draft) | pre-merge standalone repos (local; elevation and speed published) | [refuel.md](refuel.md), [speed.md](speed.md), [elevation.md](elevation.md) |
| multicharge | standalone, not installed | local standalone repo (not published) | [multicharge.md](multicharge.md) |
| salvo | standalone, postponed | local standalone repo (not published) | [salvo.md](salvo.md) |
| multimissile | standalone, local only (not read in this pass) | local standalone repo (not published) | none |

`hf_ai` tuning: [hf-ai-tuning-guide.md](hf-ai-tuning-guide.md) (v0.9.0, archived; the current guide is maintained in the public `highfleet-allies` repo).

## Debug and experiments
None of these is a QoL mod. `hf_voice` has a player package; the rest are debug-only.

| Mod | What it is | Status | Page |
|---|---|---|---|
| `hf_probe` | log-only probe: input and memory diffs, hooks on clicks, text, sounds, level loads, damage; the seam test | v3.5.1; the source of most `runs/` evidence | [probe.md](probe.md) |
| `hf_voice` | plays loose `.wav` files on a key through the game's own sound call | local repo, player package v0.1.2; shares a hook with `hf_ally`, so they are not run together | [voice.md](voice.md) |
| `hf_draw_test` | font sampler used to choose the elevation hint font | finished its job (2026-10-14), local repo | none; result in [../rendering/fonts.md](../rendering/fonts.md) |
| `hf_funccall` | calls a game function by absolute address from a hotkey or a config list and logs the result | skeleton v0.1, untested in game, **parked** (a review on 2026-10-16 found brute-force calling cannot work; `hf_probe` is the tool for evidence) | none; the repo's `README.md` and `NOTES.md` are the only docs |
| `hf_aa_missile` | scratch for the first multi-charge AA missile (`MDL_AA_X3` as data only, `ShipworksExtended.dll` adds it to the palette) | stage 1 done, stage 2 became multicharge; no git repo | none; findings are in [multicharge.md](multicharge.md) |
