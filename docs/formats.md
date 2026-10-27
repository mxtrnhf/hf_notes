# File formats

Tags: legend in `../README.md`.

## `.seria` (parts, ships, saves, levels, config)
* Nested nodes `header=number` + `{` ... `}`; braces alone on their own line; **never indent** (breaks the file). Defaults are omitted.
* A node holds `attr=value` pairs, nested nodes, or (meshes) bare floats. Repeated `attr=value` lines form an array (e.g. 360 `m_sectors` = one per degree).
* The numeric header is the class code (`m_code`): 15 Body, 31 Frame, 47 Creature, 7 Node, 199 location, 327 escadra, 515 intel (see `structures.md`).
* Serializer `FUN_14004f010`, Body field loader `FUN_140025240`.

## Check the game's own data files before guessing [guide]
The game folder (`~/.local/share/Steam/steamapps/common/HighFleet/`) is ground truth for anything that is data and not code. Before reasoning from the decompilation or from probe logs, grep the `.seria` files there:
* `Libraries/OL.seria`: per-part **stats** (price, crew/power/ammo needs, armor, `m_missile_explosive`, `m_missile_ap`, `m_weapon_load_time`, ...). Example: the blast "strength" in the probe's `BLAST` lines is the missile's `m_missile_ap`, and the Zenith warhead (`MDL_MISSILE_01`) is `m_missile_explosive` 200 in 1.151 and 300 in 1.163, found by diffing the two files.
* `Libraries/parts.seria`: **bodies** (`m_health`, `m_health_max`, density, mass, meshes) per `m_oid`.
* `Data/Dialogs/*.seria_enc`: part names (`MDL_MISSILE_01` is "R-5 ZENITH"); decode with the cipher below. `Ships/*.seria` and saves: real ship layouts with part HP.
* **The folder holds whichever version is installed.** Switching the Steam branch overwrites these files, so copy `Libraries/` (and `Data/Dialogs/`) to a versioned folder (for example `hf_notes/ref/game-data-1.151/`) while the other version is installed, then diff. The 1.151 `OL.seria` was seen once and not kept; the 1.163 copies are `~/Downloads/OL.seria`, `~/Downloads/parts.seria`, `hf_aa_missile/backup/*.orig`.
* Quick checks: `grep -n "m_oid=MDL_MISSILE_01" -A40 Libraries/OL.seria`, or load the file with a small script and compare the stats of two versions field by field (what the explosion finding did).

## Part libraries (`Libraries/`)
* `OL.seria`: `m_stats` (class code 2051; the shipped file has 176 records, per the hot-reload study, [findings/hot-reload-feasibility.md](findings/hot-reload-feasibility.md)), one per part id `m_oid`: price, category, crew/power/ammo needs, weapon and missile stats
  (`m_weapon_load_amount/time/rate/caliber`, `m_launched_speed/range`, `m_missile_explosive/ap`, ...; offsets in `structures.md`).
  Not stored in saves, so edits apply to a running campaign after restart. `m_category` is a bit field (table in `structures.md`).
