# Carrier plane loadouts: where they are picked, stock, hook candidates (1.163)

Read-only analysis of the image, 2026-10-24, nothing run in game. Tags: [code] = read in decompile/disassembly, [guess] = inferred.
Request: ally-mod-continue wants a pre-combat button that forces the LOADOUT_* of the player's carrier planes.

## 0. Short answers

1. **A plane's loadout is just a name**: an EscadraString (0x20 bytes, MSVC-style SSO string) at **plane creature `+0x3f8`**. It is looked up in `PLANE_LOADOUTS` (std::map<EscadraString, Loadout>, header at `0x143a15a60`) every time it is used. Writing a different valid `LOADOUT_*` name there is the whole override. [code]
2. **Launching a plane in battle is free.** No function on the launch / re-arm path touches an inventory. Items are only moved by the strategic-map `LOADOUT_LIST` click (section 3). [code, absence of access in the three functions below; a full xref sweep of inventory writers was not done]
3. **Inventory** = std::map<EscadraString, int> at **`Profile + 0x540`** (value int at map-node `+0x40`). Profile pointer comes from `FUN_140292ab0(BOOL_147fc6f80, DAT_147fc6f81)` or `Get_Profile()` `0x140292a90`. [code]
4. **The weighted random pick (`launch_loadout_weight`) is NOT in the battle launch.** It is only in the AI *map* air-group builder `TryLaunchAiAircraftGroup` `0x1400ef910`. In battle the AI has a different, uniform random re-pick (section 2). The player never gets a random pick.

## 1. Data structures

