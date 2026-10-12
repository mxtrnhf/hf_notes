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
