# HighFleet reverse-engineering notes

Notes behind the HighFleet mods: Steam **1.163**, with **1.151** comparisons. Image base: `0x140000000`.

## Start here

- [Project status](STATUS.md): installed builds, releases, open items and pending in-game checks.
- [Setup and working rules](docs/setup.md): tools, building, safe edits and Ghidra pitfalls.
- [Detailed reference catalog and evidence tags](docs/README.md): descriptions of the reference notes and datasets.
- [Open questions](docs/open-questions.md), [roadmap](docs/roadmap.md) and [mishaps](docs/mishaps.md).

## Browse by subject

| Directory | Contents |
|---|---|
| [Findings](docs/findings/README.md) | AI, aircraft, combat, crashes, engine internals, physics, ships, simulator and strategy |
| [Rendering and GUI](docs/rendering/README.md) | Frame pipeline, text, sprites, screens, controls and HUD |
| [Mods](docs/mods/README.md) | Mod reference pages, configuration and debug tools |
| [Runs](docs/runs/README.md) | In-game observations, benchmarks and dated simulator validation |
| [Ghidra history](docs/ghidra/README.md) | Dated change logs, sweep reports and audit evidence |
| [Data](docs/data/README.md) | Porting tables, GUI captures and the terrain reference implementation |
| [Plans](docs/plans/README.md) | Research plans, not verified findings |
| [Third-party reference](ref/README.md) | Community material and explicitly unverified outside reports |

## Core references

[Native structures](docs/structures.md) · [File formats](docs/formats.md) · [Hooks](docs/hooks.md) · [HGE engine](docs/engine-hge.md) · [Sound](docs/sound.md) · [Content](docs/content.md) · [Version differences](docs/version-differences.md) · [Porting 1.151 → 1.163](docs/porting-1151-1163.md)

## Filing rules

- Put durable answers in the appropriate findings topic; keep UI research in `docs/rendering/`.
- Put run-specific evidence in `docs/runs/`, and Ghidra change/sweep/audit records under `docs/ghidra/YYYY-MM-DD/`.
- Keep reusable datasets in `docs/data/`, grouped by purpose. Keep third-party material in `ref/`.
- Keep filenames descriptive and update relative links and the relevant folder index when moving or adding notes.
- `STATUS.md` remains the source for current installed/released versions and open work. Dated reports describe their historical run, not current status.

Mods use [Highfleet-Modloader](https://github.com/logdot/Highfleet-Modloader). Main mod repository: [highfleet-allies](https://github.com/mxtrnhf/highfleet-allies); other repositories are listed in the [mod index](docs/mods/README.md).
