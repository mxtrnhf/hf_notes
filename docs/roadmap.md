# Mod development roadmap (long term)

**Status: wish list. Not scheduled and not started. Do not act on any item without being asked.**
Item names (Zenith, A220, Pytor, Khiva) are the game's own. Category tags: Bug, QoL, Feature, AI, Mod Scope, Physics Engine.

## Version scope
**Focus is 1.163.** Some players still use 1.151 because of gameplay differences from later versions. The ones that matter for us are the **speed curve** (already fixed) and the **damage changes**. The damage changes may need both game versions played side by side, with Claude attached to the running game, to see what happens inside.

## Items

### Bugs and QoL
* **[Bug]** A proximity-fused missile colliding with flares crashes the game.
* **[QoL]** Remove the mechanic by which rockets (A220) lower mouse sensitivity globally for all weapon systems.
* **[QoL / Bug]** Changing an A220 rocket's weapon priority (to change hotkey grouping) removes the extended aiming reticle for rocket weapons.
* **[QoL / Inconsistent behavior]** Salvage minigame: when a safety hazard occurs while the wreck site is out of focus, the game enters auto-mode instead of pausing.
* **[QoL]** Option to disable Pytor's map-pointing interactions.
* **[QoL]** Audio cue (or auto-pause) when aircraft intercept enemy forces on the strategic map.
* **[QoL]** Toggle for auto-pause on the strategic map.
* **[Bug]** Capturing all cities around Khiva before the end-game event causes a crash loop / infinite loading.

### New features
* **[Feature]** Cruise-missile barrage mechanic (for example salvos of 4 simultaneous incoming cruise missiles).
* **[Feature, missing]** A functional crew-requirement system.
* **[Feature]** Tracking of ballistic missiles in the terminal phase (near the target) on the strategic map.
* **[Feature]** Editing of new enemy ship spawning events.

### AI
* **[Strategic]** The AI launches all its aircraft when it detects the player within strike range, so none are left for defensive interception.
* **[Strategic]** The AI has no evasive manoeuvring against cruise missiles on the strategic map.
* **[Tactical, exploitable]** Closing to very short range of an enemy ship in tactical combat disables all of its weapon systems.
* **[Tactical, exploitable]** The AI consistently gives way to the player's ship, which gives the player easy positional advantage.
* **[Tactical]** The AI cannot use some ordnance or parts (LG/INC shells); AP rounds are fired only at extremely short range; the AI cannot deploy flares.
* **[Tactical, exploitable]** High convergence angles can be used to disable enemy turrets.

### Mod scope
* **[Mod Scope / Bug]** Support for combined sensors. Sensor range calculation is currently bugged (accumulative) with two or more sensor types.
* **[Mod Scope]** HP modification for missiles (Zenith), aircraft, rockets (A220) and cannon shells.
* **[Mod Scope]** Wider ship-roster modification (additional ship variants, adjustable composition ratio).
* **[Mod Scope]** Editing the repair-part composition menu (hull, armor, landing gear, etc.).
* **[Mod Scope]** Adjustable time-to-live (TTL) for cluster munitions and mine bomblets.
* **[Mod Scope]** Damage model: calibers above 30 mm should not destroy missiles (Zenith), aircraft, rockets (A220) or cannon shells in a single shot.
* **[Mod Scope]** Acceleration and top-velocity modification for rockets (A220).

### Physics engine
* **[Physics]** Limited acceleration restricts the turn rate of missiles (Zenith) and aircraft; capped top speeds restrict projectile velocity.

## Tooling for modders (debug, edit, test)
Same status as above: wish list, nothing started. What exists today: `hfcrypt.py` (language packs), `apply_data.py` in the multicharge/multimissile repos (writes
part data into `OL.seria`/`parts.seria`), per-mod log files, the modloader 4.1.0 logging SDK (`setup.md`), and Ghidra with an MCP bridge. Everything else is hand-edited text.
Ordered by how much time each would save, not by effort. Tags: **[pain]** a problem we have actually hit, **[guess]** an expected benefit.

### 1. `.seria` library and CLI (parse, query, patch, diff)
* **Why [pain]:** `.seria` is picky (nested `header=number { }`, braces alone on a line, never indented, defaults omitted, repeated `attr=value` lines are arrays), so by-hand edits
  of 2051 `m_stats` records break silently. The game also **rewrites `OL.seria` and `parts.seria` at startup**, and a game update overwrites `Libraries/`.
