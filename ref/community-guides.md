# Community guides and prior art (summaries)

Our own short summaries; the originals are third-party. The Steam guide PDF is kept locally in `ref/` and is **not committed**.

## "The Ultimate HighFleet Modding Guide" (Dwang Zhongson, updated 23.11.2023; versions 1.151 and 1.163)
https://steamcommunity.com/sharedfiles/filedetails/?id=2768442721 · covers: `.seria` structure (never indent), `OL.seria` and `parts.seria` fields, the `m_category` bit table,
mass formula, ship and save file structure (strike groups, cities, tarkhans, morale), localization entries and event rewards, making new parts (old `constructor.seria` method),
ship replacement and updating (the `CORE_LAST_LOADED_VERSION` trick), modding tools, the ModLoader mods (ShipworksExtended, ammo-extended), levels and hidden levels.
Facts we use are merged into `../docs/formats.md` and `../docs/structures.md` and tagged **[guide]**. "Planned" but never written: **Events** (expand/branch/trigger) and **Textures**
(.res structure, adding a new texture file for a new part, side-specific camos), plus Cheat Engine. Its comments mention that a built-from-resources part appears in campaign depending
on the ship's combat value.

## "Dialogue (and now Character) Modification" (Loregamorl, 2021-22; removed from Steam but readable)
https://steamcommunity.com/sharedfiles/filedetails/?id=2676978688 · decode `Data/Dialogs/*.seria_enc` with stopnoanime/highfleet-dialog, edit, re-encode. Syntax tested: `<ANS=text|LABEL>`, `#LABEL`,
`<NPC=PETR>`, `<SIDE=1>` (left), `|EXIT` works on answer lines only. Portraits are PNG atlases in `Media/Tex`; each sheet has a `.res` with `rect = x,y,w,h` per sprite
(example `PETR_S` in `Static7`, a comment by Degen). Replacing a portrait works; adding characters/events is not covered.

## Others
* "Making Wheels Available in Ship Editor" (WarStalkeR, 2021, removed): appends a wheel body to `Libraries/constructor.seria` (side effect: the Emergency Modules icon disappears).
* "A hidden extended editor in the game" (Dwang Zhongson, screenshot): `EditorExtended` level swapped in as `Editor.seria`; no activation details on the page.
* Nexus: Total Rebalance (mods/5), another mod (mods/22). Discord post "A220 Man, Cruiser Fodder" is the source of the `m_category` bit table.

## Code repos
* **vladyorsh/highfleet_total_rebalance**: data-only rebalance (edited libraries, redesigned ships in `Objects/Designs`, edited dialogue packs with new ship entries, submods such as
  "Revert to Vanilla") plus Python tools: `updater.py` (recompute a ship's stats after the part library changed, using the vanilla OL as reference), `sg_editor.py` + `sg_config.py`
  (rewrite enemy strike-group fleets in a save: per group a list of `ShipEntry([names], difficulties, spawn_chance)`), `renamer.py`, and `ModTool` (a GUI shipped as a 49 MB `modtool.exe`:
  never run here). Precedent for the data pipeline, save rewriting, and "a ship must be re-saved after a part changes".
* **logdot/Highfleet-Modloader** (4.1.0), **ShipworksExtended**, **highfleet-qol** (shops, gun arcs), **ammo-extended** (shell params: `padding_cch` = caliber index used in `OL.seria`,
  `speed`, `ap_drag`, `explosive_power`, `penetrative_power`, `incendiary_power`, `shop_price`, spawn chance/amount, fire delay; `caliber` behaviour 100 normal / 90 bounce / 160 proximity /
  180 directional proximity), **stopnoanime/highfleet-dialog** (language-pack tool), **masonm12/HGE** (the engine, source), and mxtrnhf's forks `ShipworksExtendedProtonFix` and `highfleet-dialog-backup`.