* `parts.seria`: Body prototypes `m_children=15`: `m_oid`, `m_id` (also in each slot's `m_master.id`: cloning needs every occurrence replaced),
  `m_density`, `m_health(_max)`, `m_floor_type`, one `m_mesh`, several `m_sprites`, optional `m_slots`. Copied into ships/saves when a part is
  placed, so edits do **not** reach existing ships. [game]
* Mesh: `m_size` points, X right / Y down. Mass = min(width, height) x polygon area x `m_density` [guide].
* Sprite: `m_animation_name` (registered in a `.res`), `m_position`, `m_scale`, `m_angle`, `m_stage` (layer/condition). Slot: `m_type`, `m_position`
  (an external slot placed inside the mesh does not work) [guide].
* `Libraries/constructor.seria`: old way to expose a new part in the editor by overwriting a spare entry; superseded by ShipworksExtended [guide].
* ShipworksExtended reads `Modloader/config/Shipworks.json` (lists `Hulls Armors Fuels Ammos Legs Engines Guns Sensors Expendables Crafts Defences
  Generators Quarters Emergency` plus `LoadVanilla...` flags; created after the first run) and loads extra parts.seria entries into the palette. [game]
* Parts that need "resources" (hull, fuel, armor) appear in campaign shops as generic `ITEM_HULL/ITEM_ARMOR/ITEM_FUEL`; whether a built-from-resources part
  shows up in campaign depends on the ship's combat value [guide, comment].

## Ship files (`Ships/`, `Objects/Designs/`) [guide]
Root `Node` with `m_name`; `m_children=31` Frame (all hull modules, first child = bridge `MDL_COMBRIDGE_01`); loose `m_children=15` (guns, legs, engines);
`m_joints=8589934595`; one `m_children=47` **Creature** with global stats (`m_ship_name`, `m_playable`, `m_flagship`, `m_combatvalue`, `m_card_*`, `m_card_snapshot`).
Guns/sensors carry 360 `m_sectors`. Global stats are cosmetic/spawn data: change module stats instead. Vanilla ships live in `Objects/Designs` and cannot
be overwritten from the game; to replace one, copy its `m_name`, `m_card_caption`, `m_ship_name` (and optionally `m_combatvalue`, snapshot).
**Recompute trick:** lowering `CORE_LAST_LOADED_VERSION` in `Config.ini` makes the game, on next start, rewrite everything in `Ships/` (old copies go to `Ships_backup/`),
recomputing arcs, sensor arcs, global stats, mass/density and elevation. It does not pull new values from `parts.seria` (that needs a script; see rebalance repo).

## Save files (`Saves/Profile_N/profile.seria`) [guide + game]
* Parts of every ship are full Body records, so any per-part field persists. Back up before editing.
* Root: `m_scores` (starting cash), `m_unlocks=Ship|0/1`, `m_countdown` (days to the darkness event), `m_char_*` (player personality stats).
* Enemy groups: `m_escadras=327` nodes; a ship never touched since spawn is stored compactly (bridge only), so ships are easy to swap; `m_intels=515` holds the
  intel entries (callsign, position). Cities: `m_locations=199` (`m_codename`, position, `m_fuel(_capacity)`, `m_discontent`, `m_aad`, `m_discovered`), `m_items=...`
  (ammo: `m_index`, `m_count`), `m_world_trade=7` (shop parts; generated only after the first visit).
* Characters: `m_npcs` entries; tarkhans have a capitalised `m_name`, generics integer names; `m_joined`, `m_loyalty` (3 points = a star), `m_char_*` / `m_arch_*`
  personality ints in -2..2, `m_ship_first`, `m_location`. Player morale: `m_moral`, `m_rest`, `m_promotions` (8 perks), `m_xp` (in the player's Creature).

## Language packs (`Data/Dialogs/english.seria_enc` cp1252, `russian.seria_enc` cp1251) [game]
* XOR stream cipher (MSVC `rand` LCG, seed 2531011, step 214013, `byte ^= (b>>15)^b`); tool `hfcrypt.py`, same as stopnoanime/highfleet-dialog.
  Decoded text: `#KEY<TAB>text`, entries split at `#`, newlines ignored. The Russian pack is the one that matters for the owner.
* Part: `#MDL_x` name, `#MDL_x_SDESC` type label, `#MDL_x_DESC` description, `#MDL_x_KEY` launch hint (some). Ship: `#SHIP_NAME_<NAME>`, `#SHIP_DESC_<NAME>` (name upper case).
* Dialogue and events are in the same pack; see `content.md`.

## Resources and textures (`Media/`) [game]
* `Media/media.res` is a text index of `Include Media/Tex/X.res` lines. A `.res` declares `Texture name { filename = ...png  resgroup = 0 }` and
  `Animation name { texture  rect = x,y,w,h  hotspot  zorder  resgroup  frames }`: a named rectangle of a 4096x4096 RGBA PNG atlas.
  `Tex_Extra/Extra.res` is a small pack of loose textures. Sounds are `Media/Snd` (wav/ogg), `*.psi` particle files in `Prt`.
* Animation names are used by parts, icons (`Static*.res`), dialogue (`{animation=...}`), UI.
* The `.res` language is stock **HGE** (see `engine-hge.md`; particles `*.psi` = 128-byte HGE structs, fonts `*.fnt` = `[HGEFONT]` text) (open source: github.com/masonm12/HGE, `src/helpers/parser.cpp`, `resources.cpp`) [code]: resource kinds `Include Resource Texture Sound Music Stream Target Sprite Animation Font
  Particle Distortion StringTable`; properties `filename resgroup mipmap amplify size zbuffer texture rect hotspot blendmode color zorder flip scale proportion rotation frames fps mode tracking spacing sprite mesh`;
  `;` starts a comment; `Name : BaseName { ... }` derives a resource from an earlier one; `Include <path>` loads another script (path through the engine's file loader, recursive, an already loaded script is skipped).
  **A name already defined for the same resource type is rejected** ("already has been defined"; the first definition wins), so new art needs new names, and overriding a vanilla name means editing the original.
  Parse errors are written to the engine log (`hge.log` in the game folder). [game] The vanilla `media.res` lists **196** includes of which only **45 exist** (`Static1-9`, `Hall1-8`, `Background1-6`, `Mapmode1-7`, ...); each missing one is logged as
  "Script ... not found" and skipped. Vanilla scripts also log duplicate names (`Mapmode3.res`, `Media/Snd/sound.res`) and a syntax error (`Ships1.res` line 3238) and the game runs fine: an
  extra `Include` line is safe and a mistake in a new `.res` should only cost log lines. Sounds use the same language in `Media/Snd/sound.res`. `texasm` (in the HGE tools) packs sprites into an atlas and writes the `.res`.

## Levels (`Data/Levels/*.seria`) [game + guide]
Empty shells: `LVL_SCRIPT=SCR_*`, `LVL_HIGH/LOW` (arena size), `LVL_WIND_FORCE`, `LVL_BACKGROUND`. All logic is in code (no script files). Known: `Map`, `City`, `Missile`
(missile defence), `Bombers` (air raid), `CraftsVsMissile`, `CraftsVsCrafts`, `Combat`, `Editor`, `EditorExtended`, `Dungeon`, `Builder`, `Title`, `Hall`, ...
Arena size can be edited; new levels cannot be added, but a level file can be swapped under another name (e.g. `EditorExtended.seria` as `Editor.seria`: extended editor
that places non-part sprites and ships) [guide].
1.163 adds skirmish and PVP levels (`EditorSkirmish`, `PreselectSkirmish`, `PreselectSkirmishPVP`, `CombatSkirmish`, `CombatSkirmishPVP`, `City_generatedSkirmish`, with scripts `SCR_*_SKIRMISH*`, `SCR_ED_RUN`, `SCR_DUNGEON`, `SCR_EMPTY`, `SCR_START`, `SCR_TITLE`) and a separate save directory `SavesSkirmish/Profile_1..3`; the list above is for the campaign. Details: [version-differences.md](version-differences.md). The map code starts `Missile`, `Bombers`, `Combat` from the fleet update and `CraftsVsMissile`/`CraftsVsCrafts` from the map aircraft group update ([findings/map-air-groups.md](findings/map-air-groups.md)).

## `Config.ini`
Keys and an extended list of optional ones: `ref/config-ini.md`.

## Save root field names from the 1.151 `Profile` struct (hints for the keys above) [code struct; key pairing is a guess]
The save file `Saves/Profile_N/profile.seria` serialises the `Profile` object (1,380 bytes in both Ghidra programs; vectors moved by +0x48 in 1.163, see the Profile remap, and scalar offsets past
`0x1e0` are probably shifted too, so the offsets below are 1.151 values). the list above lists the keys by observation; the field names below are logdot's and can help decide which key is which.

| Profile field (1.151 offset) | Likely save key (`formats.md`) |
|---|---|
| `countdown` `0x140`, `days` `0x144`, `daysFromEvent` `0x148` | `m_countdown` (days to the darkness event) |
| `enemyValue` `0x180`, `score` `0x184`, `scoreExpedition` `0x188`, `scoreMilitary` `0x18c`, `scoreSurvivors` `0x190` | the score counters (`m_scores` is the **starting cash** per the notes; here `cash` is a separate int at `0x260`; check which one the key is) |
| `escadras` `0x1b0`, `locations` `0x1c0`, `Missiles` `0x1e0`, `explosions` `0x1f0`, `designs` `0x210`, `mapCrafts` `0x228`, `mapMarks` `0x258`, `npcs` `0x268`, `items` `0x278` | `m_escadras`, `m_locations`, ... (the vectors) |
| `cash` `0x260`, `npcIndex` `0x264` | cash and the next-NPC counter |
| `reinforcementState` `0x28c`, `endRace` `0x290`, `endWar` `0x291`, `endStrike` `0x292`, `escalation` `0x294`, `flagshipLost` `0x298`, `burnFuel` `0x299`, `rams` `0x29c` | campaign state flags; **`endWar`/`escalation` are set by `spawnEndgameShips_`** (findings/end-game.md) |
| `alert` `0x2a0`, `alertHr` `0x2a4`, `radioDuration` `0x2ac`, `radioDurationBase` `0x2b0` | alert level and radio timing |
| `enigmaSet1..4` `0x2b8..`, `enigmaKey1..12` `0x2c8..`, `enigmaGot1..12` `0x2f8..`, `enigmaTimer` `0x304` | the Enigma puzzle (12 keys, 12 "got" flags, a timer) |
| `tadsRecord` `0x308`, `intelData` `0x30c`, `ant` `0x310` | TADS record, intel counter, a flag named `ant` (`restOfEventsPrologueAntIsaiah` is the prologue event handler) |
| `charFear`, `charGerat`, `charRomani`, `charFaith`, `charRight`, `charForce`, `charWealth`, `charKindness` (ints `0x314..`) and the same eight `...Val` floats (`0x334..`) | `m_char_*`: the **eight player personality stats** (Fear, Gerat, Romani, Faith, Right, Force, Wealth, Kindness) as integer level and float value |
| `nextCreatureId` `0x358`, `nextHistoryDesign` `0x360` | id counters for new ships and saved designs |
| `trigger` `0x398`, `unlocks` `0x3d8`, `strigger` `0x418`, `events` `0x458`, `arguments` `0x498`, `demoState` `0x4b0`, `demoLoot` `0x4b8`, `inventory???` `0x4d8` | the string/number trigger tables (`CreateTriggerVal` reads these; `TUTORIAL_*`, `ESCALTION_WARNING` live here), unlocks, events |
| `mapSkyOffsetX/Y` `0x520/0x524`, `mapSkySteps`, `mapSkySeed`, `gameVersion` `0x548` | map sky, game version (written into the save) |

* **`Profile.gameVersion` (float at `0x548` in 1.151)** is what the version check `CORE_LAST_LOADED_VERSION` in `Config.ini` interacts with; the game version is also reachable through `GetGameVersionString` (`0x1401fa190`).
* The trigger tables are keyed by name: `CreateTriggerVal(&Profile+0x3f0, ...)` returns a reference to a named value (as seen in the tutorial code and in `ESCALTION_WARNING`). For save editing, these named
  values are the "flags" (tutorial progress, warnings) that a save editor may want to reset.