* A parser/serializer that round-trips a file byte-for-byte when nothing is changed (so a diff shows only the intended edit). Then:
  * `get`/`set` by id and field, for example `OL.seria[MDL_NUKE_03_CONV].m_launched_range`, with bulk edits from a CSV or JSON.
  * **Patch files instead of edited game files:** a small declarative list of changes (id, field, new value, expected old value) applied on top of vanilla. It survives game updates
    (re-apply), shows the old value when vanilla changed under it, and is what we would share with other modders instead of whole libraries. `apply_data.py` is the seed.
  * Decode and validate: `m_category` shown as bit names (table in `structures.md`), class codes as names, warnings for a cloned part whose `m_id` is not replaced everywhere
    it occurs (`formats.md`), unknown fields, wrong types.
  * `diff` between two game versions' libraries, for example 1.151 vs 1.163 (that is also the evidence for "which differences do players still prefer").

### 2. Save editor and save snapshots
* **Why [pain]:** saves are plain text but huge (every part of every ship is a full Body record). Cash, unlocks, fuel and ship swaps are one-line edits that are tedious to find.
* Named snapshots (backup before editing is already the rule, make it one command) and a **save diff**: take two snapshots around an action (fire a volley, enter a city,
  refuel) and list exactly which fields changed. **[guess]** this is the cheapest way to learn what a game action writes, and it can confirm offsets in `structures.md`.
* Common edits as commands: cash (`m_scores`), `m_countdown`, unlocks, a city's fuel stock, escadra composition, NPC loyalty. Sanity checks before writing (`m_id` uniqueness, escadra
  references still resolve). Optionally a read-only "what is in this save" summary (fleets, cities, characters).

### 3. In-game debug mod (our own DLL)
* **Debug overlay or console on hotkeys** [guess]: pause and single-step the frame, time scale, teleport the fleet, set fuel/cash, spawn a part or a fleet, toggle invulnerability,
  kill a target, set `fleet+0x50c` directly. Each one removes a replay of the campaign from a test.
* **Live struct watch:** pick an object (selected part, selected fleet) and show its known fields by name using the layouts in `structures.md`, updating each frame. A field list that
  disagrees with the game is then visible immediately instead of in a later log.
* **Direct-to-scenario launcher:** call the level loader (`FUN_14025afd0`, owned by highfleet-salvo, so coordinate) to start `Missile.seria`, `Bombers.seria` and similar with chosen
  sides, skipping the map. Needed for testing salvo and AI work (`systems.md`), and for reproducing the crash bugs in the roadmap on demand.
* **Crash capture** [guess]: a vectored exception handler that logs faulting address, module, registers and a short stack, and writes a minidump. The flare-collision crash and the
  Khiva loading loop are both currently "it crashes" with no address. This should turn each into an RVA we can open in Ghidra.

### 4. Logging and tracing
* **Declarative log hooks:** a JSON file `{address, expected bytes, what to log}` that installs a log-only detour with the existing version guard (expected bytes compared before
  patching, see `hooks.md`), so a new probe needs no C++ rebuild. The "cheapest live probe" in `setup.md` is then a config edit.
* **Structured logs:** one line per event with frame number and game time, JSON lines, to the modloader's logging SDK (replaces our per-mod files). A small viewer that filters by
  mod/function and merges several mods in time order.
* **Marker hotkey:** the player presses a key and a marker line is written ("now I fired", "now the crash is about to happen"), so a log and a play session can be matched without
  guessing. Pairs with the save snapshots above.
* Rate limiting: the AI calls the launch every frame (hundreds of failures per fight, `systems.md`), so any hook needs count-and-summarise or "log only changes".

### 5. Verification and regression
* **Site verifier [pain]:** read the patch-site table in `hooks.md` and check that every address still holds the expected bytes in a given exe or dump, plus the constants
  patched (300.0f launch cooldown, the 100/200 refuel rates, the 50.0f speed factor) and the class sizes in `structures.md`. We did this by hand for 1.163; scripted, it
  runs after every game update and in CI. It also answers "is this dump the same build" without opening Ghidra.
* **Install smoke test:** from a clean game folder, check modloader present, mods load, version guards pass, `hge.log` has no new errors, pass/fail log lines from `install.md`.
* **Notes vs binary check:** the same idea for `structures.md` offsets: a script that decompiles/greps a function and confirms a stated offset, so notes cannot drift unnoticed
  (the MapCraft size was wrong for a while).
* Game-file fingerprint (hash of `Libraries/`, `Data/`, exe) stored with each report, so a bug report says which build it came from.

### 6. Ghidra side (for the sync work between versions)
* Export names, signatures and structs of a program to text in this repo (and import them back), so annotations live in git and can be reviewed. Complements Version Tracking
  for carrying 1.151 work to 1.163 and gives the second person a diffable view of changes.
* A checked-in list of named functions with address, and a script to flag the ones whose bytes differ between builds.

### What to build first
1. The `.seria` round-trip parser with patch files (1) and the site verifier (5): both are small, scriptable and pay off at every game update.
2. Save snapshots with diff (2): turns "play and notice" into data for the notes.
3. Crash capture and the direct-to-scenario launcher (3): unblocks the crash bugs and combat testing in the roadmap.
4. The rest as the work needs it.
