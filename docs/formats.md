# File formats

Tags: **[game]** verified here, **[guide]** from the community modding guide (see `ref/community-guides.md`, unverified here).

## `.seria` (parts, ships, saves, levels, config)
* Nested nodes `header=number` + `{` ... `}`; braces alone on their own line; **never indent** (breaks the file). Defaults are omitted.
* A node holds `attr=value` pairs, nested nodes, or (meshes) bare floats. Repeated `attr=value` lines form an array (e.g. 360 `m_sectors` = one per degree).
* The numeric header is the class code (`m_code`): 15 Body, 31 Frame, 47 Creature, 7 Node, 199 location, 327 escadra, 515 intel (see `structures.md`).
* Serializer `FUN_14004f010`, Body field loader `FUN_140025240`.

## Part libraries (`Libraries/`)
* `OL.seria`: `m_stats=2051` records, one per part id `m_oid`: price, category, crew/power/ammo needs, weapon and missile stats
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
* The `.res` language is stock **HGE** (open source: github.com/masonm12/HGE, `src/helpers/parser.cpp`, `resources.cpp`) [code]: resource kinds `Include Resource Texture Sound Music Stream Target Sprite Animation Font
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

## `Config.ini`
Keys and an extended list of optional ones: `ref/config-ini.md`.
