# Highfleet 1.163 (Steam): reverse-engineering and modding notes

Single reference for everything learned while building the Highfleet mods in this workspace. Image base
`0x140000000`. Paths are written relative to the game folder (`<game>`) and the work folder (`<work>`).

Status legend: **[game]** confirmed by running the game, **[code]** read from the decompiled code only, **[guess]**
inferred. Function names `FUN_...` are Ghidra's automatic names; named ones come from public work or from us.

## 0. Map of the work

| Repo (in `<work>`) | What it is | State |
|---|---|---|
| `hf_elevation` | `highfleet_elevation.dll`: set the elevation (`m_floor`) of the held part with hotkeys | works [game]; README, LICENSE, CI draft |
| `hf_speed` | `highfleet_speed.dll`: configurable map cruise-speed formula | works [game]; README, LICENSE, CI draft |
| `hf_multicharge` | `highfleet_multicharge.dll`: **multi-charge parts** (S-4 Triumph, A-101) | split from `hf_multimissile`; README, LICENSE, CI |
| `hf_salvo` | `highfleet_salvo.dll`: **map salvo options** (launch delay, grouped defence) | split from `hf_multimissile`; README, LICENSE, CI |
| `hf_multimissile` | the combined repo before the split | archived |
| `hf_refuel` | `highfleet_refuel.dll`: refuel speed multiplier for you and for AI fleets | built, untested in play |
| `hf_aa_missile` | scratch dir of the early Triumph work (backups of the original game files, one-off scripts) | archive, superseded by `hf_multimissile/tools` |
| `hf_notes` | this file | |
| `hf163`, `hf_ghidra`, `hf_server` | the memory dump, Ghidra exports/scripts, the Ghidra project | tooling |
| `hf_qol_src`, `hf_dialog_src` | clones of logdot's highfleet-qol and stopnoanime's highfleet-dialog | reference |
| `Modloader.v4` | logdot's Highfleet-Modloader source | reference |

Installed in the game: Highfleet-Modloader (`bass.dll` proxy), ShipworksExtended, highfleet-qol 1.3.0, plus our three DLLs.

## 1. Environment and tooling

* Game: Steam build 1.163, run under Proton/Wine on Linux; the work also runs on Windows (the DLLs are plain 64-bit
  Windows DLLs). The on-disk `Highfleet.exe` is Steam-DRM packed; **analysis uses a memory dump** of the running process
  (`/proc/<pid>/mem`, raw file offset = RVA), loaded into Ghidra as `Highfleet_1.163_dump.exe` (the old 1.151 program is in the
  same project). Code bytes are identical between dumps, so the addresses below are stable for this build.
* Ghidra with a Ghidra MCP bridge: decompile, xrefs, `search_instructions`, `disassemble_bytes`, `read_memory`. Huge functions
  (e.g. the scenario script `FUN_1402ac970`) time out in the decompiler: read the jump tables with `read_memory` and disassemble
  the blocks instead. The project had to be rebuilt once because the archive file names contained literal backslashes.
* Live debugging: `gdb` attach works when `kernel.yama.ptrace_scope=0` (remember to restore it to 1); a hardware watchpoint on a
  field found the launch function. The cheaper tool, used from then on: a **log-only hook in our own DLL** that writes what it sees to
  `Modloader/multimissile.log`, driven by a test the player performs.
* Modloader (`bass.dll` proxy): needs the original library renamed to `bass.dll_`; mods in `Modloader/mods/*.dll` export `version(const char*)`
  and `init()`. **`init` is called even when `version` returned false**, so a mod must guard itself. Mods are loaded early, so the
  game code may still be encrypted: our mods wait (up to 3 minutes) until the expected bytes are visible before patching.
* Build: MinGW-w64 cross compiler, static (`-static -static-libgcc -static-libstdc++`), C++17, one `Makefile` per repo
  (`make`, `make dist`). Editor support: a `.clangd` pointing at the MinGW headers.
* Pitfalls hit: scanning memory must accept `PAGE_WRITECOPY`; the "game window focused" check fails under Proton, so hotkey mods
  must not depend on it; `pkill -f` patterns can match the shell running them.
* Safe-edit rule: the game **rewrites `Libraries/OL.seria` and `Libraries/parts.seria` at startup**; edit them only with the game closed.
  A game update overwrites everything in `Libraries/` and `Data/Dialogs/`.

