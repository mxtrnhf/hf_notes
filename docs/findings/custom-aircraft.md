# Custom aircraft: what a new plane needs, and how hf_ally follows it (2026-10-25)

Source: the new "Flight to Hara Vera" 2.0 installer (build 2026-08-30), unpacked statically on 2026-10-25 into `hf_mods_unpack/hara_vera_new/extracted/` (method: `ref/total-conversion-hara-vera.md`), its plane `CRAFT_SB15` (the SB-15 bomber), and a test install of that plane into the game folder the same day. [verified from the files; the game run is the user's test, see "Open"]

## The game has two crafts; everything else is added by data plus the qol mod
Vanilla has `CRAFT_T7` and `CRAFT_LA29` only, hardcoded in `LoadPlaneLoadouts` (`findings/carrier-plane-loadouts.md` section 14). A third plane is therefore not a game feature: it is five pieces, all of them files, none of them code:

| # | Piece | File | What SB-15 has |
|---|---|---|---|
| 1 | Part body | `Libraries/parts.seria` | a `Body` with `m_oid=CRAFT_SB15`, `m_logic=500`, `m_slot_type=2053`, six hangar `Slot`s, `m_health` 150, `m_sprites` -> `m_animation_name=sb15` (scale 0.75, angle 1.5708) |
| 2 | Stats | `Libraries/OL.seria` | a `Stats` record: price 3500, category 1024, crew 15, ammo boxes 3, `m_icon_name=CRAFT_SB15`, launch speed 300 / range 8000 |
| 3 | Textures | `Media/Tex/*.res` + PNG | three `Animation` names (below) |
| 4 | Loadouts and health | `Modloader/config/qol.json` `planes` (qol mod) | key `CRAFT_SB15`, `health` 70, four loadouts |
| 5 | Where to get it | qol `shop_parts` (campaign shops) or `Shipworks.json` "Crafts" (ShipworksExtended, Shipworks test palette) | FTHV: both, shop rule 50 % / 1-5 / merchant city (type 3) |

Plus the names: `CRAFT_SB15`, `_SDESC`, `_DESC` in `Data/Dialogs/<lang>.seria_enc` (FTHV: "SB-15", "BOMBER", "A dedicated long-range bomber. Has no air-to-air capabilities."). Without them the part shows its raw key.

**qol `planes` really adds crafts.** `patch_planes` (qol `src/plane.rs`) builds new `PLANE_LOADOUTS` and `PLANE_TLL` containers from the config and `ptr::write`s them over the game's two maps, so any key in `planes` becomes a craft, and any loadout in a craft's list is armable. The craft's body (pieces 1-3) must exist as game data; the config only registers loadouts and health. ShipworksExtended does NOT add crafts, it only puts parts into the Shipworks editor palette (`DefinePart` into `EDITOR_LIBRARY_CRAFTS`); qol's `shop_parts` does the same for city shops. For a campaign test the shop rule is enough, so ShipworksExtended is not needed (FTHV ships it only for its Shipworks palette).

## Textures: `parts.seria` has no pixels
`m_animation_name` is a name. `Media/media.res` is a list of `Include` lines (its first line is `Include Media/Tex_Extra/Extra.res`, a file the game ships for extras); each `.res` defines `Texture <name> { filename resgroup }` and `Animation <name> { texture rect bump hotspot zorder resgroup frames }`. A plane needs three names, **all new**:

| Animation | Use | SB-15 | T-7 for comparison |
|---|---|---|---|
| `sb15` | the in-battle / in-ship sprite (what `parts.seria` points at) | 300x300, `frames = 3`, `bump` (normal map) | `t7`: 100x100, 81 frames (rotation) |
| `CRAFT_SB15` | 98x98 icon (shop, editor), also the `m_icon_name` | one frame | `CRAFT_T7` |
| `CRAFT_SB15_big` | 146x108 picture | one frame | `CRAFT_T7_big` |

`rect` is the first frame; `bump` is the first frame of the normal-map copy. Frames follow to the right, and when a row runs out of atlas width they continue on the next row: the HGE source (`hge_src/src/helpers/hgeanim.cpp` `SetFrame`) wraps to x = 0 of the next frame row, but FTHV's art for the wrapped frame sits at the *rect's own x* (3375), not at 0, so **the game's real rule is not proven**. The safe way to add a plane is to copy the sprite block with identical x offsets and the same atlas width (4096): then both rules read the same pixels as FTHV. FTHV's frame 0 slot is empty, slots 1 and 2 hold the bomber (gear down, gear up), slot 3 holds a stray "OLD NORMALMAP" scrap; which frame the engine shows is not known (SB-15 is drawn with `m_animation_mode=4`, `m_animation_speed=0`).

FTHV painted these into its own copies of the big vanilla atlases (`Ships1.png`, `Static2.png`, `Static4.png`: it overwrites vanilla art). The test install does not: it ships `Media/Tex_Extra/SB15.png` (4096x2048, the SB-15 block copied from FTHV's `Ships1.png` at the same x, y shifted up by 2560; icons beside) and appends one `Texture SB15Tex` plus the three `Animation`s to `Media/Tex_Extra/Extra.res` (vanilla includes it already, so `media.res` is untouched). rects: `sb15` 3375,62,300,300 bump 3375,664; `CRAFT_SB15` 3,1500,98,98; `CRAFT_SB15_big` 110,1500,146,108.

**Another mod's plane copies nothing from another plane except by name:** a body may point at any existing animation (the old FTHV 2.0.1 pointed `CRAFT_MB110` at `t7`), so a plane without art can borrow `t7` or `la29` and only needs pieces 1, 2, 4.

## Behaviour: planes share one flight code, keyed by the loadout's parts
There is no per-craft behaviour. `0x14002e930` arms a plane from `PLANE_LOADOUTS[plane+0x3f8]` and dispatches each part by the **class of its ammo record** (`reticle`: 2 bombs, 3 rockets, 4 gun, 5 K-13), never by craft or item name. So a new bomber with bombs flies the bomber code and one with rockets the rocket code. Consequences found in SB-15's data:
* its `ROCKET` loadout uses `ITEM_AMMO_300MM_INC` (ammo class 3, a rocket, from the game's own ammo list: `Modloader/probe_ammo_raw.txt` entry 28, `0x2bf75c0`), which has no `FAB`/`NAR` in the name: classify by class, not by name;
* it has **no parts-free loadout** (no `GUN37`): there is no "guns only" loadout to write. An unknown loadout name arms the plain 37 mm gun (section 14.4 of the carrier note), so hf_ally uses a name the game does not know for "guns only" on such a craft;
* the loadout table must stay valid: a part name that is not in the ammo list has an undefined class.
`ITEM_AMMO_300MM_INC` is in the vanilla ammo list, so FTHV's `ammo_extended.dll` (which re-tunes every shell) is not a dependency of the plane.

## How hf_ally follows it (commit `bd5e647`, on top of `a6b0f61`)
`ally/src/plane_loadouts.rs` reads, once and lazily, from the live maps: the craft keys of `PLANE_TLL` (vanilla T-7 and LA-29 first, then others, at most `MAX_CRAFTS` = 4), each craft's loadout pointer vector (parts name / count at stride 0x28), and the ammo list (`0x143a13be0`, records of 0x188, class = first int, name string at +8). Falls back to the vanilla table when the maps cannot be read. `ally/src/lib.rs`: 36 button slots (`PLANE_ARM_1..36`, craft * 9 + card), click range 1..=36, and the button *places* go by the ship's own craft types: first type under ALLY, second beside it (both as before), a third and fourth in the next row / under (places 3 and 4 are guesses at free screen space). Label = craft key without `CRAFT_` with a dash before the digits (`SB-15`).

## Install recipe used (reversible; backups in `hf_game_backups/sb15_2026-10-25/`)
1. `parts.seria`: cut the `CRAFT_SB15` Body out of FTHV's file by brace matching, set its `m_master_id` to the vanilla root node id (`3086509121060961972`, the one `CRAFT_T7` has; FTHV's id `6762...` does not exist in vanilla), insert it after the `CRAFT_T7` body. Its own `m_id` and the slots' `m_master.id` (`2755763200865657213`) do not collide with any vanilla id. CRLF and the latin-1 bytes kept. Result: 116 lines added, none removed.
2. `OL.seria`: insert the `CRAFT_SB15` Stats record after `CRAFT_T7` (20 lines). `OL_peace.seria` untouched (FTHV did not touch it either).
3. Textures as above.
4. Dialogs: decode both packs with `hf_aa_missile/text/hfcrypt.py` (XOR stream, round-trip verified byte-exact), insert FTHV's three `CRAFT_SB15` entries before `#CRAFT_MB110` in the English and the Russian pack (Russian text is FTHV's cp1251), encode back.
5. `qol.json`: add `planes.CRAFT_SB15` (FTHV's, health 70 and its four loadouts; its `ROCKET` icon `LOADOUT_KH2` and the other icons exist in vanilla `Static8.res`), set `enable_shop_parts` true and `shop_parts.CRAFT_SB15` = probability 1.0, 1-3 pieces, every city type (a test setting; FTHV: 0.5, 1-5, merchant city only). Nothing else of FTHV's `qol.json` taken (its T-7 `NURS340` count 1 differs from vanilla 2).
6. hf_ally: the new DLL replaces `hf_ally_v0.13.1.dll` (old one kept as `Modloader/hf_ally_v0.13.1.dll.bak_pre-custom-planes`).
**Uninstall:** restore the five files from the backup folder (`Libraries/parts.seria`, `OL.seria`, `Media/Tex_Extra/Extra.res`, `Data/Dialogs/*.seria_enc`, `Modloader/config/qol.json`), delete `Media/Tex_Extra/SB15.png`. **Steam "verify files" reverts parts.seria, OL.seria, Extra.res and the dialogs** (but not `qol.json` or the PNG): the plane then disappears from the part libraries while `qol.json` still lists it. **A save with an SB-15 on a ship needs the part present**; removing the part from the libraries with such a save is untested and probably breaks the ship (do not test on a campaign save you care about).
ShipworksExtended was NOT installed. If it is wanted for the Shipworks palette: use upstream v1.1.3 (2026-04-08, "fixes a crash when using Proton on linux"; the FTHV copy is an older build, 130048 vs 131072 bytes) and a minimal `Shipworks.json` (`LoadVanilla` true, every list empty, `Crafts: ["CRAFT_SB15"]`); FTHV's own `Shipworks.json` names FTHV-only parts (`MDL_FUEL_03`, `MDL_BARELEG_*`, `MDL_ENGINE_NERVA`, the new cannons) and a bad oid crashes the Shipworks. Its patch site `0x1400d0add` cannot be checked against `Highfleet.exe` on disk: the file's `.text` is encrypted (the known `0x14002e930` also reads as garbage on disk).

## Open
* Not run in game yet. To check: SB-15 shows in a city shop (`Highfleet_<date>.log`: `[highfleet_qol] ... shop`), with its icon and name; it can be placed on a ship and shows its sprite (frame 0 may be blank: see textures); `hf_ally` log line `PLANE table read: crafts [...]` lists `CRAFT_SB15` and four armaments with `ROCKET` as `Rockets`; the SB-15 button appears on the pre-combat card of a ship carrying it.
* Which frame of `sb15` the engine draws, and the real frame-wrap rule.
* What `shop_parts` does for a part from the aircraft category: it injects into the weapons category's shop generation (`parts.rs` hook `0x1402bcd49`).
* Places 3 and 4 of the plane buttons.
