# Total conversion study: "Flight to Hara Vera" 2.0.1

A story/content total conversion for Steam 1.163, distributed as a 933 MB installer (`Flight to Hara Vera FINAL-16-2-0-1-...exe`, default folder = the Steam HighFleet folder).
Analysed **statically**: the installer was never run. Credits in its README: story/sprites/modules/dialog by Shieldbearer, 2.0 by Duumvir, modloader by logdot, character and background art by Midjourney.
Its README says: it does not change the core of the game; it needs the modloader ("the ONLY way to mod highfleet to this degree, most of the game is hardcoded"); **GOG is not supported**; uninstall = run the uninstaller, then verify game files in Steam.

## What is in the package (no replaced `Highfleet.exe`)
| Part | Content |
|---|---|
| `Data/Dialogs/` | both language packs, heavily rewritten (below) |
| `Libraries/` | `OL.seria`, `parts.seria`, `constructor.seria` |
| `Media/` | 298 files: 40 identical to vanilla, **120 changed**, **138 new** (17 PNG, 16 `.res`, 104 audio); `media.res` edited |
| `Objects/Designs/` | 177 ships (vanilla 163: 16 new, 2 removed) |
| `Shaders/` | 11 files, 3 changed |
| `Modloader/` | `ShipworksExtended.dll`, `highfleet_qol.dll`, `ammo_extended.dll` + `Shipworks.json`, `qol.json`, `ammo_extended.json` (shell parameters, 29 KB); 372 stray developer log files shipped by accident |
| root | modloader `bass.dll` + original `bass.dll_`, `Config.ini`, READMEs (EN/RU), changelog, music list |

## Textures and media: **adding art needs only data** [verified from the files]
* New atlases: `Hall9`-`Hall17.png/.res`, `Static10/11.png/.res`, and a new folder `Media/Tex/FTHV/` (`Firefight`, `Monastery`, `Mutiny`, `Artifacts`, `menu_anim`, `OGANIM`, `end_briefing_01`: each a PNG plus its own `.res`).
  `media.res` gets extra lines: `Include Media/Tex/Hall15.res` ... `Include Media/Tex/FTHV/Monastery.res` ... and `Include Media/Snd/ENDINGS/endings.res`; one vanilla include (`Ships2.res`) is dropped.
* **Part thumbnails = an `Animation` named exactly like the part id**, e.g. `Static11.res` defines `Animation MDL_CANNON_180P { texture = Static11 rect = 1966,3536,98,98 hotspot = 49,49 ... }` (20 of them, 98x98). Nothing else is needed.
* Existing atlases were also overwritten (Static1-8, Hall1-7, Background, Ships1, Fnt1/2, Mapmode, Midground...): the mod replaces vanilla art in place for its re-skinned characters/backgrounds.
* Sound: a new index `Media/Snd/ENDINGS/endings.res` (`Sound Name { filename=...mp3 resgroup=3 }`), `sound.res` repointed to a new `FTHVMUSIC/` folder (mp3 instead of wav); a `!readme.txt` there explains forcing combat music to play 100% of the time.

## Parts [verified]
`OL.seria` 176 -> 184 ids (15 new: `MDL_BARELEG_01-04`, `MDL_CANNON_180P/GROM/OGON/PYR_152/RAZOR`, `MDL_ENGINE_NERVA`, `MDL_ANTENNA_BIG`, `MDL_MISSILE_CLUSTER`, `MDL_MSL_A100(_CONV)`, `SOLDIER_RIFLEMAN`, 7 removed);
`parts.seria` 157 -> 176 (25 new incl. `MDL_HOOK_1/2`, `MDL_CATAPULT`, `MDL_CASEMATE_1`, `MDL_FLAG_01`, `MDL_GRAFFI_01`, `MDL_NEWARMOR2X1_01/02`, `CRAFT_MB110OG`).
Its `Shipworks.json` lists the new fuel, legs, engine, guns, sensor and expendables so they appear in the palette (the same mechanism highfleet-multicharge uses).