## 2. Hooking technique (all our DLLs)

Function-entry detour: a 14-byte `FF 25 00000000 <abs64>` jump over `len` stolen bytes (14..20, ending on an instruction boundary,
position independent), trampoline in a `VirtualAlloc` RWX page that runs the stolen bytes and jumps back. The stolen bytes are
compared with the expected ones before patching (version guard: on any other build the mod does nothing and says why in its log).
Call-site patches (speed mod) redirect a single `call` and use a code cave of `0xCC` padding.
Hooks of `hf_multimissile`: combat launch `0x14002e590` / `0x14002e3a0`, map launch `0x1400eced0`, level loader `0x14025afd0`.

### Hook ownership (so mods never patch the same place)
Mods are loaded in an unspecified order by the modloader, so two mods must never patch the same bytes. Current owners:

| Site | Kind | Owner |
|---|---|---|
| `0x14002e590`, `0x14002e3a0` (combat launch) and `0x1400eced0` (map launch) | function-entry detours | highfleet-multicharge |
| `0x14025afd0` (level loader) | function-entry detour | highfleet-salvo |
| `0x1400ed59e` (the 300.0 launch-cooldown immediate, 4 bytes) | in-place data patch | highfleet-salvo |
| `0x14011521f`, `0x140115240`, `0x14011529c` (disp32 of three `MULSS`) | operand patches | highfleet-refuel |
| `0x1400ea980` (add-fuel routine) | optional logging detour (`log_calls=1`) | highfleet-refuel |
| `0x140080699` (a `call powf`) and the cave `0x140073330` | call-site patch | highfleet-speed |
| editor held-part pointer `0x1403c0d88` (read) and `m_floor` writes | polling | highfleet-elevation |
| `0x140032f22` (gun blocking) and others | detours | highfleet-qol (logdot) |

Adding a hook anywhere in the first 14 bytes of an owned function would break its owner's version guard: patch a constant instead, or coordinate.

## 3. Engine and data formats

* HGE-based engine, statically linked. Data are `.seria` text files (defaults omitted): `m_classname=Body`, `m_code=15`, `{` ... `}`.
  A numeric `m_code` is the class code (0xf Body, 0x147 Escadra, ...). The serializer is `FUN_14004f010`, the Body field loader `FUN_140025240`.
* **Parts live in two libraries**: `Libraries/OL.seria` (ObjectsLibrary, `m_stats=2051` records: price, category, missile stats, ...) and
  `Libraries/parts.seria` (Body prototypes, `m_children=15`). A part is looked up by its id string `m_oid`; the string is mapped to an index by
  `FUN_140281cc0` and `GetStats(index)` (`FUN_140281e00`) returns the stats record. A body prototype references itself by `m_id` (also in its slots'
  `m_master.id`), so cloning a prototype means replacing every occurrence of its id.
* **Shipworks palette**: ShipworksExtended (`DefinePartEx` `0x14021b190`, `CreateLibraryEx` `0x14027f200`, `MakeGlobalEx` `0x140194de0`,
  `New` `0x140334094`, editor libraries at `0x1403bd400..` stride 0x18, `EditorParts` global `0x143a139f0`) reads
  `Modloader/config/Shipworks.json` (lists `Hulls`, `Armors`, `Fuels`, `Ammos`, `Legs`, `Engines`, `Guns`, `Sensors`, `Expendables`,
  `Crafts`, `Defences`, `Generators`, `Quarters`, `Emergency` plus `LoadVanilla...` flags). The file appears after the first run with the mod.
* **Language packs** `Data/Dialogs/english.seria_enc` (cp1252) and `russian.seria_enc` (cp1251): XOR stream cipher (MSVC `rand` LCG, seed 2531011,
  step 214013, `byte ^= (b>>15) ^ b`; same as stopnoanime/highfleet-dialog). Decoded: `#KEY<TAB>text`, entries split at `#`, newlines ignored.
  A part uses `#ID` (name), `#ID_SDESC` (type label), `#ID_DESC` (description) and, for some parts, `#ID_KEY` (launch hint).
  The player here uses the **Russian** version, so Russian text is the one that matters. Tool: `hf_multimissile/tools/hfcrypt.py`.
