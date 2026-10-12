# Highfleet 1.163 reverse-engineering notes

Short, topic-based notes behind the Highfleet mods (Steam 1.163, image base `0x140000000`).
Tags (one legend for all docs): **[game]** verified in play or on the real game files · **[code]** read from the decompilation · **[guide]** community guide, unverified here · **[guess]** inferred.

| Read | For |
|---|---|
| [docs/install.md](docs/install.md) | **installing the mods on a clean game**: order, per-mod steps, test settings, pass/fail log lines, troubleshooting |
| [docs/setup.md](docs/setup.md) | tools, modloader, building, pitfalls, safe-edit rules |
| [docs/formats.md](docs/formats.md) | `.seria`, libraries, ships, saves, language packs, textures/`.res`, levels |
| [docs/structures.md](docs/structures.md) | class codes, Body / stats / fleet / map-missile layouts, `m_category` bits |
| [docs/systems.md](docs/systems.md) | how launching, engagements, refueling, elevation/arcs work |
| [docs/engine-hge.md](docs/engine-hge.md) | the HGE engine under the game: interface table, resource loading, stock formats (.psi, .fnt, .res), mod seams |
| [docs/hooks.md](docs/hooks.md) | hooking techniques and who owns which patch site |
| [docs/mods/](docs/mods/) | one short page per mod: elevation, speed, multicharge, salvo, refuel |
| [docs/content.md](docs/content.md) | dialogue, characters, events, textures (study + experiment plan) |
| [docs/total-conversion-hara-vera.md](docs/total-conversion-hara-vera.md) | study of the "Flight to Hara Vera" total conversion: package, media, parts, dialogue, installer format |
| [docs/open-questions.md](docs/open-questions.md) | what is unknown or undecided |
| [docs/roadmap.md](docs/roadmap.md) | long-term mod wish list (bugs, QoL, AI, mod scope); not scheduled, do not act on it unasked |
| [ref/](ref/) | Config.ini reference, summaries of community guides and prior art |

Mods (all on [Highfleet-Modloader](https://github.com/logdot/Highfleet-Modloader)):
[highfleet-elevation](https://github.com/mxtrnhf/highfleet-elevation), [highfleet-speed](https://github.com/mxtrnhf/highfleet-speed),
highfleet-multicharge, highfleet-salvo, highfleet-refuel.