## Dialogue, characters, events [verified]
English pack: vanilla 2902 entries -> 3157 (**892 new keys, 637 removed, 840 changed**); Russian: 885 new, 693 removed, 863 changed.
* **No new character names.** Every `<NPC=...>` is one of the original ones (PETR, FASIL, OMAR, DAUD, KNIGHT, HIRE, GIRL, GOVERNOR, PROPHET, HARISHID, HISSID, AIRBORNE, SCOUT, BOY); new characters-by-art were not attempted. No new tag kinds (only a typo `NCP` and `RENDER_LAMP_OFF`).
* New content families: `MONASTERY_MARCH/CORSAIR/PLAIN/...`, `ENDWAR_BRIEFING_CORSAIR`, `EVENT_REVENGE`, `EVENT_MUTINY`, `EVENT_FAMILY`, `EVENT_HUNTERS`, `EVENT_WEDDING`, `EVENT_CHAPEL`, `EVENT_BOX`, `EVENT_SARYAN`, `EVENT_DINNER_*`, `EVENT_DRINKERS`, `EVENT_ANTONTROUBLE`, `EVENT_TOWN_CORSAIR`, `BETRAYAL_*`, `INTERCOM_FASIL_MEGAPONTOS`, `INTERCOM_GIRL_GOD`, `HELLO_HARISHID`, `CABIN_PLAYER`, `JOURNAL`, ...
* **How new content is attached, without any code change:** 85 *original* entries were rewritten to jump into new keys, e.g. `ISAIAH_0_1` / `ISAIAH_1_1` / `ENDRACE_SPEECH_1` / `PETR_DAUD_1` / `ANT_1` -> `EVENT_TOWN_CORSAIR_1`, `PETR_DAUD_1` -> `EVENT_DINNER_1`, `ENDWAR_BRIEFING_0` -> `MONASTERY_CORSAIR_1` / `MONASTERY_MARCH_1`,
  `HELLO_BOY_1` -> `HELLO_BOY_CORSAIR_1`, `NUCLEAR_ESCALATION_1` -> `NUCLEAR_ESCALATION_CORSAIR_1`, `KHIVA_ULTIMATUM_1` -> `KHIVA_ULTIMATUM_RADU_1`, `TUTORIAL_*` -> new `TUTORIAL_*_` side branches.
* 581 new keys are never referenced by any tag: they are reached by the **implicit numbering of `<SCR=CONTINUE>`** (an entry without a target advances `KEY_n` -> `KEY_n+1`). This also corrects `content.md`: counting only explicit references undercounts chained entries.

## The installer format (for unpacking without running it)
PE stub (143 KB) + overlay from `0x23000`. Magic `77 77 67 54 29 48 35 14`, then records `[u16 1][u32 csize][u32 usize][u8 method]` + data, method 1 = zlib, 2 = bzip2; stride = `start + 8 + csize`.
First six records: dialog template, a 132 KB resource blob, the uninstaller `Uninstal.exe` (an `MZ` exe), the wizard texts ("Launch the game through the vanilla .exe file (or steam)!", "You can zoom out in battles with mouse wheel!!!"), registry key, and the **file table** (record 5, 109 KB:
per file CRC, uncompressed size, compressed size, three FILETIMEs, path; the CRC is not a plain crc32 of the content). The data region (`0x4b558`..end) is `[method byte][stream]` blocks **in a different order than the table**, so files are matched by uncompressed size.
Result: 879 blocks parsed to the exact end of the file, 879 files named; 101 table entries have no block of their own (same-size or identical content); a few same-size files could be swapped. A real run of the installer would settle those.

## What this proves for our goals
* New textures, part icons, sounds, parts, dialogue, event branches and ships are all possible as pure data on the current modloader stack.
* Entry points are hooked by editing original entries; brand-new random-event roots and new NPC names remain untested (the mod avoided both).
* A distributable mod of this kind is a big overwrite installer; a smaller approach is possible for our own work (extra `.res`, extra `Include`, edited packs) but is still file editing: game updates and "verify files" overwrite it.