* **Saves**: `Saves/Profile_N/profile.seria` (a few MB of text). Parts of every ship are stored as full Body records (`m_oid=...`), so any per-part
  field survives landing, saving and restarting. Ship names: `m_ship_name=...`.
* **Shops** come from logdot's highfleet-qol (`Modloader/config/qol.json`): `enable_shop_parts` and `shop_parts.<ID> = [{probability, min_parts,
  max_parts, city_types}]`. Rolled **only when a city's shop is first generated**. City types: 1 UR, 2 repair, 3 merchant, 4 fuel, 5 intel,
  6 mercenary, 7 fleet HQ.
* Level files `Data/Levels/*.seria` (Map, Missile, Bombers, CraftsVsMissile, CraftsVsCrafts, Combat, ...) are **empty shells** with `LVL_SCRIPT=SCR_*`;
  the logic is in code.

## 4. Body (ship part) layout, class code 0xf (size 0xa40, ctor `FUN_140015690`, vtable `0x140352a30`)

| Offset | Field | Status |
|---|---|---|
| +0x28 | class code (`m_code`) | [game] |
| +0x48 | int state, 0 = dead/dropped | [code] |
| +0x78 | `m_id` (int64) | [game] |
| +0x88 | master (the hull/frame it is mounted on) | [game] |
| +0xb0 / +0xb8 | owner smart-ref / owner pointer (launch reads +0xb8) | [game] |
| +0x128 / +0x12c | position x, y (local to the master) | [game] |
| +0x130 / +0x138 | velocity / angle | [game] |
| +0x188 | stats index | [game] |
| +0x190 / +0x1a0 / +0x1a8 | `m_oid` std::string: data or SSO, length, capacity | [game] |
| +0x1b0 `m_b2bstate`, +0x1d0 `m_density`, +0x1f0 `m_layer`, +0x2c8/+0x2cc `m_health`/max | | [code] |
| +0x350 / +0x358 | slot vector begin/end | [game] |
| +0x3c0 / +0x3c8 | launch timer / `m_logic_active` (the launch sets it) | [game] |
| +0x3d0.. / +0x3e4.. | `m_logic_f1..f4` / `m_logic_i1..i4`; `m_logic_i4` (+0x3f0) was the first prototype's charge counter (i1 is used heavily by `FUN_140033b90`) | [game] |
| +0x490 / +0x4a8 | target ref / owner ref written by the launch | [code] |
| +0x508 / +0x510 | `m_sectors` vector<float>, 360 entries after a scan | [game] |
| +0x7a8 / +0x7ad | `m_count` / blueprint flag (clones set 1 / 0) | [game] |
| +0x848 | `m_mdl_covered` (float; 1.0 when the engine cone is blocked); in the launch function it is also a cooldown check | [code] |
| +0x858 | `m_weapon_ammo_amount` | [code] |
| +0x8d8 `m_stage` (NOT elevation), +0x90c `m_z` | | [code] |
| +0x9b0 / +0x9b8 | `m_floor_type` bitmask / `m_floor` (**the elevation**) | [game] |
| +0xa28 | `m_ed_rotate` | [code] |

Vtable slots (byte offsets): +0x48 kill (`FUN_140049ea0` -> `FUN_1402805d0` -> vtbl+0x40(this,1)), +0x50 add child, +0x68 remove from master,
+0x80 / +0x88 editor "place" steps, +0xe0 / +0xe8 master angle / position transform, +0x178 side (float, sign = friend/foe on the map), +0x210 damage.

**Stats record** (from `GetStats(Body+0x188)`; confirmed for the missile fields by cloning parts) [code]: +0x88 `m_price`, +0x8c `m_important`,
+0x90 `m_timecost`, +0x94 `m_repair_cost`, +0xb0 `m_category`, +0xb4 `m_sort_index`, +0xc4 `m_mdl_armor`, +0xd0 fuel_need, +0xd8 crew_need,
+0xe0 power_need, +0xf8 thrust, +0xfc thrust_map, +0x10c radar, +0x110 tracking, +0x114 guiding, +0x118 elint, +0x11c irst, +0x120 jammer,
+0x128 `m_mdl_sectors_type` (non-zero = the part takes part in arc scanning), +0x12c sectors_shift, +0x130 sectors_threshold, +0x140 weapon_priority,
+0x144 caliber, +0x148 load_amount, +0x14c load_time, +0x150 rate, +0x154 `m_acceleration_time`, +0x158 `m_launched_speed`, +0x15c speed2,
+0x160 range, +0x164 `m_missile_type`, +0x168 `m_missile_explosive` (> 100000 means nuclear), +0x16c cluster, +0x170 `m_missile_ap`, +0x174 agility,
+0x178 radar_range, +0x17c radar_cone, +0x180 fuze_type, +0x184 launched_health.

Smart-ref (0x18 bytes: vtable, pointer, ?): ctor `FUN_140194bd0(ref, node)`, copy `FUN_140194b80(dst, src)`, dtor `FUN_140194d20(ref)`, assign
`FUN_140194de0(ref, node)`; the reallocating vector insert for lists of them is `FUN_140004b00(vec, pos, ref)`; `FUN_1402c7c90` is
`vector<Node*>::insert(range of smart-refs)`.

## 5. Elevation and firing arcs  (mod: `hf_elevation`)

* Elevation solver `FUN_140256a90` (`Ship_SolveFloors`) sets `m_floor` from `m_floor_type` and the neighbours. Bits of `m_floor_type`: `0x01` auto-recompute,
  `0x02` neighbours must be strictly higher, `0x04`/`0x08` neighbour-count variants, `0x10` force floor 3. Parts without `0x01`/`0x10` keep the saved
  `m_floor` [game, manual test ship]. An automatic part rises by one when every connection-slot neighbour is at or above its floor, repeating until stable;
  the rise also bumps attached non-socket children. Saved ships contain floors 1-3.
* Arc scan `Body::ScanSectors` `0x140052340`: 360 one-degree rays through `World_RaycastBodies` `0x140239f30`; a hit writes 0 to the degree's `m_sectors` entry,
  a clear ray writes a weight from the stats record; `Body::UpdateEngineCovered` `0x14001c4a0` averages the engine cone into `m_mdl_covered`.
  **A body blocks a ray only if `param_7 != 0` (flag bit 5 of the stats flags at +0xb0, inverted) or `shooterFloor <= otherFloor`** (+1 if the body's master type is 7):
  elevation decides who can block whom.
* Firing arcs: logdot's highfleet-qol already restores gun arc blocking in 1.163: it detours `FireGun` (inject at `0x140032f22`, exit `0x140032ef0`, return
  `0x140032f29`), calls `is_gun_blocked(gun)` which reads the gun's 360-float `m_sectors`, requires the stats value at +0x128 to be non-zero, maps the gun angle
  relative to the root body to a one-degree sector and blocks on 0.0. Our elevation mod therefore changes what blocks a gun.
* Elevation mod: held part pointer in the editor is the global `0x1403c0d88` (null when nothing is held), editor-active flag `0x1403ef368`. Hotkeys **U** raise, **P**
  lower, **\\** hand back to automatic (then drop the part so the game recomputes). Mounted children follow the parent's floor (`sync_children`, `child_offset`),
  otherwise a gun is buried under a raised block. Other editor functions: wheel `FUN_1400bc5e0`, rotate `FUN_1400bdad0`, placing sequence `FUN_1400bbbf0`.

## 6. Map cruise speed  (mod: `hf_speed`)

The ship stats routine `FUN_14007fcf0` calls `powf(TWR - 1, 0.5)` at `0x140080699`: speed = `50 * sqrt(TWR - 1)` m/s in 1.163; version 1.151 used the straight line
`25 * TWR`. The mod redirects that one `call` to `SpeedCurve()` (`coefficient * max(TWR - subtract, 0) ^ exponent`, optional km/h cap), through a stub in padding
at `0x140073330` (16 x `0xCC`); the 24 bytes around the call and the stub site are verified first. The game caches each ship's speed, so reopen the ship to see a change.

## 7. Multi-charge parts and salvos  (mod: `hf_multimissile`)

### 7.1 Design (what is built)
* **Charge level = part id** [game]. `MDL_AA_X3 -> MDL_AA_X2 -> MDL_AA_X1` (S-4 Triumph, combat) and `MDL_A101_4 .. MDL_A101_1` (A-101, map). A launch with charges
  left fires a **clone** of the part and rewrites the real part's id in place; the last level launches the real part, which the game then consumes. The id is saved
  with the part, so charges survive landing, saves and restarts; the game's own screens show the level (each id has its own name and price); no hidden counter.
  The first prototype stored a count in `m_logic_i4`; `legacy_counter=1` migrates such parts once.
* **Id swap** [game]: write the new string into the existing buffer (it must fit the **capacity**; every level id must be no longer than the first), set the length,
  `idx = FUN_140281cc0(&oid)`, store it at +0x188; roll back if idx < 0. (30 of 179 vanilla ids are longer than 15 chars, so the limit is the capacity, not 15.)
* **Clone** [game], the editor's own sequence: `FUN_1401bfd00` copy, `vtbl+0x80`, `FUN_140280840(c,1)` assign ids, clear the slot vector, world position and angle through the
  master (`vtbl+0xe8/+0xe0`), `FUN_1400521f0` / `FUN_140051850`, `FUN_140027f90`, `vtbl+0x88`, `m_count=1`, blueprint=0, copy velocity, owner ref via `FUN_140194de0`, and **add it to
  the level node `*(0x147fc6f88)` before launching** (the per-frame update only runs for objects in the world tree). Failed clone launch: kill it with `vtbl+0x48`.
* Success of the combat launch is the **low byte** of the return value only.
* The AI of our own ships calls the launch function **every frame** until it succeeds (hundreds of failed calls per fight): failed attempts must be silent and cheap (a failed
  part is left alone for 250 ms).
* **Data tool** `tools/apply_data.py` + `multicharge.ini`: creates the stats record, the body prototype, the four language entries and the palette entry for every level, from
  a source part (`copy_from`) or an existing first id. From pristine game files it reproduces the hand-built Triumph and A-101 exactly [game-verified by diffing].

### 7.2 Combat launch [game]
`FUN_14002e590(part)` (player) / `FUN_14002e3a0(part, target)` (AI) need a target (`FUN_14006c0e0`/`FUN_14006c440`), the owner (+0xb8), the owner's cooldown (+0xad4) and
in-flight limit (owner+0x17b0); they store target/owner refs at part+0x490/+0x4a8, set +0x3c8, start a timer, and register the part in the owner's active-missile list. The part
then detaches in the logic update `FUN_140033b90` (~`0x140037806`): `vtbl+0x68` removes it from its master, `level->vtbl+0x50` adds it to the world. Player key input is
`FUN_14018a530`: code 0x1013 walks the ship's AA list (ship+0x13f0, stride 0x18, entry+8 = part) and calls the launch until one succeeds (one missile per key press);
0x1012 uses the list at ship+0x13d8 with `FUN_14002ff60`. The lists are rebuilt by the stats routine `FUN_14007fcf0` -> `FUN_140071380`.

### 7.3 Map launch of strategic missiles [game]
* Panel `FUN_140273640`: **4 switches** (`MAPMODE_MISSILE_SW`), each bound to a distinct, not-yet-queued missile part of the selected type (`MAPMODE_MISSILE_TYPE(_SELECT)`);
  `MAPMODE_MISSILE_FIRE` is the button. A strategic missile such as the A-100 (`MDL_NUKE_03_CONV`) is a single body with two mount slots.
* Queue filler `FUN_140214c40`: one **0x38-byte entry** per switched-on missile in the fleet's vector (**fleet +0x538 begin / +0x540 end / +0x548 cap**): `{SmartRef part (ptr at +8),
  SmartRef target (ptr at +0x20), float x, y at +0x30}`; a missile with stats +0x168 > 100000 triggers `NUCLEAR_ESCALATION_1`.
* Consumer `FUN_1400eced0(fleet)`, called from the fleet update `FUN_140111ff0` whenever **fleet +0x50c == 0**: takes the LAST entry, creates the map missile object (below), copies the
  part's oid into it, kills the part (`vtbl+0x48`), pops the entry, recomputes ship totals, and sets **`fleet+0x50c = 300.0`** (`mov [rdi+0x50c], 0x43960000` at `0x1400ed598`).
  The timer is counted down per frame (~`0x140115cc8`) and also blocks the AI decision `FUN_1400f00c0`: this is why a queued volley goes out one by one.
* Our hooks: `charges` points the entry's part ref at a clone (`FUN_140194de0(entry, clone)`) after swapping the real part to the next id; `salvo.map_launch_delay` rewrites the
  cooldown right after the original returns (a volley of three left together at 3).
* AI side: `FUN_1400f00c0(fleet, targetInfo)` decides to fire (cooldown, range 100..9000, per-target salvo caps 1/2/8 in targetInfo+0x84) and fills the queue via `FUN_1400fc760`.

### 7.4 Map missile object ("Missile", class code `0x400000001047`, size 0x308, ctor `FUN_1400e48a0`, vtable `0x14035e998`)

| Offset | Field |
|---|---|
| +0x150 / +0x154 | position x, y |
| +0x158 / +0x15c | speed / heading |
| +0x240 | reverse flag |
| **+0x248** | **missile count** (the launch writes 1) |
| +0x270 | the fleet it targets |
| +0x29c | type (3 = ground when range <= 60) |
| **+0x2b8 / +0x2c8 / +0x2d0** | **the missile's part id** (std::string: data, length, capacity) |

World singleton `FUN_140292a90()`: map missiles vector **+0x228/+0x230**, fleets **+0x270/+0x278**, a second fleet list +0x1f8/+0x200 (friendlies that join a defence).
`FUN_1400ec440(a, b, dt)` = "do these two map objects come within 1.0 of each other during the next dt step" (closest approach along their headings); used for every encounter.

### 7.5 Engagements (map -> battle) [game unless marked]
* Loader `FUN_14025afd0(const char* level, bool, bool)`: stores the name (`DAT_1403c1390`), sets **`DAT_143a11902 = 1` (engagement pending: blocks a second one in the same pass)**,
  then `FUN_1402db350` etc.
* Engagement lists = four global `std::vector`s of smart-refs: **A `0x143a158e0` (our side), B `0x143a159c0` (the other side)**, C `0x143a158b0`, D `0x143a13de8`.
* Logged in play: `Missile.seria` (a missile threatens our fleet): A = [Escadra], B = [Missile]. `Bombers.seria` (a plane group attacks): A = [**MapCraft**, class code
  `0x800000001047`, ONE object carrying the planes], B = [Escadra]. `CraftsVsMissile.seria` / `CraftsVsCrafts.seria` (planes defending/engaging, loaded by `FUN_140117840`) never seen yet.
* Trigger for `Missile.seria` (inside `FUN_140111ff0`): first missile with `FUN_1400ec440` true and opposite side wins; clears A/B/C/D, pushes that ONE missile into B, adds nearby friendly fleets into A,
  calls the loader. A volley of three therefore produced three fights in a row.
* Scenario `SCR_MISSILE` (a state machine inside the giant `FUN_1402ac970`; branch at `0x1402c4baf`, state byte-table `0x1402c7a00`, offset table `0x1402c79e4`): state 1 (`0x1402c4dfc`) calls
  **`FUN_1402d45c0`**: sorts the defender fleet's ships, spawns up to 4 (`FUN_1402672c0`), then reads **only B[0]**: `for i < B[0]+0x248` it creates a missile with
  `EditorParts_DefinePart(0x143a139f0, string at B[0]+0x2b8, level, 1)` at a random offset, and finally zeroes the count.
* **Salvo grouping** (`group_missiles`): pushing extra missiles into list B is **ignored** [game]; **summing the counts into the first object works** [game]: three missiles became one fight
  against three, the emptied extras are removed with `vtbl+0x48` on the next `Map.seria` load; missiles of the other side, other part ids or other targets are not merged,
  and map-level interception is unaffected (one interceptor still kills one missile) because the merge happens only when the fight is built.
* Plane downing on the map: `FUN_140111110` (called from `FUN_1400f11b0`) prints `MISSILE_INTECEPTED` and downs **at most 3 crafts per pass**, ~2/3 chance each (`CRAFT_DOWN`, `vtbl+0x210`) [code].

### 7.6 Module layout of `hf_multimissile`
`src/game.h` every game address/offset (the only place with raw numbers); `src/util.*` log, memory, ini reader, detours; `src/charges.*` multi-charge parts (combat + map hook logic);
`src/salvo.*` map launch delay and salvo grouping; `src/engagement_log.*` research logger; `src/main.cpp` exports and hook installation (routes only).
Config: `Modloader/config/multicharge.ini` (parts, read by the DLL and `tools/apply_data.py`) and `salvo.ini`. Log: `Modloader/multimissile.log`.

## 7b. Refueling  (repo: `hf_refuel`)

A community member who reads the code said the refuel rate is **hard-coded**, not data. Confirmed [game]: a logger on the add-fuel routine during a real refuel showed everything.
* **The rule** (inside the fleet update `FUN_140111ff0`, docked fleet `RSI`, station `R15`, frame time `XMM15`) [game]:
  `amount = min(fleet.capacity(+0x4a0) - fleet.fuel(+0x498), dt * RATE, station.stock(+0x274))`, then `added = FUN_1400ea980(fleet, amount)` and
  `station.stock -= added`. `RATE` is **200.0** at a station of type 4 (`station+0x258 != 0 && station+0x25c == 4`, the fuel city), **100.0** at any other, read by
  `MULSS xmm0,[rip+..]` at **`0x14011521f`** (200) and **`0x140115240`** (100). AI fleets use the same constant **100.0** at **`0x14011529c`** (no station stock accounting).
  The constants live at `0x14035282c` and `0x1403524e0` and are shared by hundreds of unrelated places (they are pooled `200.0f`/`100.0f`), so the mod repoints only the three instructions
  (disp32 at +4) at private floats placed just above the image (rip-relative reach).
* In the log the player's fleet received 1142.857 per call = 100 * 11.4286 (`dt`, so the map's time unit is ~80/7 per frame step), in bursts of 7 calls per ~19.5 ms; 132 fleets were refueled the same way.
* `FUN_1400ea980(Escadra*, double amount)` = **add fuel to a fleet**: distributes `amount` over the ships in proportion to free tank space (ship `+0x1638` current, `+0x1640` capacity, doubles; per-ship fill
  `FUN_140060d80(ship, amount)`), adds the total to `fleet+0x498` (snapping to an integer within 0.1) and returns it. Other callers: `+0xf9791` (fuel from absorbed ships, `FUN_1400f9460`; amounts 240000..480000),
  `+0x2b1b0a` (scenario setup, 5,000,000 once), the shipworks exit `FUN_1400d2260`, `FUN_1400a6230`, `FUN_1402017a0`, `FUN_140261a20`, `FUN_140290210`.
* Fleet fields: `+0x420 m_refuel_timer` / `+0x424 m_refuel_amount` are a **delayed delivery** (the fleet update counts the timer down and then delivers the amount); they stayed 0 during station refueling,
  so the station path is the per-frame rule above. `+0x468` is the refuel animation flag (`FUN_1400fe8b0`: `refueling_start/loop/stop`); save/load of the fields is `FUN_1400feb90`.
* Settings of the mod: `player_rate_multiplier`, `ai_rate_multiplier` (a huge value means "fill at once"; it cannot over-deliver because of the two caps). Open: the buy-fuel slider UI (`FUEL_BUY_SLIDER`)
  and `REFUEL_TIME` were not traced because the per-frame rule explained the observed refueling.

## 8. Gameplay facts learned
* The Triumph (AA, needs a fire control radar like the R-9 Sprint `MDL_MISSILE_03`) is **combat only**; the A-100 is a **map-only** strategic missile.
* On the map, missiles can be shot at planes and other missiles; this is computed on the map without a battle level.
* Planes: a group is one `MapCraft` object; in `Bombers.seria` they spawn from it.

## 9. Open questions
* Map-level AA against flocks/salvos (a merged object is only created inside the fight, but check the three-crafts-per-pass rule against bigger groups).
* Launching a volley as ONE map object with count N (it would also fly as a group); the `MapCraft` scenario `SCR_BOMBERS` has not been read.
* Whether an AI fleet defending against our salvo uses the same `Missile.seria` setup (the merge would apply to it too).
* **Multi-charge strategic missiles together with salvos** is deliberately not designed or tested: one A-101 part is one launcher switch (one queued launch at a time), so a single part cannot fire several charges in one volley; a volley of several A-101 parts works as separate launches, and the defence merge treats them like any other missiles. Decide the intended use before testing or documenting it.
* `CraftsVsMissile` / `CraftsVsCrafts` flows; shop behaviour of the Triumph in a fresh campaign (QoL rolls shops once per city).
* Gun-side use of `m_sectors` is solved by highfleet-qol; the arc scan being "gated off by data" (stats +0x128 == 0) versus a patched call is not settled.
* For a public release: inject names/descriptions at runtime instead of editing the language packs; README/guide for adding new multi-charge parts; LICENSE name; scrub paths.