* `PLANE_TLL` `0x143a13c50`: map CRAFT_* -> Plane. Node: key at `+0x20`, value at `+0x40`. Plane value = `{ u64 cached_weight_sum @+0x40 (lazily summed; qol calls it _padding), CVec<Loadout*> @+0x48..+0x50 }`. [code: TryLaunchAiAircraftGroup sums `loadout+0x58` into node `+0x40` when 0]
* `PLANE_LOADOUTS` `0x143a15a60`: map LOADOUT_* -> Loadout (node 0xa0 bytes). Loadout fields as in qol `GameLoadout`: `+0x20` key; parts vector at node `+0x80..+0x88` (stride 0x28: name EscadraString, `count` int at `+0x20`); weight at loadout `+0x58`; **`has_gun37mm` byte at node `+0x9c`** (qol reads it as the loadout's gun flag). [code]
* Part classes via `filterAmmos(name)` -> first int: **2 and 3 = bombs / unguided rockets (bomber role)**, 4 = gun, 5 = missile-like (K13 class). `loadAmmoForAircraft` calls: 2 -> `FUN_140007aa0(logic,name,count)`, 3 -> `FUN_140007bd0`, 4 -> `configure_plane_gun`, 5 -> `FUN_140007970`. [code]
* Plane creature: `+0x3f8` loadout name, `+0xa20` its `AircraftLogic*` (0x1b0 bytes, built by `AircraftLogic()` ctor), `+0x100` of a *carrier* = list head of its plane creatures (node `+0x10` = plane). Logic fields: `+0x120` list of ints (ammo index per bomb/rocket, type 2), `+0x130` list (type 3), `+0x1a4` gun ammo index, `+0xac/+0xb4` gun counts. [code]
* `+0xad4` side float: negative = enemy AI (existing notes).

## 2. Where a plane gets its loadout (battle)

`loadAmmoForAircraft__` **`0x14002e930`** (rename candidate; Ghidra name `loadAmmoForAircraft??`). Args: RCX plane creature, RDX owner ship (param_2), R8 anchor/parent (param_3), R9 = param_4 (a Vec2 passed by value; 5th stack arg float). Steps [code]:

1. `+0x3cc = 1`, creates the AircraftLogic if `plane+0xa20 == 0`. **All of the loadout work is inside that `if`**: when the plane already owns a logic (a re-used landed plane), the existing logic/ammo is kept.
2. Campaign only (`BOOL_147fc6f80`), owner `+0xad4 < 0` (enemy), and profile difficulty field `> 5`: with chance `(diff-5)/20` the plane's name `+0x3f8` is **overwritten by a uniformly random loadout of its CRAFT** (index via `HGE vtable+0x108`, range 0..n-1; no weights). This is the only battle-time random pick, and it is AI-only. The CRAFT entry is found by `compData(&PLANE_TLL, ..., plane+0x190)`: **the CRAFT name is the string at plane `+0x190`**. [code]
3. Looks up `plane+0x3f8` in `PLANE_LOADOUTS`. Not found -> falls back to just `ITEM_GUN37`. Found -> if `BOOL_147fc6f80 || DAT_147fc6f81 || has_gun37mm` adds ITEM_GUN37, then walks the parts and calls the four setters above.

So **the override hook for the player's planes is a write to `plane+0x3f8` before step 3**, and it must not be applied when `owner+0xad4 < 0`.

Callers of `0x14002e930`:

| site | role |
|---|---|
| `0x1402679c8` in `rep_140245ab0_New` (`0x140267700`) | spawns a *group* of planes; **only the plane-vs-plane scenarios** (`FUN_1402cf4d0` = level seria `SCR_CRAFTS_VS_CRAFTS`, variant `DAT_147fc6fc4 == 1`, call at `0x1402c58ed`; `FUN_1402ca2b0` = another scripted scenario, call at `0x1402c5540`). **Not the normal carrier battle** (corrected 2026-10-24, see section 7). |
| `0x14007a658` in `FUN_14007a4c0` | **the player's launch**: `Input_KeyUp` `0x14018a530` calls it at `0x14018a815` (RDI = the controlled ship; gates: byte `0x147fc6fb7 != 0`, byte `0x143a11909 == 0`), also `SomethingWithLevelSerias` `0x1402c492d`. Picks one plane from the carrier's vector, frees its old logic, calls `0x14002e930` |
| `0x140065bd9` in `AiShipTick` | AI carrier launch |

(Earlier text here claimed `FUN_1402cf4d0` is the battle-start setup; wrong, it is the plane-vs-plane scenario. It reads `plane+0x3f8` only to classify bomber/fighter there.)

### Re-arm on landing (free)

`FUN_14000ebb0(logic, newState)` `0x14000ebb0` is the aircraft state machine setter (STATE_ATTACK 3, TO_ATTACK_POINT 2, RETIREMENT 1, RETIREMENT_AFTER_ATTACK 4, TO_OUT_OF_SCREEN 5, DESACTIVATED 7; 6 = returned). On state 6, campaign, with empty bomb lists (`logic+0x128 == 0 && +0x138 == 0`) it re-reads `plane+0x3f8` from `PLANE_LOADOUTS` and refills type-2/3 parts from the loadout. No inventory access. [code] Hence a changed `+0x3f8` also changes the next re-arm.

### AI map air groups (weighted pick, do not touch)

`TryLaunchAiAircraftGroup` `0x1400ef910`: picks per-plane `rand(1, weight_sum)` and walks the loadout vector subtracting `loadout+0x58` (`HGE vtable+0x108`), producing `(CRAFT name, LOADOUT name)` string pairs, then `CreateMapAircraftGroup` `0x14010f8e0`. Enemy only (reads fleet `+0x4ec` plane count, cooldown `+0x510`).

## 3. Inventory and the existing LOADOUT_LIST UI

* Inventory map: `Profile+0x540` (std::map<EscadraString,int>). A second map at `+0x550` accumulates "in use" counts. A vector at `+0x560` holds the pair list (CRAFT, LOADOUT), element size 0x40 (two 0x20 strings). `Profile+0x530` / `+0x538` are pointers to the currently selected craft GUI button and selected ship. [code: ClickFunc and `FUN_1402a9090`]
* Counting a loadout: `FUN_1402a9090(profile)` `0x1402a9090` already does it: for every plane button in `profile+0x538 -> +0x100` list it computes `min over parts of inv[part] / part.count` and stores it at button `+0x7a8`, with `+0x7a4 = loadout has parts`. **Reuse that formula for the grey-out:** `available = min(inv[item] / count)`. A part name missing in the map is created with 0 by operator[] in the game, in your code treat missing as 0.
* Single read of an item: lookup `Profile+0x540` map by name (map header at `*(profile+0x540)`; sentinel `+0x19` byte; node key at `+0x20`; `EscadraString` compare `compareEscadraString` `0x140009920`; value int at node `+0x40`). The game's own operator[] helper is `0x14002dda0(map*, out, key*)`. [code]
* **`ClickFunc` (`0x14012f120`) handler**, `Frame+0xa40 == "LOADOUT_LIST"`, site `0x14012fa08..0x14012fc48` (loads `PLANE_LOADOUTS` at `0x14012fa26`): the clicked button's name (`button+0x190`) is the loadout. It checks every part `inv[part] >= count` (bail if any is short), then `inv[part] -= count; used[part] += count`, then `inv[craft]-- ; used[craft]++` for the craft name in the selected button (`profile+0x530 -> +0x190`) [the two craft updates are read from the disassembly; the exact map each is applied to I could not fully separate, [guess]: CRAFT_* stock lives in the same inventory map], appends the (craft, loadout) pair to `profile+0x560`, calls `FUN_1402a9090` and `FUN_1401c4ee0`. [code]
* `FUN_1401c4ee0` `0x1401c4ee0` builds the `MISSILE_MARK` map marker (carrier air-strike target) and its tooltip from the `+0x560` pairs: bombers (part class 2/3) with `sign_bomb`, others with `sign_fighter_mini`. **This UI belongs to the strategic air-strike plan, not to the pre-combat battle plan.** I did not establish how the pair list is turned into spawned planes; that is the open link between this UI and the battle launch.

## 4. Carrier / plane type identification

* Plane creature: CRAFT name = EscadraString at **`+0x190`**; loadout name = `+0x3f8`. [code]
* Carrier = a ship creature whose `+0x100` plane list is non-empty (`FUN_1402cf4d0` iterates exactly that; entries with `plane+0x48 != 0`, i.e. alive). The code also writes the ship's index in the ship vector into an int field of each plane (offset not verified). Carrier's landed/spare planes: vector `ship+0x14c8..+0x14d0`.
* To list the loadouts for a carrier in the UI: for each plane, `PLANE_TLL[plane+0x190].loadouts` (CVec at Plane `+0x8`), as qol already does.

## 5. Hook candidates

| use | address | note |
|---|---|---|
| force loadout for player planes (preferred) | entry of `loadAmmoForAircraft__` `0x14002e930` | `plane` = RCX, owner = RDX; skip when `*(float*)(owner+0xad4) < 0`; write a copy of the chosen name into `plane+0x3f8` (EscadraString: replace via the game's own string copy (`rep_14009dec0_CopyString`, as the function itself does at its step 2), do not memcpy over an SSO/heap string) |
| (retracted) `FUN_1402cf4d0` | only the CRAFTS_VS_CRAFTS scenario, irrelevant for carrier battles | |
| re-arm | `0x14000edec` area in `FUN_14000ebb0` (reads `BOOL_147fc6f80`, then `plane+0x3f8` at `0x14000ee1f`) | automatic once `+0x3f8` is changed |
| greying | read `Profile+0x540` as above, or call `0x1402a9090` equivalent | no hook needed |
| consume items [if wanted] | there is none in battle; mimic ClickFunc `0x14012fb0b..0x14012fb80` (`inv[part] -= count; used[part] += count`) | |

## 6. Not established

* Where the player's carrier planes get their *initial* `+0x3f8` (saved with the creature, `SerializeHeader` `0x1400510f7` touches `+0x3f8`; Shipworks default not found).
* How the `profile+0x560` pair list reaches the battle launch.
* Whether any other code decrements `Profile+0x540` (no full xref sweep).
* The offset of the ship-index field in section 4.

## 7. Follow-up 2026-10-24: pre-combat card -> ship, planes as parts, consumption, armament list

### What a plane is [code]
A carrier's planes are **parts of the carrier creature with logic id `0x1f4` (500)**. `Creature_AccumulatePartStats` `0x140072790..`: for every part with `+0x3c4 == 0x1f4` it pushes a Link to the part into the carrier vector **`+0x14c8..+0x14d0`** (stride 0x18; Link = `{vtable +0, Node* +8, id +0x10}`, ctor `Link_ConstructFromBody` `0x140194bd0`), adds to a counter at `+0x15f4`, and stores the count in **`+0x17dc`** (`0x140072884`). So the plane stock is the part list of the ship design; there is no separate hangar count. `+0x3f8` / `+0x190` / `+0xa20` are fields of that plane part. The `AircraftLogic` (`+0xa20`) is created lazily by `0x14002e930` at launch; the arming therefore happens **at each launch**, not at battle start [code: `if (plane[0x144]==0) new AircraftLogic`; `FUN_14007a4c0` frees and nulls it before calling].

### Pre-combat card -> ship (per hf_notes `docs/rendering/precombat-screen.md`)
Card `+0xbc0` is a Link to the ship creature (`precombatOk` `0x1402d89c0` matches `node+0x18` against it). Ship creature = `*(Creature**)(card+0xbc0 + 8)`. "Has planes" = `*(u32*)(ship+0x17dc) > 0`, or `*(u64*)(ship+0x14c8) != *(u64*)(ship+0x14d0)` (the test `afterBattleStars` and `shipCardsMainStatsDisp?` `0x14007e271` use). Plane list entry i: `part = *(Part**)(*(u64*)(ship+0x14c8) + i*0x18 + 8)`; craft name = EscadraString at `part+0x190`, loadout name at `part+0x3f8`. Whether the plane parts' `+0x3f8` is already filled at pre-combat (ship loaded from the save) was not verified; `SerializeHeader` `0x1400510f7` (de)serialises it, so it should be. The ship creatures exist at pre-combat: the card list and `shipCardsMainStatsDisp?` read the vectors there [code].

### Which launch paths read the name (all go through `0x14002e930`)
* Player-controlled ship: `Input_KeyUp` -> `FUN_14007a4c0` (one plane per key release).
* AI ships **including allied AI carriers** (side float `+0xad4 > 0`): `AiShipTick` `0x140062f90` -> `0x140065bd9`. A "player side only" filter that tests `owner+0xad4 < 0` still lets allied AI carriers through; if only the controlled ship's planes should change, also compare `owner` with the controlled creature.
* Landing re-arm: `FUN_14000ebb0` state 6 (`BOOL_147fc6f80` campaign only, bomb lists empty): re-reads `plane+0x3f8`; no inventory.

### Consumption
Vanilla never consumes anything for a launch, a re-arm or a crash, and nothing returns items after a battle (`afterBattleStars` only reads the plane vector to choose a sprite) [code, no inventory access found on these paths; no full sweep of `Profile+0x540` writers]. The only vanilla moves are the strategic `LOADOUT_LIST` click (`inv[part] -= count; used[part] += count`, `Profile+0x540` / `+0x550`) [see also `hf_ml/analysis/clickfunc/planes-and-loadouts.md`]. Cleaner point than "each arming": **consume once per (plane part, battle)**: decrement when a plane is armed for the first time in the battle (mark it, e.g. a set of part pointers cleared at battle start) and do not charge landing re-arms (the game re-arms free from the same loadout). Returning the items on leaving the battle has no vanilla analogue; if wanted, the mod must track the set and add back for planes not lost (a plane's alive state: part `+0x48 != 0`, same test `FUN_14007a4c0` uses on its list nodes). This is a design choice, not a game fact.

### Plane armaments (hardcoded table, `LoadPlaneLoadouts` `0x1401af830`, from `hf_ml/analysis/clickfunc/planes-and-loadouts.md` and the live `qol.json` dump)
Loadout -> parts (name x count): T7: `LOADOUT_T7_GUN37` (none), `_FAB100` ITEM_FAB100 x4, `_FAB250` ITEM_FAB250 x2, `_NURS122` ITEM_NAR122 x12, `_NURS340` ITEM_NAR340 x2, `_K13` ITEM_K13 x2; LA29: `_GUN37` (none), `_FAB100` x2, `_FAB250` x1, `_NURS122` x6. Weights 10 (K13 5). So **plane armaments = {ITEM_FAB100, ITEM_FAB250, ITEM_NAR122, ITEM_NAR340, ITEM_K13}**; ITEM_GUN37 is the default gun and needs no stock. For a mod that may add loadouts, derive the set from `PLANE_LOADOUTS` (`+0x80..+0x88` vectors) at runtime. Default fallback loadout = `*_GUN37` (no parts, flag `has_gun37mm`).

### Open
Initial `+0x3f8` content of a fresh plane part (default string from the part definition vs. empty vs. `LOADOUT_*_GUN37`) was not read; if empty, `0x14002e930` falls back to ITEM_GUN37 only. `FUN_14007a4c0` selection criteria (`+0x48`, `+0x888 != 1`, `+0x890`, `+0x820 == 1.0`, `+0x24c == 0`, `+0x259` role byte) are in the decompile but not interpreted.
